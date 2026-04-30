#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { parseMarkdownToSlides } from "./markdown_slides.mjs";

const [inputMd, outputPptx, layoutArg = "16:9", themeArg = "business-light"] = process.argv.slice(2);

if (!inputMd || !outputPptx) {
  console.error("Usage: build_pptx_from_markdown.mjs <inputMd> <outputPptx> [layout] [theme]");
  process.exit(2);
}

if (!fs.existsSync(inputMd)) {
  console.error(`Input markdown not found: ${inputMd}`);
  process.exit(1);
}

let PptxGenJS;
try {
  const mod = await import("pptxgenjs");
  PptxGenJS = mod.default ?? mod;
} catch {
  console.error("Missing dependency: pptxgenjs");
  process.exit(3);
}

const mdDir = path.dirname(path.resolve(inputMd));
const markdown = fs.readFileSync(inputMd, "utf8");
const parsedSlides = parseMarkdownToSlides(markdown);

const pptx = new PptxGenJS();
pptx.layout = layoutArg === "4:3" ? "LAYOUT_STANDARD" : "LAYOUT_WIDE";
pptx.author = "lumi-writer";
pptx.company = "lumi-writer";
pptx.subject = "Generated from markdown";
pptx.theme = {};

const theme = themeArg === "business-light" ? themeArg : "business-light";
const palette = theme === "business-light"
  ? {
      title: "0F172A",
      text: "1E293B",
      muted: "64748B",
      bg: "FFFFFF",
    }
  : {
      title: "0F172A",
      text: "1E293B",
      muted: "64748B",
      bg: "FFFFFF",
    };

function toAbsoluteAsset(assetPath) {
  const raw = assetPath.replace(/^["']|["']$/g, "");
  if (path.isAbsolute(raw)) {
    return raw;
  }
  return path.resolve(mdDir, raw);
}

function addSlideBody(slide, item) {
  const textLines = [];
  for (const p of item.paragraphs) {
    textLines.push(p);
  }
  for (const b of item.bullets) {
    textLines.push(`• ${b}`);
  }
  const hasText = textLines.length > 0;
  const images = item.images
    .map((img) => ({ ...img, absPath: toAbsoluteAsset(img.path) }))
    .filter((img) => fs.existsSync(img.absPath));
  const hasImages = images.length > 0;

  if (!hasText && !hasImages) {
    slide.addText("（本页无可渲染内容）", {
      x: 0.8,
      y: 1.5,
      w: 11.5,
      h: 1.0,
      fontSize: 18,
      color: palette.muted,
      fontFace: "Calibri",
    });
    return;
  }

  if (hasText && hasImages) {
    slide.addText(textLines.join("\n"), {
      x: 0.6,
      y: 1.3,
      w: 5.8,
      h: 5.4,
      fontSize: 18,
      color: palette.text,
      fontFace: "Calibri",
      breakLine: true,
      valign: "top",
    });

    const maxImages = Math.min(images.length, 3);
    const totalHeight = 5.4;
    const gap = 0.15;
    const blockHeight = (totalHeight - gap * (maxImages - 1)) / maxImages;

    for (let i = 0; i < maxImages; i += 1) {
      slide.addImage({
        path: images[i].absPath,
        x: 6.7,
        y: 1.3 + i * (blockHeight + gap),
        w: 6.2,
        h: blockHeight,
      });
    }
    return;
  }

  if (hasText) {
    slide.addText(textLines.join("\n"), {
      x: 0.8,
      y: 1.4,
      w: 11.8,
      h: 5.5,
      fontSize: 20,
      color: palette.text,
      fontFace: "Calibri",
      breakLine: true,
      valign: "top",
    });
    return;
  }

  const maxImages = Math.min(images.length, 3);
  if (maxImages === 1) {
    slide.addImage({
      path: images[0].absPath,
      x: 0.8,
      y: 1.3,
      w: 11.8,
      h: 5.7,
    });
    return;
  }

  const totalHeight = 5.7;
  const gap = 0.15;
  const blockHeight = (totalHeight - gap * (maxImages - 1)) / maxImages;
  for (let i = 0; i < maxImages; i += 1) {
    slide.addImage({
      path: images[i].absPath,
      x: 0.8,
      y: 1.3 + i * (blockHeight + gap),
      w: 11.8,
      h: blockHeight,
    });
  }
}

for (let i = 0; i < parsedSlides.length; i += 1) {
  const item = parsedSlides[i];
  const slide = pptx.addSlide();
  slide.background = { color: palette.bg };
  slide.addText(item.title || `Slide ${i + 1}`, {
    x: 0.6,
    y: 0.3,
    w: 12.2,
    h: 0.7,
    fontSize: 30,
    bold: true,
    color: palette.title,
    fontFace: "Calibri",
    valign: "mid",
  });
  addSlideBody(slide, item);
  slide.addText(`${i + 1}/${parsedSlides.length}`, {
    x: 11.7,
    y: 6.9,
    w: 1.0,
    h: 0.2,
    fontSize: 10,
    color: palette.muted,
    align: "right",
    fontFace: "Calibri",
  });
}

await pptx.writeFile({ fileName: path.resolve(outputPptx) });
console.log(`[OK] pptx: ${path.resolve(outputPptx)}`);
