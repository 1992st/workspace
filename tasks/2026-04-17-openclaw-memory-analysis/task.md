---
task_id: 2026-04-17-001
slug: openclaw-memory-analysis
status: COMPLETED
created: 2026-04-17
completed: 2026-04-17
---

# OpenClaw Memory 机制深度解析

## 状态
COMPLETED

## 目标
整理 OpenClaw 源码，详细介绍 memory 整理机制，完整呈现对应的 prompts。

## 输出
- 主文档: `/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-17-openclaw-memory-analysis/openclaw-memory-deep-dive.md`

## 核心发现

### 1. Memory 四层架构
1. Bootstrap Files (永久层) - SOUL.md, AGENTS.md, USER.md, MEMORY.md
2. Session Transcript (半永久层) - JSONL 存储，可被压缩
3. LLM Context Window (临时层) - 200K tokens 限制
4. Retrieval Index (搜索层) - memory_search / memory_get

### 2. 核心 Prompt 汇总

**Memory Flush User Prompt:**
```
Pre-compaction memory flush. 
Store durable memories only in memory/YYYY-MM-DD.md (create memory/ if needed). 
Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, 
TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, 
or edit them. 
If memory/YYYY-MM-DD.md already exists, APPEND new content only and do not 
overwrite existing entries. 
Do NOT create timestamped variant files (e.g., YYYY-MM-DD-HHMM.md); always use 
the canonical YYYY-MM-DD.md filename. 
If nothing to store, reply with NO_REPLY.
```

**Memory Flush System Prompt:**
```
Pre-compaction memory flush turn. 
The session is near auto-compaction; capture durable memories to disk. 
Store durable memories only in memory/YYYY-MM-DD.md (create memory/ if needed). 
Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, 
TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, 
or edit them. 
If memory/YYYY-MM-DD.md already exists, APPEND new content only and do not 
overwrite existing entries. 
You may reply, but usually NO_REPLY is correct.
```

### 3. 关键安全提示常量 (来自 flush-plan.ts)
- `MEMORY_FLUSH_TARGET_HINT`: 指定存储目标路径
- `MEMORY_FLUSH_APPEND_ONLY_HINT`: 强制追加模式
- `MEMORY_FLUSH_READ_ONLY_HINT`: 保护引导文件不被覆盖

### 4. 触发条件
- 触发点 = 上下文窗口上限 - reserveTokensFloor(40K) - softThresholdTokens(4K)
- 例如：200K - 40K - 4K = 156K tokens 时触发

### 5. 黄金法则
> "如果它没有被写入文件，它就不存在。"

## 参考来源
- OpenClaw 官方文档
- GitHub 源码: flush-plan.ts, memory-core/index.ts
- Velvetshark Memory Masterclass
