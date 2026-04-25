#!/usr/bin/env python3
import argparse
import html
import shutil
import pathlib
import re
import subprocess
import sys
from typing import Dict, List, Tuple


PLACEHOLDER_RE = re.compile(r"\{\{diagram:([a-zA-Z0-9._-]+)(?:\|([^}]+))?\}\}")
SIZE_HINT_RE = re.compile(r"diagram:size\s+(\d+)x(\d+)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build diagrams and generate article.publish.md from placeholders."
    )
    p.add_argument(
        "target",
        help="Task id (e.g. 2026-04-05-002) or absolute/relative task directory path.",
    )
    p.add_argument(
        "--root",
        default="/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk",
        help="Workspace root directory.",
    )
    return p.parse_args()


def resolve_task_dir(root: pathlib.Path, target: str) -> pathlib.Path:
    target_path = pathlib.Path(target)
    if target_path.exists():
        return target_path.resolve()
    return (root / "publish_queue" / target).resolve()


def safe_read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def safe_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_size_hint(source: str, default_w: int = 1200, default_h: int = 720) -> Tuple[int, int]:
    m = SIZE_HINT_RE.search(source)
    if not m:
        return default_w, default_h
    w = max(320, min(2400, int(m.group(1))))
    h = max(240, min(2400, int(m.group(2))))
    return w, h


def html_to_svg(source_html: str, title: str = "diagram") -> str:
    width, height = parse_size_hint(source_html)
    safe_html = source_html.strip()
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <style>
      .frame {{
        fill: #ffffff;
        stroke: #d9dde5;
        stroke-width: 2;
      }}
      .title {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 22px;
        font-weight: 600;
        fill: #1f2937;
      }}
    </style>
  </defs>
  <rect class="frame" x="1" y="1" width="{width-2}" height="{height-2}" rx="16"/>
  <text class="title" x="24" y="42">{html.escape(title)}</text>
  <foreignObject x="16" y="56" width="{width-32}" height="{height-72}">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
      {safe_html}
    </div>
  </foreignObject>
</svg>
"""
    return svg


def mmd_to_svg_with_mmdc(src: pathlib.Path, dst_svg: pathlib.Path, dst_png: pathlib.Path) -> bool:
    cmd = ["mmdc", "-i", str(src), "-o", str(dst_svg), "-b", "transparent", "-t", "neutral"]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    try:
        subprocess.run(
            ["mmdc", "-i", str(src), "-o", str(dst_png), "-b", "white", "-t", "neutral"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        # PNG is optional
        pass
    return True


def mmd_fallback_svg(src: pathlib.Path) -> str:
    content = safe_read(src)
    escaped = html.escape(content)
    lines = escaped.splitlines()
    width = 1200
    height = max(420, 170 + 24 * min(40, len(lines)))
    hint = "Mermaid CLI (mmdc) missing. Install it to render this as a real diagram."
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>
  <rect x="24" y="24" width="{width-48}" height="{height-48}" fill="#fff8e1" stroke="#f59e0b" stroke-width="2" rx="12"/>
  <text x="48" y="66" font-family="Menlo,Consolas,monospace" font-size="22" fill="#92400e">{html.escape(hint)}</text>
  <foreignObject x="48" y="90" width="{width-96}" height="{height-120}">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font-family:Menlo,Consolas,monospace;font-size:14px;line-height:1.45;color:#7c2d12;white-space:pre-wrap;">
{escaped}
    </div>
  </foreignObject>
</svg>
"""


