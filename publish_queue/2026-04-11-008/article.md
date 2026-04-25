# 你的 AI 是怎么记住你的？我扒了两个顶级产品的底层代码

> 一个靠"反思"，一个靠"算法"。

你有没有发现，跟 AI 聊久了，它好像越来越"懂你"？

你上周随口提的偏好，今天它还记得；你三个月前写过的一个项目细节，它居然能翻出来当参考。

更别提那种"恍若隔世"的体验——隔了半个月再打开 Claude，它开口就是"上次你说的那个方案，后来进展怎么样了？"

我常常被这种"记忆幻觉"骗到。但实际上，AI 没有记忆。至少不是人类意义上的记忆。

它之所以"记得"你，是因为背后有一整套精密的工程机制，在不停地收集、整理、筛选、归档。你的一对一对话，只不过是冰山露出水面的那一小角。

上个月，Claude Code 的完整源码通过 npm 的一个 sourcemap 意外泄露了。46 万行代码被摊在阳光下，其中就包括 Anthropic 是怎么设计"AI 记忆"的。

我花了一周时间，把 Claude Code 的记忆系统代码读了一遍，又顺手翻遍了 OpenClaw 的 memory-core 插件源码。

结果发现了一个非常有趣的分野：

**同样是让 AI"记住"用户，两家走了两条完全不同的路。**

一个是"反思派"：让 AI 自己当清道夫，靠理解和判断来整理记忆。

一个是"算法派"：把每一次搜索都量化成数据，靠分数和阈值来决定什么该留下。

这篇文章，就是把这两条路线完整地拆给你看。

---

## 01 先说结论：记忆没有魔法，全是工程

在展开之前，我必须先破除一个迷思：

**任何声称"AI 有记忆"的说法，都是修辞。**

大语言模型本质上是"无状态"的。你每次发消息，它都是一次性处理完你给的上下文，然后给出回复。模型本身并不"保存"你们的聊天历史。

所以所谓的"记忆"，全都是**外挂系统**——有人在模型外面搭了一套书架，把对话里的重要信息挑出来，写成文本文件，等下次聊天时再塞回模型的 prompt 里。

Claude Code 和 OpenClaw 都信奉同一个底层原则：

> **所有能被记住的东西，都必须显式地写在磁盘上。没有隐藏状态。**

但接下来就是分歧点了：

**谁来写？什么时候写？谁来决定什么值得记住？**

Claude Code 的答案是：**让 LLM 自己写、自己整理。**

OpenClaw 的答案是：**让工具自动追踪，让算法来晋升。**

---

## 02 Claude Code 的路线：主代理写，子代理整理

Anthropic 是怎么做的？

### 记忆写进去：每轮对话结束后自动触发

Claude Code 有一个叫 `extractMemories` 的后台钩子。每次你一轮对话结束（模型给出最终回复、不再调用工具）时，它就会悄悄启动。

注意，这里不是主代理自己去写，而是**fork 出一个子代理**。

这个子代理非常有讲究：它是主对话的"完美副本"，能共享父对话的 prompt cache，所以运行成本极低。但它的权限被严格限制死了：

- 只能读（`Read`、`Grep`、`Glob`）
- Bash 只能运行只读命令（`ls`、`cat`、`grep` 这些）
- `Edit` / `Write` **只能在 auto-memory 目录内部操作**

如果这一轮主代理自己已经动手写了记忆文件，后台 fork 就自动跳过，不会重复劳动。

这种"互斥"设计很聪明：主代理和后台代理，永远只有一个在干活。

**预注入 manifest** 是它的另一个提速技巧。子代理启动前，系统会先把现有记忆文件扫描一遍，生成目录清单直接塞进 prompt。这样它就不用先花一轮去 `ls` 了。

### 记忆整理：AutoDream，一个四阶段的"反思"流程

写进去只是第一步。过段时间记忆会变多、变乱，这时候就需要整理了。

