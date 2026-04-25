# Task 目录规范（2026-04-13）

## 目标
- `tasks/` 成为唯一工作目录
- 设计、研究、发布准备统一走 `tasks/`
- `dev-topics/` 停用，不再新增任务内容

## 标准结构

```text
tasks/
  <task_id>-<slug>/
    task.md
    article.md
    drafts/
    assets/
    backups/
```

约束：
- `task_id`: `YYYY-MM-DD-XXX`
- `slug`: `kebab-case`
- `drafts/` 禁止使用 `v2/v3/final` 命名

## task.md 要求

必须包含 frontmatter：

```yaml
---
task_id: 2026-04-13-001
title: ""
status: DRAFTING
owner: agent-radar-desk
created_at: "2026-04-13T00:00:00+08:00"
updated_at: "2026-04-13T00:00:00+08:00"
---
```

正文必须包含状态段（状态双写）：

```md
## 状态
- status: DRAFTING
```

## 状态机

`NEW -> SCOPING -> COLLECTING -> SYNTHESIZING -> DRAFTING -> REVIEW_READY -> APPROVED -> PACKAGED -> SENT`

## 迁移规则
- 历史 `tasks/*.md` 一律迁移到 `tasks/<task_id>-<slug>/task.md`
- 历史 `dev-topics/*` 一律并入 `tasks/<task_id>-<slug>/drafts/`
- 迁移完成后，`dev-topics/` 保留空目录或迁移记录，不再承载新内容
