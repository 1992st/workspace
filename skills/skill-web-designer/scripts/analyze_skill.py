#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TEXT_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".sh", ".py", ".txt"}
EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".cache", "viewer"}
EXCLUDED_NAMES = {".DS_Store", "viewer-flow-spec.json"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a skill directory into a web model.")
    parser.add_argument("--skill-root", required=True)
    parser.add_argument("--flow-spec", help="Path to agent-authored semantic flow spec JSON.")
    parser.add_argument("--model-out")
    parser.add_argument("--quality-out")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> tuple[dict[str, str], bool]:
    if not text.startswith("---\n"):
        return {}, False
    end = text.find("\n---", 4)
    if end == -1:
        return {}, False
    raw = text[4:end].strip()
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data, True


def iter_files(root: Path) -> list[Path]:
    results: list[Path] = []
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        if path.name in EXCLUDED_NAMES:
            continue
        if path.is_file():
            results.append(path)
    return sorted(results)


def file_type(rel: str) -> str:
    path = Path(rel)
    lowered = rel.lower()
    if rel == "SKILL.md":
        return "skill"
    if "/prompts/" in f"/{lowered}" or re.search(r"/config/.*prompt.*\.md$", f"/{lowered}"):
        return "prompt"
    if lowered.startswith("scripts/") or lowered.startswith("tools/") or re.search(r"\.(sh|py)$", lowered):
        return "script"
    if lowered.startswith("references/") or "/references/" in lowered:
        return "reference"
    if lowered.startswith("templates/") or "/templates/" in lowered:
        return "template"
    if lowered.startswith("config/") or re.search(r"\.(yaml|yml|json)$", lowered):
        return "config"
    if lowered.startswith("assets/"):
        return "asset"
    if lowered.startswith("_meta/") or lowered.endswith(("copy_plan.md", "refactor_plan.md", "expansion.md")):
        return "meta"
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return "text"
    return "asset"


def is_editable_prompt(rel: str) -> bool:
    lowered = f"/{rel.lower()}"
    return "/prompts/" in lowered and lowered.endswith(".md") or re.search(r"/config/.*prompt.*\.md$", lowered) is not None


def embedded_content(root: Path, rel: str) -> str | None:
    path = root / rel
    if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    return read_text(path)


def choose_mode(types: set[str]) -> str:
    has_prompt = "prompt" in types
    has_script = "script" in types
    has_template = "template" in types
    if has_template and (has_prompt or has_script):
        return "hybrid-flow"
    if has_template:
        return "template-flow"
    if has_script:
        return "script-flow"
    if has_prompt:
        return "prompt-flow"
    return "text-only"


def make_step(step_id: str, title: str, description: str, files: list[str]) -> dict:
    return {
        "id": step_id,
        "title": title,
        "description": description,
        "files": files,
    }


def build_fallback_flows(files: list[dict]) -> list[dict]:
    entry_files = [item["path"] for item in files if item["path"] == "SKILL.md"]
    return [
        {
            "id": "skill-overview",
            "title": "Skill Overview",
            "description": "Fallback overview only. A semantic flow spec was not provided by the agent.",
            "steps": [
                {
                    "id": "read-skill-md",
                    "title": "Read SKILL.md",
                    "description": "Open the skill entrypoint. Generate a semantic flow spec for a useful workflow view.",
                    "kind": "read",
                    "files": entry_files,
                }
            ],
        }
    ]


def load_flow_spec(path: Path | None) -> tuple[dict | None, str | None]:
    if path is None:
        return None, None
    raw = json.loads(read_text(path))
    if isinstance(raw, list):
        raw = {"flows": raw}
    if not isinstance(raw, dict):
        raise ValueError("flow spec must be an object or a list of flows")
    flows = raw.get("flows")
    if not isinstance(flows, list):
        raise ValueError("flow spec must be a list or an object with a flows list")
    return raw, str(path)


def normalize_flow_spec(spec: dict, files: list[dict]) -> tuple[dict, list[dict], list[dict]]:
    valid_paths = {item["path"] for item in files}
    findings: list[dict] = []
    normalized: list[dict] = []
    flows = spec.get("flows") or []

    def add_warning(code: str, message: str, path: str = "") -> None:
        findings.append({"severity": "warning", "code": code, "message": message, "path": path})

    summary = normalize_summary(spec.get("summary"))

    for flow_index, flow in enumerate(flows, start=1):
        if not isinstance(flow, dict):
            add_warning("invalid-flow", f"Flow #{flow_index} is not an object.")
            continue
        title = str(flow.get("title") or f"Flow {flow_index}").strip()
        flow_id = safe_id(str(flow.get("id") or title).lower())
        steps: list[dict] = []
        for step_index, step in enumerate(flow.get("steps") or [], start=1):
            if not isinstance(step, dict):
                add_warning("invalid-flow-step", f"Step #{step_index} in {title} is not an object.")
                continue
            step_title = str(step.get("title") or f"Step {step_index}").strip()
            requested_files = [str(path) for path in step.get("files") or []]
            existing_files = [path for path in requested_files if path in valid_paths]
            missing_files = [path for path in requested_files if path not in valid_paths]
            for missing in missing_files:
                add_warning("flow-file-missing", f"Flow step references a file that is not in the skill model: {missing}", missing)
            steps.append(
                {
                    "id": safe_id(str(step.get("id") or step_title).lower()),
                    "title": step_title,
                    "description": str(step.get("description") or "").strip(),
                    "kind": normalize_step_kind(step.get("kind")),
                    "evidence": normalize_file_refs(step.get("evidence"), valid_paths, add_warning),
                    "files": existing_files,
                }
            )
        if not steps:
            add_warning("flow-without-steps", f"Flow has no valid steps: {title}")
            continue
        normalized.append(
            {
                "id": flow_id,
                "title": title,
                "description": str(flow.get("description") or "").strip(),
                "intent": str(flow.get("intent") or "").strip(),
                "trigger": str(flow.get("trigger") or "").strip(),
                "inputs": normalize_text_list(flow.get("inputs")),
                "outputs": normalize_text_list(flow.get("outputs")),
                "decision_points": normalize_text_list(flow.get("decision_points")),
                "tuning_points": normalize_tuning_points(flow.get("tuning_points"), valid_paths, add_warning),
                "blockers": normalize_text_list(flow.get("blockers")),
                "steps": steps,
            }
        )

    if not normalized:
        add_warning("semantic-flow-invalid", "No valid semantic flows were found; falling back to Skill Overview.")
        normalized = build_fallback_flows(files)
    return summary, normalized, findings


def normalize_summary(value: object) -> dict:
    if not isinstance(value, dict):
        return {
            "responsibility": "",
            "when_to_use": [],
            "when_not_to_use": [],
            "core_outputs": [],
            "boundaries": [],
        }
    return {
        "responsibility": str(value.get("responsibility") or "").strip(),
        "when_to_use": normalize_text_list(value.get("when_to_use")),
        "when_not_to_use": normalize_text_list(value.get("when_not_to_use")),
        "core_outputs": normalize_text_list(value.get("core_outputs")),
        "boundaries": normalize_text_list(value.get("boundaries")),
    }


def normalize_text_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def normalize_file_refs(value: object, valid_paths: set[str], add_warning) -> list[str]:
    refs: list[str] = []
    for path in normalize_text_list(value):
        if path in valid_paths:
            refs.append(path)
        else:
            add_warning("flow-file-missing", f"Flow references a file that is not in the skill model: {path}", path)
    return refs


def normalize_tuning_points(value: object, valid_paths: set[str], add_warning) -> list[dict]:
    if not isinstance(value, list):
        return []
    results: list[dict] = []
    for index, item in enumerate(value, start=1):
        if isinstance(item, str):
            item = {"title": item}
        if not isinstance(item, dict):
            add_warning("invalid-tuning-point", f"Tuning point #{index} is not an object.")
            continue
        files = normalize_file_refs(item.get("files"), valid_paths, add_warning)
        results.append(
            {
                "title": str(item.get("title") or f"Tuning Point {index}").strip(),
                "description": str(item.get("description") or "").strip(),
                "files": files,
            }
        )
    return results


def normalize_step_kind(value: object) -> str:
    kind = str(value or "read").strip().lower()
    return kind if kind in {"read", "decide", "edit", "run", "verify", "report"} else "read"


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return cleaned or "step"


def quality_checks(
    root: Path,
    skill_text: str,
    frontmatter: dict[str, str],
    has_frontmatter: bool,
    files: list[dict],
    flow_source: str,
    summary: dict,
    flows: list[dict],
    flow_findings: list[dict],
) -> list[dict]:
    findings: list[dict] = []

    def add(severity: str, code: str, message: str, path: str = "") -> None:
        findings.append({"severity": severity, "code": code, "message": message, "path": path})

    if not (root / "SKILL.md").exists():
        add("error", "missing-skill-md", "SKILL.md is required.")
        return findings
    if not has_frontmatter:
        add("error", "missing-frontmatter", "SKILL.md must start with YAML frontmatter.", "SKILL.md")
    if not frontmatter.get("name"):
        add("error", "missing-name", "Frontmatter must include name.", "SKILL.md")
    elif not re.fullmatch(r"[a-z0-9-]{1,63}", frontmatter["name"]):
        add("warning", "name-format", "Skill name should use lowercase letters, digits, and hyphens.", "SKILL.md")
    if not frontmatter.get("description"):
        add("error", "missing-description", "Frontmatter must include description.", "SKILL.md")
    elif len(frontmatter["description"]) < 40:
        add("warning", "weak-description", "Description may be too short to guide triggering.", "SKILL.md")
    if len(skill_text.splitlines()) > 500:
        add("warning", "skill-md-long", "SKILL.md is long; move detailed content into references.", "SKILL.md")
    if flow_source != "semantic_agent":
        add("warning", "semantic-flow-missing", "No agent-authored semantic flow spec was provided; viewer uses fallback overview.", "SKILL.md")
    findings.extend(flow_findings)
    if flow_source == "semantic_agent":
        if not summary.get("responsibility"):
            add("warning", "weak-agent-explanation", "Semantic spec should explain the skill responsibility in summary.responsibility.", "SKILL.md")
        for flow in flows:
            title = flow.get("title", "")
            if not flow.get("intent") or not flow.get("inputs") or not flow.get("outputs"):
                add("warning", "shallow-flow-model", f"Flow should include intent, inputs, and outputs: {title}", "viewer-flow-spec.json")
            if not flow.get("tuning_points"):
                add("warning", "missing-tuning-points", f"Flow should identify user-tunable prompts, rules, configs, or scripts: {title}", "viewer-flow-spec.json")
            if not flow.get("blockers"):
                add("info", "missing-blockers", f"Flow has no blockers listed; verify that is intentional: {title}", "viewer-flow-spec.json")
            for step in flow.get("steps", []):
                if not (step.get("evidence") or step.get("files")):
                    add("warning", "missing-step-evidence", f"Step should link to evidence files: {step.get('title', '')}", "viewer-flow-spec.json")

    type_set = {item["type"] for item in files}
    lower_skill = skill_text.lower()
    for resource_type in ["prompt", "script", "reference", "template"]:
        if resource_type in type_set and resource_type + "s" not in lower_skill and resource_type not in lower_skill:
            add("info", f"undocumented-{resource_type}", f"{resource_type} files exist but SKILL.md may not explain when to use them.", "SKILL.md")

    for item in files:
        path = item["path"]
        lowered = path.lower()
        if any(part in lowered for part in [".git/", "node_modules/", "/tmp/", ".bak"]):
            add("warning", "excluded-artifact", "Skill contains artifact-like paths that should not be bundled.", path)
        if item["type"] == "script":
            add("info", "script-review", "Check script dependencies, inputs, outputs, and safety boundaries.", path)
        if re.search(r"(^|/)(user|auth|token|credential|secret)", lowered):
            add("warning", "private-value-risk", "File path suggests private or credential data; review before publishing.", path)

    absolute_pattern = re.compile(r"(/Users/|/Volumes/|/home/|[A-Za-z]:\\\\)")
    for item in files:
        if item["type"] not in {"asset"} and Path(root / item["path"]).suffix.lower() in TEXT_EXTENSIONS:
            text = read_text(root / item["path"])
            if absolute_pattern.search(text):
                add("warning", "absolute-path", "File contains absolute paths; verify they are intentional or parameterized.", item["path"])
                break

    return findings


def analyze(root: Path, flow_spec_path: Path | None = None) -> tuple[dict, dict]:
    skill_path = root / "SKILL.md"
    skill_text = read_text(skill_path) if skill_path.exists() else ""
    frontmatter, has_frontmatter = parse_frontmatter(skill_text)

    file_items: list[dict] = []
    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        typ = file_type(rel)
        file_items.append(
            {
                "path": rel,
                "type": typ,
                "editable": is_editable_prompt(rel),
                "content": embedded_content(root, rel),
            }
        )

    mode = choose_mode({item["type"] for item in file_items})
    flow_spec, flow_spec_source = load_flow_spec(flow_spec_path)
    if flow_spec is None:
        summary = normalize_summary(None)
        flows = build_fallback_flows(file_items)
        flow_findings: list[dict] = []
        flow_source = "fallback_structural"
    else:
        summary, flows, flow_findings = normalize_flow_spec(flow_spec, file_items)
        flow_source = "semantic_agent"
    model = {
        "skill": {
            "name": frontmatter.get("name", root.name),
            "description": frontmatter.get("description", ""),
            "path": str(root),
            "mode": mode,
            "flow_source": flow_source,
            "flow_spec": flow_spec_source,
        },
        "summary": summary,
        "files": file_items,
        "flows": flows,
        "editable": [item["path"] for item in file_items if item["editable"]],
    }
    findings = quality_checks(root, skill_text, frontmatter, has_frontmatter, file_items, flow_source, summary, flows, flow_findings)
    report = {
        "skill": model["skill"],
        "summary": {
            "errors": sum(1 for item in findings if item["severity"] == "error"),
            "warnings": sum(1 for item in findings if item["severity"] == "warning"),
            "info": sum(1 for item in findings if item["severity"] == "info"),
        },
        "findings": findings,
    }
    return model, report


def main() -> int:
    args = parse_args()
    root = Path(args.skill_root).resolve()
    flow_spec_path = Path(args.flow_spec).resolve() if args.flow_spec else None
    model, report = analyze(root, flow_spec_path)

    if args.model_out:
        Path(args.model_out).write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        print(json.dumps(model, ensure_ascii=False, indent=2))
    if args.quality_out:
        Path(args.quality_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
