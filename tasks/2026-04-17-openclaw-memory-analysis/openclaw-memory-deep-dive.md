# OpenClaw Memory 机制深度解析

> 本文基于 OpenClaw 官方文档、GitHub 源码和社区最佳实践整理

---

## 1. 核心架构概览

OpenClaw 的 Memory 系统不是单一的"记忆模块"，而是**四层协作体系**：

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Bootstrap Files (永久层)                          │
│  - SOUL.md, AGENTS.md, USER.md, MEMORY.md, TOOLS.md         │
│  - 每次会话重新加载，survives everything                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Session Transcript (半永久层)                       │
│  - JSONL 格式存储在磁盘                                     │
│  - 可被 compaction 压缩成摘要                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: LLM Context Window (临时层)                         │
│  - 模型实际"看到"的内容                                     │
│  - 固定大小 (约 200K tokens)                                │
│  - 溢出时触发 compaction                                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Retrieval Index (搜索层)                           │
│  - memory_search / memory_get 工具                          │
│  - 基于向量 + 关键词的混合搜索                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 文件结构详解

### 2.1 核心记忆文件

| 文件 | 用途 | 加载时机 | 持久性 |
|------|------|----------|--------|
| `MEMORY.md` | 长期记忆：稳定事实、用户偏好、决策 | 每次会话开始 | 永久 |
| `memory/YYYY-MM-DD.md` | 每日笔记：运行上下文、观察 | 今天+昨天自动加载 | 永久 |
| `DREAMS.md` | 梦境日记： dreaming 阶段总结 | 可选，人工审阅 | 永久 |
| `SOUL.md` | 代理个性与语气 | 每次会话开始 | 永久 |
| `AGENTS.md` | 代理角色定义 | 每次会话开始 | 永久 |
| `USER.md` | 用户偏好 | 每次会话开始 | 永久 |
| `TOOLS.md` | 工具使用规范 | 每次会话开始 | 永久 |

### 2.2 关键原则

> **核心原则：如果它没有被写入文件，它就不存在。**

这是 OpenClaw Memory 系统的黄金法则。任何只存在于对话中的指令、偏好或决策都可能在 compaction 时丢失。

---

## 3. Compaction（压缩）机制

### 3.1 什么是 Compaction？

当对话接近模型的上下文窗口限制时，OpenClaw 会将旧消息**压缩成摘要**，以便继续对话。

**触发条件：**
- 上下文接近 token 限制
- 模型返回溢出错误 (如 `request_too_large`, `context length exceeded`)

### 3.2 Compaction 的生命周期

```
正常路径（有预留空间）:                           异常路径（溢出恢复）:
┌─────────────────┐                               ┌─────────────────┐
│ 上下文接近限制   │                               │ 上下文溢出      │
└────────┬────────┘                               └────────┬────────┘
         ↓                                                ↓
┌─────────────────┐                               ┌─────────────────┐
│ Memory Flush    │                               │ 直接进入压缩    │
│ (自动保存重要    │                               │ 无 flush 阶段   │
│  内容到磁盘)     │                               │ 最大信息丢失    │
└────────┬────────┘                               └────────┬────────┘
         ↓                                                ↓
┌─────────────────┐                               ┌─────────────────┐
│ Compaction      │                               │ Compaction      │
│ (旧消息变摘要)   │                               │ (紧急压缩)      │
└────────┬────────┘                               └────────┬────────┘
         ↓                                                ↓
┌─────────────────┐                               ┌─────────────────┐
│ 继续对话        │                               │ 重试原请求      │
│ (摘要+新消息)   │                               │                 │
└─────────────────┘                               └─────────────────┘
```

### 3.3 什么能 survive compaction？

| 能存活 | 不能存活 |
|--------|----------|
| 所有工作区文件 (SOUL.md, AGENTS.md 等) | 仅存在于对话中的指令 |
| 写入 memory/YYYY-MM-DD.md 的内容 | 会话中的偏好、修正、决策 |
| 最近约 20K tokens 的消息 | compaction 前的所有图片 |
| 文件路径和 ID | 工具结果的完整上下文 |
| | 原始指令的细节和细微差别 |

---

## 4. Memory Flush（预压缩刷新）机制

### 4.1 核心 Prompt（来自 flush-plan.ts 源码）

这是 OpenClaw 最关键的 safety net，**在 compaction 前自动触发**：

