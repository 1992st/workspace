#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from html import escape
from pathlib import Path

from analyze_skill import analyze


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
VIEWER_TEMPLATE = SKILL_ROOT / "templates" / "static-viewer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a static web viewer for a skill.")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--flow-spec", help="Path to agent-authored semantic flow spec JSON.")
    return parser.parse_args()


def copy_template(dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for item in VIEWER_TEMPLATE.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)


def embed_json(index_path: Path, model: dict, report: dict) -> None:
    html = index_path.read_text(encoding="utf-8")
    model_json = escape(json.dumps(model, ensure_ascii=False), quote=False)
    report_json = escape(json.dumps(report, ensure_ascii=False), quote=False)
    html = html.replace(
        "<!-- SKILL_MODEL_JSON -->",
        f'<script id="skill-model-data" type="application/json">{model_json}</script>',
    )
    html = html.replace(
        "<!-- QUALITY_REPORT_JSON -->",
        f'<script id="quality-report-data" type="application/json">{report_json}</script>',
    )
    index_path.write_text(html, encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = Path(args.skill_root).resolve()
    flow_spec_path = Path(args.flow_spec).resolve() if args.flow_spec else None
    viewer_dir = root / "viewer"
    model, report = analyze(root, flow_spec_path)

    copy_template(viewer_dir)
    (viewer_dir / "skill-model.json").write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    (viewer_dir / "quality-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if flow_spec_path:
        shutil.copy2(flow_spec_path, viewer_dir / "flow-spec.json")
    embed_json(viewer_dir / "index.html", model, report)

    print(
        json.dumps(
            {
                "viewer": str(viewer_dir / "index.html"),
                "model": str(viewer_dir / "skill-model.json"),
                "quality_report": str(viewer_dir / "quality-report.json"),
                "mode": model["skill"]["mode"],
                "flow_source": model["skill"]["flow_source"],
                "flow_spec": model["skill"]["flow_spec"],
                "findings": report["summary"],
                "viewer_status": "ready_static",
                "load_strategy": "embedded_json",
                "requires_directory_for_browsing": False,
                "requires_directory_for_editing": True,
                "open_method": "file:// supported",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
