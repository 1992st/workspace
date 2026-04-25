---
task_id: 2026-04-11-007
title: OpenClaw 与 Claude Code 记忆机制对比（源码级分析）
status: REVIEW_READY
domain: 技术演进推演 / 记忆机制研究
created_at: 2026-04-11T09:15:00+08:00
---

## 任务摘要
用户要求撰写一篇偏技术的文章，基于源码对比 OpenClaw 和 Claude Code 的记忆机制。

## 关键产出
- 正文：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-11-007-memory-clash/article.md`

## 内容结构
1. 文件结构对比（索引型 vs 时间线型）
2. 记忆写入机制（extractMemories/autoDream vs Flush+主动写）
3. 搜索/召回（grep-only vs hybrid vector+keyword）
4. Dream/整合目标差异（自愈合 vs 信号晋升）
5. 安全隔离（forked agent 沙盒 vs 主代理显式控制）
6. 扩展性（闭合系统 vs 插件化后端）
7. 三条可执行动作

## 源码引用
- Claude Code 泄露源码：`src/services/autoDream/autoDream.ts`
- Claude Code 泄露源码：`src/services/extractMemories/extractMemories.ts`
- Claude Code 泄露源码：`src/services/autoDream/consolidationPrompt.ts`
- OpenClaw 官方文档：`docs/concepts/memory.md`
- OpenClaw 官方文档：`docs/concepts/dreaming`

## 状态
- status: REVIEW_READY
