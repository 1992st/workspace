---
name: skill-web-designer
description: "Generate static web viewers for local Codex/OpenClaw skills. Use when the user asks to visualize a skill, generate a skill web page, inspect prompts/scripts/references/templates, edit prompt files through a local browser page, or evaluate whether a SKILL.md is suitable for agent use."
metadata:
  openclaw:
    emoji: "🧩"
    user-invocable: true
    triggers:
      - "生成skill网页"
      - "skill可视化"
      - "skill web"
      - "查看skill结构"
      - "skill质量检查"
      - "prompt编辑页面"
---

# Skill Web Designer

Use this skill to turn a local skill directory into a static web viewer that explains what the skill does, how its agent workflow runs, and where each flow can be tuned.

## Core Idea

Do not hard-code flows in the viewer and do not use file-type groups as workflow names. First read the target skill, create an agent-authored semantic flow spec from its real behavior, then render an explanation-oriented model.

The viewer must answer:
- What does this agent do?
- When should or should not this skill be used?
- What are the main flows?
- What inputs, decisions, blockers, and outputs exist in each flow?
- Which prompts, rules, configs, templates, or scripts can be tuned?
- Which files prove each claim?

Outputs:
- `<skill-root>/viewer/skill-model.json`
- `<skill-root>/viewer/quality-report.json`
- `<skill-root>/viewer/flow-spec.json` when a semantic spec is provided
- `<skill-root>/viewer/index.html`
- `<skill-root>/viewer/app.js`
- `<skill-root>/viewer/styles.css`

## Workflow

1. Confirm the target directory contains `SKILL.md`.
2. Read the target `SKILL.md`. If it references specific prompts, references, scripts, templates, or config files needed to understand the workflow, read only those files.
3. Read `references/model-schema.md` and write a semantic flow spec JSON. Flow titles must describe the target skill's real user-facing actions, not resource types.
4. The spec must include a `summary` and, for each flow, `intent`, `inputs`, `outputs`, `decision_points`, `blockers`, `tuning_points`, and evidence files.
5. Run:

```bash
python3 skills/skill-web-designer/scripts/generate_viewer.py --skill-root <target-skill-root> --flow-spec <flow-spec-json>
```

6. Check the generator output. Only report the viewer as directly usable when `viewer_status` is `ready_static`.
7. Open `<target-skill-root>/viewer/index.html` in a browser.

## Rules

- Do not change the target skill format; `SKILL.md` remains the entrypoint.
- Do not generate fixed flows such as `Skill Entry`, `Prompt Flow`, `Script and Tool Flow`, `Template Flow`, or `Supporting Docs and Config` unless those are explicit concepts in the target skill.
- Do not generate a file browser disguised as a workflow. Every flow needs user-facing intent, required inputs, expected outputs, blockers, and tuning points.
- If no semantic flow spec is provided, the script must only generate a fallback overview and a `semantic-flow-missing` warning.
- The generated viewer must embed the target `skill-model` and `quality-report` in `index.html` so it can be opened directly via `file://`.
- The viewer may also write `skill-model.json` and `quality-report.json` for debugging and tooling.
- Prompt files may be editable through the browser when File System Access API is available.
- Scripts, tools, references, configs, and `SKILL.md` are read-only in the viewer.
- The quality report provides findings and suggestions only; do not auto-fix target skills.
- Directory selection is only for reading file contents and editing prompt files; browsing the generated skill model must work without directory import.
