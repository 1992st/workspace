import test from "node:test";
import assert from "node:assert/strict";
import { parseMarkdownToSlides, splitSlides } from "./markdown_slides.mjs";

test("splitSlides uses explicit --- delimiters", () => {
  const md = "# S1\nA\n---\n# S2\nB";
  const slides = splitSlides(md);
  assert.equal(slides.length, 2);
  assert.match(slides[0], /S1/);
  assert.match(slides[1], /S2/);
});

test("splitSlides auto-paginates by H1/H2 when no delimiter", () => {
  const md = "# Intro\nA\n## Detail\nB\n# End\nC";
  const slides = splitSlides(md);
  assert.equal(slides.length, 3);
});

test("parseMarkdownToSlides extracts title, bullets, paragraphs, images", () => {
  const md = "# Title\n- one\n- two\npara\n![x](assets/a.png)";
  const slides = parseMarkdownToSlides(md);
  assert.equal(slides.length, 1);
  assert.equal(slides[0].title, "Title");
  assert.deepEqual(slides[0].bullets, ["one", "two"]);
  assert.deepEqual(slides[0].paragraphs, ["para"]);
  assert.equal(slides[0].images[0].path, "assets/a.png");
});
