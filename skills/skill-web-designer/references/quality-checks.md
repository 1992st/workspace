# Quality Checks

The quality report is advisory. It does not modify target files.

## Required Checks

- `SKILL.md` exists.
- YAML frontmatter exists.
- Frontmatter has `name`.
- Frontmatter has `description`.
- Skill name uses lowercase letters, digits, and hyphens.
- Description names clear trigger/use cases.
- `SKILL.md` is not overly long.
- Bundled resources are referenced from `SKILL.md` when important.
- Prompt files have scenario or route context.
- Scripts/tools have dependency or usage notes.
- Templates have expansion rules.
- `.git`, `node_modules`, `tmp`, caches, and backup files are flagged.
- Obvious absolute paths, tokens, usernames, or private values are flagged for review.

## Severity

- `error`: likely breaks discovery or loading.
- `warning`: likely harms agent usage or maintenance.
- `info`: useful improvement.
