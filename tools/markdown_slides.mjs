#!/usr/bin/env node

function hasNonEmptyContent(lines) {
  return lines.some((line) => line.trim().length > 0);
}

export function splitSlides(markdown) {
  const normalized = String(markdown ?? "").replace(/\r\n/g, "\n");
  const byDelimiter = normalized
    .split(/^\s*---\s*$/m)
    .map((part) => part.trim())
    .filter(Boolean);

  if (byDelimiter.length > 1) {
    return byDelimiter;
  }

  const lines = normalized.split("\n");
  const slides = [];
  let current = [];

  for (const line of lines) {
    if (/^#{1,2}\s+/.test(line) && hasNonEmptyContent(current)) {
      slides.push(current.join("\n").trim());
      current = [];
    }
    current.push(line);
  }

  if (hasNonEmptyContent(current)) {
    slides.push(current.join("\n").trim());
  }

  return slides.length > 0 ? slides : [normalized.trim()];
}

function parseSlide(slideText, index) {
  const lines = slideText.split("\n");
  let title = "";
  const bullets = [];
  const paragraphs = [];
  const images = [];

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }

    const heading = line.match(/^#{1,6}\s+(.+)$/);
    if (heading) {
      if (!title) {
        title = heading[1].trim();
      } else {
        paragraphs.push(heading[1].trim());
      }
      continue;
    }

    const bullet = line.match(/^([-*+]|\d+[.)])\s+(.+)$/);
    if (bullet) {
      bullets.push(bullet[2].trim());
      continue;
    }

    const imageMatch = line.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imageMatch) {
      images.push({
        alt: imageMatch[1].trim(),
        path: imageMatch[2].trim(),
      });
      continue;
    }

    paragraphs.push(line);
  }

  if (!title) {
    if (paragraphs.length > 0) {
      title = paragraphs[0].slice(0, 48);
    } else if (bullets.length > 0) {
      title = bullets[0].slice(0, 48);
    } else {
      title = `Slide ${index + 1}`;
    }
  }

  return { title, bullets, paragraphs, images };
}

export function parseMarkdownToSlides(markdown) {
  const slides = splitSlides(markdown);
  return slides.map((slideText, index) => parseSlide(slideText, index));
}
