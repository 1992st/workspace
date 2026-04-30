#!/usr/bin/env node
import fs from 'node:fs';

const [htmlPath, pngPath, widthArg='1242'] = process.argv.slice(2);
if (!htmlPath || !pngPath) {
  console.error('Usage: render_html_to_png.mjs <htmlPath> <pngPath> [width]');
  process.exit(2);
}

const width = Number(widthArg) || 1242;
if (!fs.existsSync(htmlPath)) {
  console.error(`Input HTML not found: ${htmlPath}`);
  process.exit(1);
}

const htmlContent = fs.readFileSync(htmlPath, 'utf8');
const wrapper = `<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  html, body { margin: 0; padding: 0; background: #ffffff; }
  #canvas {
    width: ${width}px;
    margin: 0 auto;
    box-sizing: border-box;
    display: block;
  }
</style>
</head>
<body>
  <div id="canvas">${htmlContent}</div>
</body>
</html>`;

async function run() {
  let playwright;
  try {
    playwright = await import('playwright');
  } catch {
    console.error('Missing dependency: playwright');
    process.exit(3);
  }

  const browser = await playwright.chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width, height: 2000 } });
  await page.setContent(wrapper, { waitUntil: 'networkidle' });
  await page.waitForTimeout(100);
  const el = await page.$('#canvas');
  if (!el) {
    throw new Error('render target #canvas not found');
  }
  await el.screenshot({ path: pngPath });
  await browser.close();
}

run().catch((err) => {
  console.error(String(err?.stack || err));
  process.exit(1);
});