Claude Code 的整理机制叫 `autoDream`，触发条件有三道闸门：

1. **时间闸**：距离上次整理超过 24 小时
2. **会话闸**：这段时间内新增了至少 5 个会话
3. **锁闸**：当前没有别的进程在整理

一旦触发，它同样 fork 出一个子代理，但 prompt 变成了一个完整的四阶段指令：

**Phase 1 - Orient（定位）**

子代理先 `ls` 记忆目录，读 `MEMORY.md`，再快速浏览已有的 topic 文件，了解当前记忆的"地形"。

**Phase 2 - Gather（收集信号）**

读 daily logs，检索最近Session的 transcript。如果某个信息需要特定上下文（比如"上周构建失败的错误信息是什么"），就用 `grep` 去 JSONL 会话记录里找。

**Phase 3 - Consolidate（整合）**

把新信息合并进现有的 topic 文件，避免创建重复文件。把"昨天"、"上周"这样的相对时间转成绝对日期。如果发现旧记忆被证伪了，直接删掉或修正。

**Phase 4 - Prune and Index（修剪索引）**

维护 `MEMORY.md`。删掉指向过时文件的指针，把超过 200 字符的冗长索引行拆回 topic 文件，添加新指针。

整个流程的核心是：**LLM 自己当图书管理员**。它不是按照一套死板的规则在跑，而是靠"理解"来决定哪些信息值得合并、哪些文件该删、哪些索引该加。

### 文件布局：MEMORY.md 是索引，不是正文

Claude Code 的记忆目录大概长这样：

```
~/.claude/projects/<项目名>/memory/
├── MEMORY.md              ← 索引（限制 200 行 / 25KB）
├── logs/YYYY/MM/...       ← 日常日志
└── <topic>.md             ← 主题记忆正文
```

`MEMORY.md` 是一个**超轻量的目录**。每一行都是类似这样的指针：

```
- [Title](file.md) — one-line hook
```

真正的内容分散在各个 topic 文件里。这样做的目的是：加载快，不做大文件注入。

---

## 03 OpenClaw 的路线：工具追踪 + 算法晋升

现在看 OpenClaw 是怎么做的。

### 记忆写进去：没有后台 fork，但有"自动追踪"

OpenClaw 不提供自动 fork 子代理来帮你写记忆。它给你的只有两个工具：

