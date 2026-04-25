---
task_id: 2026-04-05-004
title: "Task: 2026-04-05-004"
status: REVIEW_READY
owner: agent-radar-desk
created_at: "2026-04-13T15:16:22+0800"
updated_at: "2026-04-13T15:16:22+0800"
---

## 状态
- status: REVIEW_READY

## 迁移信息
- source: /Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-05-004-task-2026-04-05-004/legacy/2026-04-05-004.md

## Legacy Notes

# Task: 2026-04-05-004

## 标题
Agent观察室：cron 投递修复 + 选题四层深研落地

## 状态
REVIEW_READY

## 本次改动
1. 将 `radar-daily-0800` / `radar-daily-1900` / `radar-weekly-friday-2000` 的 delivery 从 `mode:none` 改为飞书 announce 投递
2. 将上述 3 条任务 `payload.lightContext` 改为 `true`，降低 08:00 限流概率
3. 新增 `tools/cron_guard.sh`，将失败或未送达任务自动转为 `NEEDS_INPUT`
4. 新增选题规范：四层深研（45 分钟）

## 关键证据（绝对路径）
- OpenClaw cron 配置：`/Users/zhangst/.openclaw/cron/jobs.json`
- 运行记录：`/Users/zhangst/.openclaw/cron/runs/radar-daily-0800.jsonl`
- 运行记录：`/Users/zhangst/.openclaw/cron/runs/radar-daily-1900.jsonl`
- 运行记录：`/Users/zhangst/.openclaw/cron/runs/radar-weekly-friday-2000.jsonl`
- 工具脚本：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tools/cron_guard.sh`
- 选题规范：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/guides/topic-deep-research.md`

## 自动告警结果
- 已自动生成 `NEEDS_INPUT`：
  - `/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-05-001-task-2026-04-05-001/legacy/2026-04-05-001.md`
  - `/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-05-002-task-2026-04-05-002/legacy/2026-04-05-002.md`
  - `/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-05-003-task-2026-04-05-003/legacy/2026-04-05-003.md`

## 下一步
1. 等待下一个 19:00 与次日 08:00 窗口，验证 `delivered=true`
2. 若仍有飞书 400，继续走纯文本投递并排查 Feishu 卡片权限
3. 按四层深研规范跑一次正式选题并复核质量
