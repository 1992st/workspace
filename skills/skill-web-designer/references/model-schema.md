# Skill Model Schema

`skill-model.json` is the stable interface between analysis and the web viewer.

## Top Level

```json
{
  "skill": {
    "name": "skill-name",
    "description": "frontmatter description",
    "path": "/abs/path/to/skill",
    "mode": "hybrid-flow",
    "flow_source": "semantic_agent",
    "flow_spec": "/abs/path/to/flow-spec.json"
  },
  "summary": {
    "responsibility": "One-sentence explanation of what this skill-agent does.",
    "when_to_use": [],
    "when_not_to_use": [],
    "core_outputs": [],
    "boundaries": []
  },
  "files": [],
  "flows": [],
  "editable": []
}
```

## File Item

```json
{
  "path": "prompts/example.md",
  "type": "prompt",
  "editable": true,
  "content": "embedded text content when available"
}
```

`content` is embedded for text-like files so the generated `viewer/index.html` can be opened directly with `file://` and still display the current skill. Local directory binding is only required for reading a newer filesystem copy or saving editable prompt changes.

The generated `viewer/` directory is an output artifact and must be excluded from future analysis. Otherwise repeated generation can recursively include old viewer files in the next model.

Allowed file types:
- `skill`
- `prompt`
- `script`
- `reference`
- `template`
- `config`
- `asset`
- `meta`
- `text`

## Flow Item

Flows must describe the target skill's real workflow. They are authored by the agent after reading the target `SKILL.md` and any necessary referenced files. They are not generated from file types.

```json
{
  "id": "collect-project-truth",
  "title": "Collect Project Truth",
  "description": "Gather the concrete project facts required before generating an embedded maintenance agent.",
  "intent": "Prevent the agent from guessing project paths, branches, tools, or issue sources.",
  "trigger": "User asks to initialize or create an embedded project maintenance agent.",
  "inputs": ["project id", "workspace root", "code paths"],
  "outputs": ["project-profile.yaml draft", "TODO(user) list"],
  "decision_points": ["Known values are copied; unknown values become TODO(user)."],
  "blockers": ["Missing code path", "Missing build command"],
  "tuning_points": [
    {
      "title": "Required field policy",
      "description": "Adjust which fields block initialization.",
      "files": ["_meta/VARIABLE_SCHEMA.md"]
    }
  ],
  "steps": [
    {
      "id": "read-variable-schema",
      "title": "Read Variable Schema",
      "description": "Identify required fields and mark unknown values as TODO(user).",
      "kind": "read",
      "evidence": ["_meta/VARIABLE_SCHEMA.md"],
      "files": ["_meta/VARIABLE_SCHEMA.md"]
    }
  ]
}
```

Allowed step kinds:
- `read`
- `decide`
- `edit`
- `run`
- `verify`
- `report`

## Semantic Flow Spec Input

`generate_viewer.py` accepts an agent-authored flow spec:

```bash
python3 skills/skill-web-designer/scripts/generate_viewer.py --skill-root <skill-root> --flow-spec <flow-spec-json>
```

The spec may be either a JSON list of flows or an object with a `flows` list:

```json
{
  "summary": {
    "responsibility": "Coordinate PMS work items, workloads, project issue tracking, and requirement sync.",
    "when_to_use": ["User asks about workload, PMS work items, project bugs, or requirement sync."],
    "when_not_to_use": ["User asks for unrelated local code refactors."],
    "core_outputs": ["PMS query result", "write-operation draft", "sync report"],
    "boundaries": ["Write operations require user confirmation."]
  },
  "flows": [
    {
      "id": "route-pms-scenario",
      "title": "Route PMS Scenario",
      "description": "Choose the correct PMS workflow before reading detailed prompts or tools.",
      "intent": "Select the right route before loading prompts or running PMS tools.",
      "trigger": "User request matches workload, work item, bug tracking, project report, or requirement sync.",
      "inputs": ["user request", "tracked project config"],
      "outputs": ["selected PMS workflow"],
      "decision_points": ["workload vs work item vs project issue vs requirement sync"],
      "blockers": ["unknown tracked project", "missing CLI dependency"],
      "tuning_points": [
        {
          "title": "Scene routing prompt",
          "description": "Tune how the agent classifies PMS scenarios.",
          "files": ["SKILL.md"]
        }
      ],
      "steps": [
        {
          "id": "read-skill-routing",
          "title": "Read Scene Routing",
          "description": "Use the scene routing section in SKILL.md to select the next prompt or reference.",
          "kind": "read",
          "evidence": ["SKILL.md"],
          "files": ["SKILL.md"]
        }
      ]
    }
  ]
}
```

Every `files` entry should reference a path present in the target skill model. Missing paths are removed from the rendered step and reported as quality warnings.

Quality expectations:
- `summary.responsibility` should be present.
- Every flow should include `intent`, `inputs`, `outputs`, and `tuning_points`.
- Every step should link to evidence through `evidence` or `files`.
- Use `blockers` to explain when the agent must stop and ask the user.