- `memory_search`：语义搜索 MEMORY.md 和 memory/*.md
- `memory_get`：按路径和行号安全读取片段

写记忆这件事，主要靠**主代理显式调用 Write/Edit 工具**，或者依赖 compaction 前的 **memory flush** 提醒——在上下文压缩前，OpenClaw 会静默插入一个提示，让 agent 把对话里还没写进文件的重要信息赶紧存下来。

但 OpenClaw 有一个非常特殊的机制：**每次你调用 `memory_search`，系统都会自动做 short-term recall tracking。**

什么意思？

只要你搜索了记忆，被 surface 出来的那些结果，就会被量化记录到一个 JSON 数据库（`short-term-recall.json`）里。记录的内容包括：

- query 本身
- 结果的路径、行号、snippet、分数
- 这个 snippet 被召回过多少次（recallCount）
- 有多少不同的 query 招出过它（queryHashes）
- 它分别在哪几天被招出过（recallDays）
- 自动提取的概念标签（conceptTags）

OpenClaw 不评判你的记忆"好不好"，但它会**忠实地记录你的记忆被怎样使用过**。

### 记忆整理：Dreaming，一套三阶段晋升流水线

OpenClaw 的 dreaming 是**可选功能，默认关闭**。一旦开启，系统会注册一个 cron job（默认每天凌晨 3 点），触发一轮完整的"梦境清扫"。

最关键的区别在于：

> **OpenClaw 的 dreaming，不是靠 LLM 反思来整理记忆，而是靠算法评分来决定谁能进长期记忆。**

它分为三个阶段：Light Sleep、REM Sleep、Deep Sleep。

#### Light Sleep：把日常记忆和会话 transcript"喂"进数据库

每天早上（或者说 cron 触发时），系统会做两件事：

1. **ingest daily memory**：读取 `memory/YYYY-MM-DD.md`，按标题+段落/列表 chunk 拆成 snippet，写入 short-term recall store。
2. **ingest session transcripts**：扫描各个 agent 的会话记录文件，提取新增消息，按天汇总到 `session-corpus/YYYY-MM-DD.txt`，同样记录 recall。

完成后，生成一个 `## Light Sleep` 的摘要区块，并给这批 entry 打上 light phase signal，后续 deep 评分会获得小幅 boost。

#### REM Sleep：做主题统计和"候选真理"提取

REM 阶段同样先 ingest 数据，然后做两件事：

1. **主题统计**：基于 conceptTags，计算哪些概念在最近记忆中反复出现，生成 reflection。
2. **候选真理提取**：从还没被 promoted 的 entries 里，按 confidence 公式筛选出高价值 snippet，标记为"possible lasting truths"。

结果写入 `## REM Sleep` 区块，并给通过筛选的 entry 打上 REM phase signal。

#### Deep Sleep：算法晋升到 MEMORY.md

这是真正决定"什么成为长期记忆"的阶段。

OpenClaw 会给每个候选 snippet 打一个**六维加权分**：

| 信号 | 权重 | 含义 |
|------|------|------|
| Frequency | 0.24 | 总信号次数 |
| Relevance | 0.30 | 平均 retrieval score |
| Diversity | 0.15 | 独立 query / 覆盖天数 |
| Recency | 0.15 | 半衰期衰减新鲜度（默认 14 天） |
| Consolidation | 0.10 | 多天复发的强度 |
| Conceptual | 0.06 | 概念标签丰富度 |

再加上 light/REM phase signal 的额外 boost（最高约 0.08）。

**晋升门槛非常刚硬：**

- `minScore >= 0.75`
- `minRecallCount >= 3`
- `minUniqueQueries >= 2`
- 可选的 `maxAgeDays` 限制

而且，在真正写入 `MEMORY.md` 前，系统会做一个 **rehydration**：重新从源文件读取 snippet 对应的位置。如果原文已经被删改或者找不到了，这个候选直接被丢弃，防止把过时的东西晋升上去。

通过筛选的候选会被 append 到 `MEMORY.md` 的一个 `## Promoted From Short-Term Memory` 区块里，并标记 `promotedAt`，下次不会再重复晋升。

### Dream Diary：给人看的，不是给机器用的

每个 phase 结束后，如果配置了 subagent，OpenClaw 还会调用一个子代理生成一段人类可读的"梦境日记"，写入 `DREAMS.md`。

但这只是装饰文本——它**不参与下一轮决策**。真正的决策权永远在 JSON store 和算法公式手里。

### 文件布局：MEMORY.md 是正文，直接注入

OpenClaw 的记忆目录长这样：

```
<workspace>/
├── MEMORY.md                              ← 长期记忆（直接注入 prompt）
├── memory/YYYY-MM-DD.md                   ← 日常笔记
├── DREAMS.md                              ← Dream Diary（给人读的）
└── memory/.dreams/
    ├── short-term-recall.json             ← 召回记录数据库
    ├── phase-signals.json                 ← light/REM 强化信号
    ├── daily-ingestion.json               ← 每日摄取状态
    ├── session-ingestion.json             ← 会话摄取状态
    ├── session-corpus/YYYY-MM-DD.txt      ← 提取的会话语料
    └── short-term-promotion.lock          ← 文件锁
```

`MEMORY.md` 的角色和 Claude Code **完全相反**：它是**正文本身**，每次 DM 会话开头都会被直接塞进 prompt。

---

## 04 两条路线的根本分野

读到这里，你应该已经能清晰地看到两条路线的不同了。

### Claude Code：LLM-as-Janitor

Anthropic 选择了一种非常"信仰 LLM"的方式：既然 LLM 能理解和生成，那整理记忆这件事也交给它来做。

整个系统的设计哲学是：

- **MEMORY.md 是索引**：轻量、快速加载，正文在 topic 文件里。
- **forked agent + cache sharing**：后台子代理运行成本低。
- **没有固定分数**：什么值得记住，完全靠 LLM 自己的判断。

这很优雅，也很"Anthropic"。但它有一个隐含的假设：**LLM 的整理能力足够好，足够稳定。**

### OpenClaw：Algorithm-as-Gatekeeper

OpenClaw 选择了一种非常工程化的方式：既然记忆的质量最终表现为"被搜索召回了多少次、被多少不同 query 验证过"，那干脆把这些行为全部量化，用阈值和公式来做决策。

它的设计哲学是：

- **MEMORY.md 是正文**：直接注入，不是索引。
- **量化驱动**：所有搜索行为都被记录成 JSON 数据。
- **LLM 只做 narrative，不做 janitor**：除了写 Dream Diary，核心流程全是确定性代码。
- **可审计、可解释**：你可以打开 `DREAMS.md` 和 phase reports，看到机器为什么做了这个决定。

这很理性，也很可控。但它也有一个隐含的假设：**使用频率和检索分数能很好地代理"重要性"。**

---

## 05 两条路线，谁更好？

这个问题没有标准答案。要看你的场景信任什么。

### 什么时候 Claude Code 的方式更好？

- 你的记忆内容**结构化程度高**，需要频繁合并、去重、修枝。
- 你信任 LLM 的**语义理解能力**，愿意让它自己当图书管理员。
- 你希望**减少工程复杂度**，不想维护 JSON store 和评分公式。
- 你的记忆量**不算太大**，LLM 整理一次的成本可接受。

### 什么时候 OpenClaw 的方式更好？

- 你的记忆内容**非常庞杂**，需要一套客观的筛子来防止 MEMORY.md 变成垃圾堆。
- 你更信任**可量化的规则**，希望对"什么能进长期记忆"有完全可控的阈值。
- 你需要**可审计的决策链路**，能向用户解释"为什么 AI 记住了这个"。
- 你的系统**多 agent、多 workspace**，需要跨会话的统一记忆调度。

---

## 06 这三条行动建议，你可以直接拿走

1. **如果你正在设计自己的 Agent 记忆系统**，先诚实回答一个问题：你更信任 LLM 的整理能力，还是更信任可量化的评分规则？这个问题会帮你快速选定架构方向。

2. **如果你用 OpenClaw 且发现 MEMORY.md 越来越冗长**，打开 dreaming（在配置里把 `dreaming.enabled` 设为 `true`），让算法帮你筛选高频高分的 snippet 自动晋升；同时养成定期看 `DREAMS.md` 的习惯，了解机器在关注什么主题。

3. **如果你参考 Claude Code 的 forked agent 模式做后台任务**，请务必做到两点：一是利用 shared cache 显著降低子代理运行成本；二是必须给子代理严格设定 `canUseTool` 沙箱，否则就是把完整文件系统权限交给了后台 LLM，风险极高。

---

## 写在最后

AI 记忆的战争，本质上是一场关于**控制权和信任**的战争。

你相信一个足够聪明的 LLM，能像一个贴心的私人助理一样，帮你把所有文件整理得井井有条吗？

还是你相信只有冰冷的数字、明确的阈值和可追踪的日志，才能在大规模运行时不出乱子？

Claude Code 和 OpenClaw，分别站到了这两个答案的极端。但它们达成了一件共识：

**再聪明的 AI，也得把记忆老老实实写在纸上。**

因为只有这样，你才有机会知道它到底在想什么。