**默认 Memory Flush Prompt:**
```typescript
export const DEFAULT_MEMORY_FLUSH_PROMPT = [
  "Pre-compaction memory flush.",
  "Store durable memories only in memory/YYYY-MM-DD.md (create memory/ if needed).",
  "Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them.",
  "If memory/YYYY-MM-DD.md already exists, APPEND new content only and do not overwrite existing entries.",
  "Do NOT create timestamped variant files (e.g., YYYY-MM-DD-HHMM.md); always use the canonical YYYY-MM-DD.md filename.",
  "If nothing to store, reply with NO_REPLY.",
].join(" ");
```

**默认 Memory Flush System Prompt:**
```typescript
export const DEFAULT_MEMORY_FLUSH_SYSTEM_PROMPT = [
  "Pre-compaction memory flush turn.",
  "The session is near auto-compaction; capture durable memories to disk.",
  "Store durable memories only in memory/YYYY-MM-DD.md (create memory/ if needed).",
  "Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them.",
  "If memory/YYYY-MM-DD.md already exists, APPEND new content only and do not overwrite existing entries.",
  "You may reply, but usually NO_REPLY is correct.",
].join(" ");
```

### 4.2 关键配置参数

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "reserveTokensFloor": 40000,      // 预留 token 数
        "memoryFlush": {
          "enabled": true,                  // 启用 flush
          "softThresholdTokens": 4000,      // 提前触发阈值
          "systemPrompt": "Session nearing compaction. Store durable memories now.",
          "prompt": "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store."
        }
      }
    }
  }
}
```

### 4.3 计算触发点

```
触发点 = 上下文窗口上限 - reserveTokensFloor - softThresholdTokens

例如：
- 上下文窗口: 200,000 tokens
- reserveTokensFloor: 40,000
- softThresholdTokens: 4,000
- 触发点: 200,000 - 40,000 - 4,000 = 156,000 tokens
```

---

## 5. Memory Search 机制

### 5.1 混合搜索架构

```
Query ──┬──> Embedding ──> Vector Search ──┐
        │                                  ├──> Weighted Merge ──> Top Results
        └──> Tokenize ───> BM25 Search ────┘
               (关键词匹配)
```

### 5.2 支持的 Embedding 提供商

| 提供商 | ID | 需要 API Key | 特点 |
|--------|-----|-------------|------|
| OpenAI | `openai` | Yes | 快速，默认自动检测 |
| Gemini | `gemini` | Yes | 支持图片/音频索引 |
| Voyage | `voyage` | Yes | 高质量 |
| Mistral | `mistral` | Yes | 自动检测 |
| GitHub Copilot | `github-copilot` | No | 使用 Copilot 订阅 |
| Local | `local` | No | GGUF 模型，约 0.6GB |
| Ollama | `ollama` | No | 本地，需显式配置 |
| Bedrock | `bedrock` | No | AWS 凭证链自动检测 |

### 5.3 可选增强功能

**Temporal Decay（时间衰减）:**
- 旧笔记逐渐失去排名权重
- 默认半衰期：30 天（一个月前的笔记权重为 50%）
- 常青文件如 `MEMORY.md` 不衰减

**MMR（最大边际相关性）:**
- 减少冗余结果
- 确保 Top 结果覆盖不同主题

---

## 6. Dreaming（梦境）机制

### 6.1 三阶段模型

| 阶段 | 目的 | 写入长期记忆 | 输出位置 |
|------|------|------------|----------|
| **Light** | 排序和暂存近期短期材料 | 否 | `## Light Sleep` in DREAMS.md |
| **Deep** | 评分和提升持久候选 | 是 (MEMORY.md) | `## Deep Sleep` in DREAMS.md |
| **REM** | 反思主题和重复想法 | 否 | `## REM Sleep` in DREAMS.md |

### 6.2 Deep Ranking 信号权重

| 信号 | 权重 | 描述 |
|------|------|------|
| Frequency | 0.24 | 条目积累的短期信号数量 |
| Relevance | 0.30 | 条目的平均检索质量 |
| Query Diversity | 0.15 | 触发条目的不同查询/天上下文 |
| Recency | 0.15 | 时间衰减的新鲜度分数 |
| Consolidation | 0.10 | 多天重复强度 |
| Conceptual Richness | 0.06 | 片段/路径的概念标签密度 |

### 6.3 提升阈值

候选必须同时满足：
- `minScore` - 最低综合得分
- `minRecallCount` - 最少召回次数
- `minUniqueQueries` - 最少不同查询数

---

## 7. 完整 Prompt 汇总

### 7.1 Memory Flush Prompts

