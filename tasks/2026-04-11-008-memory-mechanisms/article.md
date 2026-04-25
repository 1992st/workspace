# 两条路线：Claude Code 与 OpenClaw 的记忆机制对比

> 任务号：`2026-04-11-008`

## 一句话结论

Claude Code 的记忆系统是让**主代理自己写、子代理来整理**，MEMORY.md 只是索引，核心靠的是 LLM 的反思能力；OpenClaw 的记忆系统是**工具化搜索 + 算法化晋升**，MEMORY.md 是直接注入的正文， dreaming 是一套用分数和阈值筛选的自动化流水线。

两者都把「没有隐藏状态，全写进磁盘」作为设计底线，但实现路径完全不同。

---

## 第一部分：Claude Code 的记忆机制

### 1. 文件布局

Claude Code 的自动记忆放在项目对应的目录下：

```
~/.claude/projects/<project>/memory/
├── MEMORY.md          ← 索引文件（限制 200 行 / 25KB）
├── logs/YYYY/MM/...   ← 日常日志（assistant 模式使用）
└── <topic>.md         ← 各主题记忆正文
```

`MEMORY.md` 的角色很明确：**它不是正文，而是目录**。每一行是一条超简短的指针，格式大概是 `- [Title](file.md) — one-line hook`。真正的内容分散在各个 topic 文件里。

### 2. 记忆怎么写进去：extractMemories

每次你一轮对话结束（模型给出最终回复、不再调用工具）时，Claude Code 会触发一个后台钩子 `extractMemories`。它的核心实现有几个特点：

**（1）forked agent 模式**

它不是主代理自己去写，而是 fork 出一个子代理（`runForkedAgent`）。这个子代理是主对话的「完美副本」，能共享父对话的 prompt cache，所以额外成本很低。

**（2）严格的工具沙箱**

子代理只能做这几件事：
- `Read`、`Grep`、`Glob`（只读）
- 只读的 `Bash`（`ls`、`cat`、`grep` 等）
- `Edit` / `Write` **仅限于 auto-memory 目录内部**

它想碰项目代码？门都没有。

**（3）互斥机制**

如果这一轮主代理自己已经动手写了记忆文件，后台 fork 就自动跳过这一段，不会重复劳动。主代理和后台代理是互斥的。

**（4）cursor 与 coalescing**

用 `lastMemoryMessageUuid` 做光标，确保下次只处理新消息。如果前一次的 extraction 还没跑完，新请求来了，它会 stash 起来，等当前跑完再补一个 trailing run。

**（5）预注入 manifest**

跑之前会先把现有记忆文件扫一遍（`scanMemoryFiles`），生成 manifest 直接塞进 prompt，省得子代理先花一轮去 `ls`。

### 3. 记忆怎么整理：autoDream

隔一段时间后，记忆会变多、变乱，Claude Code 就会触发 `autoDream`——一个后台的「反思整理」流程。

**触发条件（三道闸门）：**
1. **时间闸**：距离上次整理 >= 默认 24 小时
2. **会话闸**：这段时间内新增了 >= 默认 5 个会话
3. **锁闸**：当前没有别的进程在整理

**执行方式：**
同样用 forked agent，但 prompt 是一个四阶段指令：

| 阶段 | 动作 |
|------|------|
| Orient | `ls` 记忆目录，读 `MEMORY.md`，了解现状 |
| Gather | 读 daily logs，必要时 `grep` 会话 transcript 找特定上下文 |
| Consolidate | 把新信息合并进现有 topic 文件，或创建新文件；把相对时间转成绝对日期；删掉过时的矛盾信息 |
| Prune and Index | 维护 `MEMORY.md`：删旧指针、缩短过长的行、加新指针 |

**关键细节：**
- 工具限制更严：Bash 只能读，不能写。
- `sessionIds` 会排除当前会话，所以 dream 只整理**已经结束的对话**。
- 有 `DreamTask` UI 状态 tracking，用户可以在后台任务面板里看到进度，甚至可以 kill 掉。
- 如果失败了，会 rollback lock 的 mtime，让时间闸重新满足，下次再试。

### 4. Claude Code 的设计哲学

- **LLM-as-janitor**：整理记忆这件事， itself 交给 LLM 来做反思。
- **MEMORY.md 是索引**：轻量、快速加载，正文在 topic 文件里。
- **forked agent + cache sharing**：子代理运行成本低。

---

## 第二部分：OpenClaw 的记忆机制

### 1. 文件布局

OpenClaw 的记忆文件全部放在 agent workspace 里：

