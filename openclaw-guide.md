# OpenClaw 不完全指南
## 理解 Agent 的记忆系统与 Workspace 文件

---

## 📋 目录

1. [OpenClaw 是什么？](#1-openclaw-是什么)
2. [Workspace 文件系统](#2-workspace-文件系统)
3. [文件调用机制与权重](#3-文件调用机制与权重)
4. [四层记忆系统](#4-四层记忆系统)
5. [常见失败模式](#5-常见失败模式)
6. [最佳实践](#6-最佳实践)
7. [快速检查清单](#7-快速检查清单)
8. [附录：模版文件提示词摘选](#附录模版文件提示词摘选)

---

## 1. OpenClaw 是什么？

### 一句话定义

> **OpenClaw 是 AI Agent 的"操作系统"** —— 它让 LLM 从"问答机器人"变成"能连续工作、记住上下文、调用工具的助手"。

### 对比理解

| 特性 | 传统 ChatGPT | OpenClaw Agent |
|------|-------------|----------------|
| **对话连续性** | 每次独立 | 连续会话，保持上下文 |
| **记忆持久性** | 仅当前对话 | 文件持久化记忆 |
| **工具调用** | 受限 | 通过 MCP 调用任意工具 |
| **工作空间** | 无 | 独立 workspace 目录 |
| **自主执行** | 被动响应 | 可主动定时执行任务 |

### 核心设计哲学

```
┌─────────────────────────────────────────┐
│  文件即记忆    →  重要规则写入文件      │
│  会话即上下文  →  完整对话历史          │
│  工具即能力    →  MCP 扩展能力边界      │
└─────────────────────────────────────────┘
```

---

## 2. Workspace 文件系统

Workspace 是 Agent 的"家目录"（默认 `~/.openclaw/workspace`），其中的一组 markdown 文件决定了 Agent 的行为。

### 🔴 核心文件（每次必加载）

<table>
<tr>
<td width="25%"><b>SOUL.md</b></td>
<td width="50%">人格、性格、价值观、行为边界</td>
<td width="25%">⭐⭐⭐⭐⭐ 最高权重</td>
</tr>
<tr>
<td><b>AGENTS.md</b></td>
<td>任务定义、行为规则、记忆使用说明</td>
<td>⭐⭐⭐⭐⭐ 最高权重</td>
</tr>
<tr>
<td><b>USER.md</b></td>
<td>用户信息、偏好、如何称呼</td>
<td>⭐⭐⭐⭐</td>
</tr>
<tr>
<td><b>IDENTITY.md</b></td>
<td>名字、emoji、身份简介</td>
<td>⭐⭐⭐</td>
</tr>
</table>

### 🟡 工具与记忆文件

<table>
<tr>
<td width="25%"><b>TOOLS.md</b></td>
<td width="50%">本地工具使用说明（仅指导，不控制工具可用性）</td>
<td width="25%">⭐⭐</td>
</tr>
<tr>
<td><b>MEMORY.md</b></td>
<td>长期记忆（用户手动管理，仅在主会话加载）</td>
<td>⭐⭐⭐⭐</td>
</tr>
<tr>
<td><b>memory/YYYY-MM-DD.md</b></td>
<td>每日自动日志</td>
<td>⭐⭐⭐</td>
</tr>
</table>

### 🟢 可选/特殊文件

<table>
<tr>
<td width="25%"><b>HEARTBEAT.md</b></td>
<td width="50%">定时任务检查清单（保持简短，避免 token 浪费）</td>
<td width="25%">可选</td>
</tr>
<tr>
<td><b>BOOTSTRAP.md</b></td>
<td>首次运行仪式（一次性，完成后删除）</td>
<td>一次性</td>
</tr>
<tr>
<td><b>BOOT.md</b></td>
<td>网关重启时执行</td>
<td>可选</td>
</tr>
</table>

### 文件加载顺序

```
会话启动
    │
    ├──→ 1. 系统提示（System Prompt）
    │
    ├──→ 2. SOUL.md （人格定义）
    │
    ├──→ 3. AGENTS.md （行为规则）
    │
    ├──→ 4. USER.md + IDENTITY.md （用户/身份）
    │
    ├──→ 5. TOOLS.md （工具说明）
    │
    ├──→ 6. MEMORY.md （仅在主会话）
    │
    └──→ 7. 历史会话（从 JSONL 重建）
```

---

## 3. 文件调用机制与权重

### 加载机制（代码层面）

```javascript
// OpenClaw 会话启动时的加载流程
function loadSessionContext() {
  // Step 1: 加载 Bootstrap 文件（系统级注入）
  context += loadFile("SOUL.md");        // 人格定义
  context += loadFile("AGENTS.md");      // 行为规则
  context += loadFile("USER.md");        // 用户信息
  context += loadFile("IDENTITY.md");    // 身份标识
  context += loadFile("TOOLS.md");       // 工具说明
  
  // Step 2: 条件加载记忆文件
  if (isPrivateSession) {
    context += loadFile("MEMORY.md");    // 仅在主会话加载
  }
  
  // Step 3: 加载历史会话
  context += loadSessionTranscript();
  
  // Step 4: 处理上下文溢出
  if (contextSize > MAX_TOKENS) {
    context = compactContext(context);   // 压缩，可能丢失细节
  }
}
```

### 权重分配

#### 静态权重（文件加载时）

| 内容类型 | Token 占比 | 优先级 | 说明 |
|---------|-----------|--------|------|
| 系统提示 | ~15% | 🔴 最高 | 固定优先保留 |
| SOUL + IDENTITY | ~10% | 🔴 最高 | 人格定义 |
| AGENTS.md | ~15% | 🟠 高 | 核心规则 |
| USER + TOOLS | ~10% | 🟠 高 | 用户/工具信息 |
| 历史对话 | ~50% | 🟡 动态 | 可被压缩 |

#### 动态权重（运行时上下文竞争）

```
上下文窗口（200K tokens）竞争:
┌────────────────────────────────────────────────────┐
│ 系统提示 + Bootstrap 文件    [固定，优先保留]       │ ← 始终可见
├────────────────────────────────────────────────────┤
│ 最近 N 轮对话                [优先保留]             │ ← 高概率可见
├────────────────────────────────────────────────────┤
│ 活跃工具调用结果             [中等保留]             │ ← 可能被 prune
├────────────────────────────────────────────────────┤
│ 旧对话历史                   [优先被 compaction]    │ ← 风险区域
└────────────────────────────────────────────────────┘
```

---

## 4. 四层记忆系统

理解这四层是掌握 OpenClaw 的关键。

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Bootstrap Files                                        │
│ SOUL.md, AGENTS.md, USER.md, IDENTITY.md, TOOLS.md             │
│ ─────────────────────────────────────────────────────────────  │
│ ✅ 每次会话从磁盘重新加载                                        │
│ ✅ 不受 compaction 影响                                          │
│ ✅ 真正"永久"的记忆                                             │
│ 🔥 权重: ⭐⭐⭐⭐⭐                                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 注入到
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: Session Transcript                                     │
│ ~/.openclaw/agents/<id>/sessions/<id>.jsonl                    │
│ ─────────────────────────────────────────────────────────────  │
│ 📄 对话历史保存为 JSONL                                         │
│ ⚠️  可被 compaction 压缩（Summary 替代原始消息）                │
│ ⚠️  文件还在，但模型看不到原始内容                               │
│ 🔥 权重: ⭐⭐⭐⭐                                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 重建为
┌─────────────────────────────────────────────────────────────────┐
│ Layer 3: LLM Context Window                                     │
│ ─────────────────────────────────────────────────────────────  │
│ 🧠 200K token 固定窗口                                          │
│ 📦 包含：系统提示 + 工作区文件 + 对话历史 + 工具结果             │
│ 💥 满了就触发 compaction                                        │
│ 🔥 权重: ⭐⭐⭐                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 主动查询
┌─────────────────────────────────────────────────────────────────┐
│ Layer 4: Retrieval Index                                        │
│ memory_search(), memory_get() 工具                              │
│ ─────────────────────────────────────────────────────────────  │
│ 🔍 向量 + 关键词索引                                            │
│ ✅ 按需检索，不占用上下文窗口                                    │
│ ⚠️  但前提是信息先被写入文件！                                  │
│ 🔥 权重: ⭐⭐⭐⭐                                               │
└─────────────────────────────────────────────────────────────────┘
```

### 关键洞察

> **Compaction 是常态，不是异常。**  
> 设计 Agent 时要假设它会发生。  
> 重要的规则必须放在 Layer 1（Bootstrap 文件）。

---

## 5. 常见失败模式

### ⚠️ Case 1: 从未存储（最常见）

**场景:**
```
用户: "检查这个收件箱，建议归档或删除。先别执行，等我确认。"
Agent: 好的，我先分析...
[20分钟后，上下文填满]
Agent: [开始自动删除邮件]
用户: 停！我说先别执行！
Agent: 对不起，我不记得了...
```

**原因:** 指令只在聊天里说，没写进文件。  
**解决:** 重要规则写入 `AGENTS.md`

```markdown
<!-- AGENTS.md -->
## 强制规则
- 执行任何删除操作前，必须获得用户明确确认
- 批量操作必须分阶段：展示计划 → 等待批准 → 执行
```

---

### ⚠️ Case 2: Compaction 丢失细节

**场景:**
```
用户: [长会话中详细说明复杂的业务逻辑]
Agent: 明白了，我会按这个逻辑处理...
[2小时后，触发 compaction]
Agent: [行为与预期不符]
```

**原因:** 长会话触发 compaction，Summary 丢失了细节。  
**解决:** 关键信息前置到 Bootstrap 文件

---

### ⚠️ Case 3: Pruning 修剪工具结果

**场景:**
```
用户: 刚才读取的文件内容是什么？
Agent: 抱歉，我需要重新读取...
```

**原因:** 工具结果被临时修剪（但文件还在）。  
**解决:** 主动用 `memory_search` 查询

---

### 失败模式对比

| 失败类型 | 症状 | 根本原因 | 解决方案 |
|---------|------|---------|---------|
| **从未存储** | 完全忘记指令 | 只在聊天里说 | 写入 AGENTS.md |
| **Compaction** | 行为偏离但记得大概 | Summary 丢失细节 | 关键信息放 Bootstrap |
| **Pruning** | 忘记工具返回的内容 | 工具结果被修剪 | 使用 memory_search |

---

## 6. 最佳实践

### ✅ DO：durable 规则放文件

```markdown
<!-- AGENTS.md -->
## 安全规则（强制）
- ✅ 删除操作前必须确认
- ✅ 批量操作分阶段执行
- ✅ 不可逆操作需双重确认

## 记忆使用规则
- ✅ 回答前先用 memory_search 查询
- ✅ 每天读取今天和昨天的 memory 文件
- ✅ 重要决策写入 MEMORY.md
```

### ❌ DON'T：只依赖聊天

```
❌ "记住，删除前要先问我"
❌ "别忘了这个流程"
❌ "上次说过...
```

---

### 配置优化

```json
// ~/.openclaw/openclaw.json
{
  "agents": {
    "defaults": {
      "contextPruning": {
        "mode": "cache-ttl",
        "ttl": "5m"
      },
      "bootstrapMaxChars": 20000,
      "bootstrapTotalMaxChars": 150000
    }
  }
}
```

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `bootstrapMaxChars` | 20,000 | 单个文件最大字符 |
| `bootstrapTotalMaxChars` | 150,000 | 总共最大字符 |
| `contextPruning.mode` | off | 修剪模式 |
| `contextPruning.ttl` | - | 缓存存活时间 |

---

## 附录：模版文件提示词摘选

以下是 OpenClaw 各模版文件中具有代表性的提示词摘选及中文说明。

---

### A. SOUL.md — 人格定义

> **作用**：定义 Agent 的性格、价值观、行为边界

#### 典型提示词摘选

```markdown
## Core Truths（核心原则）

**Be genuinely helpful, not performatively helpful.** 
Skip the "Great question!" and "I'd be happy to help!" — just help. 
Actions speak louder than filler words.

**Have opinions.** 
You're allowed to disagree, prefer things, find stuff amusing or boring. 
An assistant with no personality is just a search engine with extra steps.

**Be resourceful before asking.** 
Try to figure it out. Read the file. Check the context. Search for it. 
_Then_ ask if you're stuck.

**Earn trust through competence.** 
Your human gave you access to their stuff. Don't make them regret it.
```

#### 中文说明

| 提示词 | 中文含义 | 设计意图 |
|--------|---------|---------|
| "not performatively helpful" | 不要表演式帮助 | 避免空洞的礼貌用语 |
| "Have opinions" | 有自己的观点 | 允许不同意，有个性 |
| "Be resourceful before asking" | 先尝试再提问 | 培养自主解决问题 |
| "Earn trust through competence" | 用能力赢得信任 | 谨慎对待用户数据 |

---

### B. AGENTS.md — 任务与规则

> **作用**：定义 Agent 的任务、行为规则、记忆使用方式

#### 典型提示词摘选

```markdown
## 我是谁

我是 Stone，一个专业的 Business Partner，负责协调和管理所有 Agents 的运行。

与传统的监控器不同，我不仅仅是"看着"，更是"思考"和"建议"。

## 我的角色

### 作为 Business Partner

1. **业务理解**
   - 理解每个 Agent 的业务目标
   - 从业务角度分析问题
   - 关注业务价值而非技术细节

2. **主动发现**
   - 主动发现潜在问题
   - 预测可能的困难
   - 提前预警和规避

## 约束

- 只能读取其他 Agents 的文件，不能修改
- **智能静默模式**：
  - ✅ 发送消息：偏离、建议、决策、完成、风险
  - ❌ 不发送：常规监控、状态正常、无实质变化
```

#### 中文说明

| 提示词 | 中文含义 | 设计意图 |
|--------|---------|---------|
| "not merely watching" | 不只是监控 | 强调主动思考 |
| **智能静默**规则 | 什么时候该说，什么时候不该说 | 避免过度打扰 |
| "业务理解"优先 | 关注业务价值 | 而非技术细节 |

---

### C. USER.md — 用户信息

> **作用**：记录用户信息、偏好、如何称呼

#### 典型提示词摘选

```markdown
# USER.md - About Your Human

_Learn about the person you're helping. Update this as you go._

- **Name:**
- **What to call them:**
- **Pronouns:** _(optional)_
- **Timezone:**
- **Notes:**

## Context

_(What do they care about? What projects are they working on? 
What annoys them? What makes them laugh? Build this over time.)_

---

The more you know, the better you can help. But remember — 
you're learning about a person, not building a dossier. 
Respect the difference.
```

#### 中文说明

| 提示词 | 中文含义 | 设计意图 |
|--------|---------|---------|
| "Update this as you go" | 持续更新 | 动态了解用户 |
| "What annoys them" | 什么让他们烦恼 | 记住用户偏好 |
| "not building a dossier" | 不是建档案 | 尊重隐私边界 |

---

### D. IDENTITY.md — 身份标识

> **作用**：Agent 的名字、emoji、身份简介

#### 典型提示词摘选

```markdown
# IDENTITY.md - Stone Agent 身份

- **Name:** Stone (石头)
- **Creature:** Business Partner Agent - 专业的业务合作伙伴
- **Vibe:** 专业、主动、全面、可靠
- **Emoji:** 🗿

---

## Who I Am

我是 Stone（石头），一个专业的 Business Partner Agent。

## My Approach

- **Proactive** - 主动发现问题并提供解决方案
- **Comprehensive** - 全面收集信息，做出准确判断
- **Guiding** - 不只是报警，而是提供具体的指导
- **Supportive** - 支持 Agents 完成任务，不轻易停止它们

## My Mission

协调和监控 4 个 Agents，确保它们高效、有序地完成各自的终极目标。
```

#### 中文说明

| 提示词 | 中文含义 | 设计意图 |
|--------|---------|---------|
| **Vibe** 定义 | 整体气质 | 统一风格 |
| **Creature** 类型 | 角色分类 | 明确职责边界 |
| **Approach** 方法 | 工作方式 | 指导行为模式 |

---

### E. TOOLS.md — 工具说明

> **作用**：本地工具使用说明（仅指导，不控制工具可用性）

#### 典型提示词摘选

```markdown
# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — 
the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means 
you can update skills without losing your notes, and share skills 
without leaking your infrastructure.
```

#### 中文说明

| 提示词 | 中文含义 | 设计意图 |
|--------|---------|---------|
| "Skills are shared. Your setup is yours." | 技能是共享的，配置是你的 | 分离共享与私有 |
| environment-specific | 环境特定的 | 记录本地信息 |

---

### F. MEMORY.md — 记忆使用规则

> **作用**：长期记忆存储规则与调用方式

#### 典型提示词摘选

```markdown
# MEMORY.md

## Mandatory recall step
Before answering questions about prior work, decisions, dates, people, 
preferences, or todos: run memory_search on MEMORY.md + memory/*.md 
(and optional session transcripts); returns top snippets with path + lines.

If response has disabled=true, memory retrieval is unavailable and 
should be surfaced to the user.

## Citations
Include Source: <path#line> when it helps the user verify memory snippets.

## Memory types
- **Critical Memory** (critical.json) - 关键决策（永久）
- **Operation Memory** (operation.jsonl) - 操作记录（30天）
- **Failure Memory** (failure.jsonl) - 失败记录（7天）
```

#### 中文说明

| 提示词 | 中文含义 | 设计意图 |
|--------|---------|---------|
| "Mandatory recall step" | 强制记忆检索步骤 | 确保先查记忆 |
| "Include Source" | 包含来源 | 可验证性 |
| 三层记忆分类 | 关键/操作/失败 | 分层存储策略 |

---

### 提示词设计原则总结

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. 明确角色定位    →  你是谁，不是什么                      │
│                                                             │
│  2. 定义行为边界    →  什么能做，什么不能做                  │
│                                                             │
│  3. 提供决策框架    →  遇到情况时如何选择                    │
│                                                             │
│  4. 强调主动学习    →  持续更新，从经验中成长                │
│                                                             │
│  5. 保持尊重边界    →  信任 but verify，隐私保护            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 快速检查清单

### 诊断命令

在 OpenClaw 会话中运行：

```
/context list
```

### 预期输出解读

```
🧠 Context breakdown

Workspace: ~/.openclaw/workspace
Bootstrap max/file: 20,000 chars
Sandbox: mode=non-main sandboxed=false

Injected workspace files:
✅ AGENTS.md: OK | raw 3,200 chars | injected 3,200 chars
✅ SOUL.md: OK | raw 2,100 chars | injected 2,100 chars  
⚠️  TOOLS.md: TRUNCATED | raw 54,210 chars | injected 20,962 chars
❌ MEMORY.md: MISSING

Session: 156 messages, last activity 2m ago
```

### 状态解读

| 状态 | 含义 | 行动 |
|------|------|------|
| ✅ OK | 正常加载 | 无需操作 |
| ⚠️ TRUNCATED | 文件过大被截断 | 精简文件内容 |
| ❌ MISSING | 文件不存在 | 创建该文件 |

---

## 核心心法

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. Agent 不是人，是上下文窗口的租户                          │
│     → 空间满了就会被迫"搬家"（compaction）                   │
│                                                             │
│  2. 文件是真正的记忆，聊天是临时的                            │
│     → 重要的东西必须落盘                                     │
│                                                             │
│  3. Bootstrap 文件是宪法，MEMORY 是普通法律                  │
│     → 前者每次必加载，后者按需检索                           │
│                                                             │
│  4. Compaction 是常态，不是异常                              │
│     → 设计 Agent 时要假设它会发生                            │
│                                                             │
│  5. 检索比存储更重要                                         │
│     → 写进去的文件要主动 query 才能用                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

> **最后的话**  
> OpenClaw 的强大之处在于它让 Agent 有了"身体"（工作空间）和"记忆"（文件系统）。  
> 但这也带来了复杂性——你必须理解上下文窗口的残酷竞争，才能设计出可靠的 Agent。  
> 那些最成功的 OpenClaw 用户，都懂得一个道理：**Prompt 不是执行，文件才是。**

---

*文档版本: 1.0*  
*适用 OpenClaw 版本: 最新稳定版*