**用户提示 (DEFAULT_MEMORY_FLUSH_PROMPT):**
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

**系统提示 (DEFAULT_MEMORY_FLUSH_SYSTEM_PROMPT):**
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

### 7.2 安全提示常量 (来自 flush-plan.ts)

```typescript
const MEMORY_FLUSH_TARGET_HINT =
  "Store durable memories only in memory/YYYY-MM-DD.md (create memory/ if needed).";

const MEMORY_FLUSH_APPEND_ONLY_HINT =
  "If memory/YYYY-MM-DD.md already exists, APPEND new content only and do not overwrite existing entries.";

const MEMORY_FLUSH_READ_ONLY_HINT =
  "Treat workspace bootstrap/reference files such as MEMORY.md, DREAMS.md, SOUL.md, TOOLS.md, and AGENTS.md as read-only during this flush; never overwrite, replace, or edit them.";
```

---

## 8. 最佳实践总结

### 8.1 三条最重要的原则

1. **将持久规则放入文件，而非对话**
   - MEMORY.md 和 AGENTS.md 能 survive compaction
   - 对话中的指令不会

2. **启用 Memory Flush 并预留足够空间**
   - 默认已启用，但检查 `reserveTokensFloor` 是否足够
   - 建议：40K 预留（默认 20K 可能太紧）

3. **让记忆检索成为强制步骤**
   - 在 AGENTS.md 中添加规则："search memory before acting"
   - 否则代理会猜测而非查阅笔记

### 8.2 诊断命令

```bash
# 检查上下文
/context list

# 检查记忆索引状态
openclaw memory status
openclaw memory status --deep

# 重建索引
openclaw memory index --force

# 检查 dreaming 状态
/dreaming status
```

### 8.3 手动保存技巧

```
# 在关键决策点后手动触发保存
Save this to MEMORY.md

# 或者
Write today's key decisions to memory

# 手动 compaction（在你控制的时机）
/compact Focus on decisions and open questions
```

---

## 9. 常见失败模式

### 9.1 Failure A: "从未存储"
- 指令只存在于对话中
- 从未写入文件
- **解决方案：** 养成手动保存习惯

### 9.2 Failure B: "Compaction 改变了上下文"
- 长会话达到 token 限制
- Compaction 总结了旧消息
- 总结是 lossy 的：丢失了细节
- **解决方案：** 使用 `/compact` 主动控制时机

### 9.3 Failure C: "会话修剪删除了工具结果"
- 工具输出被修剪以优化缓存
- 代理"忘记"了工具返回的内容
- 这是临时的；磁盘上的 transcript 未被修改
- **解决方案：** 将关键工具结果保存到 memory 文件

---

## 10. 配置参考

### 10.1 推荐配置（基于 velvetshark.com 的 Masterclass）

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "reserveTokensFloor": 40000,
        "memoryFlush": {
          "enabled": true,
          "softThresholdTokens": 4000,
          "systemPrompt": "Session nearing compaction. Store durable memories now.",
          "prompt": "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store."
        }
      },
      "contextPruning": {
        "mode": "cache-ttl",
        "ttl": "5m"
      },
      "memorySearch": {
        "query": {
          "hybrid": {
            "mmr": { "enabled": true },
            "temporalDecay": { "enabled": true }
          }
        }
      }
    }
  }
}
```

### 10.2 启用 Dreaming

```json
{
  "plugins": {
    "entries": {
      "memory-core": {
        "config": {
          "dreaming": {
            "enabled": true,
            "timezone": "America/Los_Angeles",
            "frequency": "0 3 * * *"
          }
        }
      }
    }
  }
}
```

---

## 11. 参考来源

1. OpenClaw 官方文档: https://docs.openclaw.ai/concepts/memory
2. Memory Search 文档: https://docs.openclaw.ai/concepts/memory-search
3. Compaction 文档: https://docs.openclaw.ai/concepts/compaction
4. Dreaming 文档: https://docs.openclaw.ai/concepts/dreaming
5. OpenClaw Memory Masterclass: https://velvetshark.com/openclaw-memory-masterclass
6. GitHub 源码 (flush-plan.ts): https://github.com/openclaw/openclaw/blob/main/extensions/memory-core/src/flush-plan.ts
7. GitHub 源码 (memory-core/index.ts): https://github.com/openclaw/openclaw/blob/main/extensions/memory-core/index.ts

---

*整理时间: 2026-04-17*
*基于 OpenClaw v2026.2.23+ 版本*