def try_convert_svg_to_png(svg_file: pathlib.Path, png_file: pathlib.Path) -> bool:
    magick = shutil.which("magick")
    if magick:
        try:
            subprocess.run(
                [
                    magick,
                    "-background",
                    "white",
                    "-density",
                    "220",
                    str(svg_file),
                    "-resize",
                    "1600x1600>",
                    str(png_file),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return png_file.exists() and png_file.stat().st_size > 0
        except Exception:
            pass

    sips = shutil.which("sips")
    if sips:
        try:
            subprocess.run(
                [sips, "-s", "format", "png", str(svg_file), "--out", str(png_file)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return png_file.exists() and png_file.stat().st_size > 0
        except Exception:
            pass
    return False


def build_diagrams(src_dir: pathlib.Path, out_dir: pathlib.Path) -> Dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, str] = {}

    for png_file in sorted(src_dir.glob("*.png")):
        diagram_id = png_file.stem
        dst_png = out_dir / f"{diagram_id}.png"
        shutil.copy2(png_file, dst_png)
        manifest[diagram_id] = dst_png.name

    for html_file in sorted(src_dir.glob("*.html")):
        diagram_id = html_file.stem
        svg_file = out_dir / f"{diagram_id}.svg"
        png_file = out_dir / f"{diagram_id}.png"
        svg_content = html_to_svg(safe_read(html_file), title=diagram_id)
        safe_write(svg_file, svg_content)
        if try_convert_svg_to_png(svg_file, png_file):
            manifest[diagram_id] = png_file.name
        else:
            manifest[diagram_id] = svg_file.name

    for mmd_file in sorted(src_dir.glob("*.mmd")):
        diagram_id = mmd_file.stem
        svg_file = out_dir / f"{diagram_id}.svg"
        png_file = out_dir / f"{diagram_id}.png"
        if not mmd_to_svg_with_mmdc(mmd_file, svg_file, png_file):
            safe_write(svg_file, mmd_fallback_svg(mmd_file))
        manifest[diagram_id] = svg_file.name

    return manifest


def render_publish_article(article_in: pathlib.Path, article_out: pathlib.Path, out_dir: pathlib.Path) -> List[str]:
    text = safe_read(article_in)
    missing: List[str] = []

    def repl(match: re.Match) -> str:
        diagram_id = match.group(1)
        alt = (match.group(2) or diagram_id).strip()
        png_path = out_dir / f"{diagram_id}.png"
        if png_path.exists():
            return f"![{alt}](./diagrams/out/{diagram_id}.png)"
        svg_path = out_dir / f"{diagram_id}.svg"
        if svg_path.exists():
            return f"![{alt}](./diagrams/out/{diagram_id}.svg)"
        missing.append(diagram_id)
        return match.group(0)

    rendered = PLACEHOLDER_RE.sub(repl, text)
    safe_write(article_out, rendered)
    return sorted(set(missing))


def main() -> int:
    args = parse_args()
    root = pathlib.Path(args.root).resolve()
    task_dir = resolve_task_dir(root, args.target)
    if not task_dir.exists():
        print(f"[error] task directory not found: {task_dir}", file=sys.stderr)
        return 2

    article_in = task_dir / "article.md"
    if not article_in.exists():
        print(f"[error] article.md not found: {article_in}", file=sys.stderr)
        return 2

    src_dir = task_dir / "diagrams" / "src"
    out_dir = task_dir / "diagrams" / "out"
    article_out = task_dir / "article.publish.md"

    if not src_dir.exists():
        print(f"[warn] diagram source directory not found: {src_dir}")
        src_dir.mkdir(parents=True, exist_ok=True)

    manifest = build_diagrams(src_dir, out_dir)
    missing = render_publish_article(article_in, article_out, out_dir)

    print(f"[ok] task: {task_dir}")
    print(f"[ok] generated publish article: {article_out}")
    if manifest:
        print("[ok] diagrams built:")
        for k, v in sorted(manifest.items()):
            print(f"  - {k} -> diagrams/out/{v}")
        png_missing = [k for k in sorted(manifest.keys()) if not (out_dir / f"{k}.png").exists()]
        if png_missing:
            print("[warn] PNG not generated for diagrams below, publish will fall back to SVG:")
            for k in png_missing:
                print(f"  - {k}")
    else:
        print("[warn] no diagram sources found under diagrams/src")

    if missing:
        print("[warn] unresolved placeholders:")
        for item in missing:
            print(f"  - {item}")
    else:
        print("[ok] all diagram placeholders resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