```
<workspace>/
├── MEMORY.md                              ← 长期记忆（直接注入每次会话）
├── memory/YYYY-MM-DD.md                   ← 日常笔记（今昨两天自动加载）
├── DREAMS.md                              ← Dream Diary（人类可读，可选）
└── memory/.dreams/
    ├── short-term-recall.json             ← 搜索召回记录的量化数据库
    ├── phase-signals.json                 ← light / REM 阶段的强化信号
    ├── daily-ingestion.json               ← 每日文件摄取状态
    ├── session-ingestion.json             ← 会话 transcript 摄取状态
    ├── session-corpus/YYYY-MM-DD.txt      ← 从会话里提取的语料
    └── short-term-promotion.lock          ← 文件锁
```

`MEMORY.md` 的角色和 Claude Code **完全相反**：它是**正文本身**，系统会在每次 DM 会话开头把它直接塞进 prompt。

### 2. 记忆怎么写进去：显式工具 + 自动 flush

OpenClaw 没有后台 fork agent 自动帮你写记忆。它提供两个工具：

- `memory_search`：语义搜索 MEMORY.md 和 memory/*.md
- `memory_get`：按路径和行号安全读取片段

但有个关键机制：**每次 `memory_search` 被调用时，系统会自动做 short-term recall tracking**。也就是说，你被 surface 出来的搜索结果，会被量化记录到 `short-term-recall.json` 里，包括：

- query 内容
- 结果的路径、行号、snippet、分数
- 召回次数（recallCount）
- 查询去重（queryHashes）
- 日期分布（recallDays）
- 概念标签（conceptTags）

**另一个入口是「memory flush」**：在 compaction（上下文压缩）之前，OpenClaw 会静默插入一个提醒，让 agent 把对话里还没写进文件的重要信息赶紧存下来。这是防止上下文丢失的保险闸。

### 3. 记忆怎么整理：Dreaming（三阶段流水线）

OpenClaw 的 dreaming 是**可选功能，默认关闭**。开启后，系统会注册一个 cron job（默认每天凌晨 3 点），触发一轮完整的记忆整理 sweep。

和传统理解不同，OpenClaw 的 dreaming **不是让 LLM 去反思和改写文件**，而是一套用**算法和数据结构**驱动的晋升流水线。它分三个阶段：

#### 阶段一：Light Sleep（摄取与Staging）

`runLightDreaming` 做两件事：
1. **ingest daily memory**：读取 `memory/YYYY-MM-DD.md`，按标题和列表/段落 chunk 拆成 snippet，写入 `short-term-recall.json`
2. **ingest session transcripts**：扫描各 agent 的会话记录文件，提取新消息，按天汇总到 `session-corpus/YYYY-MM-DD.txt`，同样记录 recall

然后它会生成一个 `## Light Sleep` 的 summary block（可写到 daily memory 文件或单独 report），并给这些 entry 打上 **light phase signal**，后续 deep 评分会获得小幅 boost。

#### 阶段二：REM Sleep（模式识别与反思）

`runRemDreaming` 同样先 ingest 数据，然后做两件事：
1. **主题统计**：基于 `conceptTags` 计算哪些概念在 recent memories 里反复出现，生成 reflection
2. **候选真理提取**：从还没被 promoted 的 entries 里，按 confidence 公式筛选出高价值 snippet，作为 "possible lasting truths"

结果写入 `## REM Sleep` block，并给对应 entry 打上 **REM phase signal**。

#### 阶段三：Deep Sleep（算法晋升到 MEMORY.md）

这是真正决定「什么成为长期记忆」的阶段，实现在 `short-term-promotion.ts` 里。

**评分公式（六维加权）：**

| 信号 | 权重 | 含义 |
|------|------|------|
| Frequency | 0.24 | 总信号次数（recall + daily） |
| Relevance | 0.30 | 平均 retrieval score |
| Diversity | 0.15 | 独立 query / 覆盖天数的多样性 |
| Recency | 0.15 | 按半衰期衰减的新鲜度（默认 14 天） |
| Consolidation | 0.10 | 多天复发的强度（recallDays 的跨度与间隔） |
| Conceptual | 0.06 | concept tag 的丰富度 |

再加上 light / REM phase signal 的额外 boost（最高约 0.08）。

**晋升门槛：**
- `minScore >= 0.75`
- `minRecallCount >= 3`
- `minUniqueQueries >= 2`
- `maxAgeDays` 限制

**rehydration 机制：**
在真正写进 `MEMORY.md` 之前，系统会重新从源文件读取 snippet 对应的位置，做** relocation**。如果原文已经被删改，这个候选就会被丢弃，确保不会把过时的东西晋升上去。

**写入方式：**
通过的候选被 append 到 `MEMORY.md` 的一个 `## Promoted From Short-Term Memory` 区块里，并标记 `promotedAt`，下次不会再重复晋升。

**Dream Diary：**
每个 phase 结束后，如果配置了 subagent，还会调用一个子代理生成一段人类可读的「梦境日记」，写入 `DREAMS.md`。但这纯属给人看的装饰文本，**不参与下一轮决策**。

### 4. OpenClaw 的设计哲学

- **MEMORY.md 是正文**：直接注入，不是索引。
- **量化驱动的晋升**：用 JSON store 记录所有搜索行为，靠算法评分决定谁能进长期记忆。
- **LLM 只做 narrative，不做 janitor**：除了可选的 Dream Diary 文案，整理记忆的核心流程全是确定性代码。
- **可审计、可解释**：`DREAMS.md`、separate reports、phase signals 都是为了让人类能 review 机器在想什么。

---

## 第三部分：核心差异对比

| 维度 | Claude Code | OpenClaw |
|------|-------------|----------|
| **MEMORY.md 角色** | 索引（目录） | 正文（直接注入 prompt） |
| **记忆触发方式** | 每轮结束后自动 fork 子代理提取 | `memory_search` 调用时自动追踪 recall + 用户/代理显式写入 |
| **整理触发方式** | `extractMemories`（每轮）+ `autoDream`（24h/5会话） | `memory flush`（compaction 前）+ dreaming cron（默认每天 3 点） |
| **整理决策者** | **LLM**（子代理按四阶段 prompt 整理） | **算法**（六维加权评分 + 阈值门控） |
| **工具限制** | fork 出的子代理受限（只读 Bash + 只能写 memory 目录） | 无后台 fork 自动写记忆；dreaming 是主进程代码操作 |
| ** transcript 处理** | `autoDream` 时 `grep` 会话 JSONL 找上下文 | `dreaming-phases` 程序化扫描会话文件，提取语料到 `session-corpus/` |
| **晋升/整理标准** | 没有固定分数，完全靠 LLM 判断什么值得留 | 有明确的量化评分和阈值（0.75/3/2） |
| ** human review ** | 较弱（只能在 memory 目录里看文件） | 较强（专门的 `DREAMS.md` 和 phase reports） |
| **默认开关** | `extractMemories` 默认开启；`autoDream` 通过 feature flag 控制 | `memory-core` 默认启用；`dreaming` 默认关闭 |
| **状态存储** | 纯 markdown，无额外机器状态文件 | `*.json` store（recall、signals、ingestion checkpoint） |

---

## 第四部分：源码引用

**Claude Code（泄露源码，本地备份）：**
- 自动提取记忆：`/Volumes/zhangstExtern/openclaw/workspace/stone/claude-code-leaked/src/services/extractMemories/extractMemories.ts`
- 自动 dreaming（整理）：`/Volumes/zhangstExtern/openclaw/workspace/stone/claude-code-leaked/src/services/autoDream/autoDream.ts`
- dreaming prompt：`/Volumes/zhangstExtern/openclaw/workspace/stone/claude-code-leaked/src/services/autoDream/consolidationPrompt.ts`
- 路径解析：`/Volumes/zhangstExtern/openclaw/workspace/stone/claude-code-leaked/src/memdir/paths.ts`

**OpenClaw（官方仓库）：**
- dreaming 控制器：`/Users/zhangst/work/code/moltbot/extensions/memory-core/src/dreaming.ts`
- 三阶段实现：`/Users/zhangst/work/code/moltbot/extensions/memory-core/src/dreaming-phases.ts`
- 算法晋升（deep）：`/Users/zhangst/work/code/moltbot/extensions/memory-core/src/short-term-promotion.ts`
- 工具定义（recall tracking）：`/Users/zhangst/work/code/moltbot/extensions/memory-core/src/tools.ts`
- phase report 写入：`/Users/zhangst/work/code/moltbot/extensions/memory-core/src/dreaming-markdown.ts`
- 官方文档：`/Users/zhangst/work/code/moltbot/docs/concepts/memory.md`、`/Users/zhangst/work/code/moltbot/docs/concepts/dreaming.md`

---

## 三条可执行动作

1. **如果你正在设计自己的 Agent 记忆系统**，先回答一个问题：你更信任 LLM 的整理能力，还是更信任可量化的评分规则？ Claude Code 适合前者，OpenClaw 适合后者。
2. **如果你用 OpenClaw 且发现 MEMORY.md 越来越冗长**，打开 dreaming（`dreaming.enabled: true`），让算法帮你筛选高频高分的 snippet 自动晋升；同时定期看 `DREAMS.md` 了解机器在关注什么主题。
3. **如果你参考 Claude Code 的 forked agent 模式做后台任务**，注意两点：一是 shared cache 能显著降低成本；二是必须给子代理严格设定 `canUseTool`，否则就是把完整文件系统权限交给了后台 LLM。
