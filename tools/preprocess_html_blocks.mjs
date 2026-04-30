#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const [inputMd, tmpDir, outMd] = process.argv.slice(2);
if (!inputMd || !tmpDir || !outMd) {
  console.error('Usage: preprocess_html_blocks.mjs <inputMd> <tmpDir> <outMd>');
  process.exit(2);
}

const content = fs.readFileSync(inputMd, 'utf8');
const lines = content.split(/\r?\n/);
fs.mkdirSync(tmpDir, { recursive: true });

function countDivDelta(line) {
  const open = (line.match(/<div\b/gi) || []).length;
  const close = (line.match(/<\/div>/gi) || []).length;
  return open - close;
}

function writeBlock(id, htmlLines) {
  const p = path.join(tmpDir, `${id}.html`);
  fs.writeFileSync(p, htmlLines.join('\n') + '\n', 'utf8');
}

// Mode A: explicit HTML2PNG markers
const hasMarkers = lines.some((l) => /HTML2PNG:START/.test(l));
const out = [];
let idx = 0;

if (hasMarkers) {
  let inBlock = false;
  let currentId = '';
  let buf = [];
  for (const line of lines) {
    const start = line.match(/HTML2PNG:START(?:\s+id=([^\s]+))?/);
    if (start) {
      inBlock = true;
      idx += 1;
      currentId = start[1] ? start[1].trim() : `chart-${String(idx).padStart(3, '0')}`;
      out.push(`__HTML2PNG_BLOCK__${currentId}__`);
      buf = [];
      continue;
    }
    if (inBlock && /HTML2PNG:END/.test(line)) {
      writeBlock(currentId, buf);
      inBlock = false;
      currentId = '';
      buf = [];
      continue;
    }
    if (inBlock) {
      buf.push(line);
      continue;
    }
    out.push(line);
  }
  fs.writeFileSync(outMd, out.join('\n'), 'utf8');
  console.log(`mode=marker blocks=${idx}`);
  process.exit(0);
}

// Mode B: auto-detect <div>...</div> blocks
let i = 0;
while (i < lines.length) {
  const line = lines[i];
  const trimmed = line.trim();
  if (!trimmed.startsWith('<div')) {
    out.push(line);
    i += 1;
    continue;
  }

  // Start block
  idx += 1;
  const id = `auto-${String(idx).padStart(3, '0')}`;
  let depth = 0;
  const buf = [];

  while (i < lines.length) {
    const cur = lines[i];
    buf.push(cur);
    depth += countDivDelta(cur);
    i += 1;
    if (depth <= 0 && /<\/div>\s*$/.test(cur.trim())) {
      break;
    }
  }

  writeBlock(id, buf);
  out.push(`__HTML2PNG_BLOCK__${id}__`);
}

fs.writeFileSync(outMd, out.join('\n'), 'utf8');
console.log(`mode=auto blocks=${idx}`);
