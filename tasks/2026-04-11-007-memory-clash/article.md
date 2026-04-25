# OpenClaw 与 Claude Code 的记忆机制对比：从源码看两种「Agent 长记性」的思路

> **一句话结论**：Claude Code 的记忆是**主代理自己写、子代理来整理**，追求简洁和自洽；OpenClaw 的记忆是**工具化搜索+插件化引擎**，追求可扩展和可审查。两者都把「没有隐藏状态」写进了设计基因里。

---

Agent 最让人上头也最让人抓狂的点，就是**记性**。上下文一满，前面聊的就跟没聊过一样。为了解决这个问题，Claude Code 和 OpenClaw 都选择把记忆**外化成文件**，而不是塞在模型上下文里硬撑。

但翻开源码你会发现，同样是「写 Markdown 文件」，两者的工程哲学差得挺远。今天这篇就从源码级别，把两边的记忆机制拆开对比一下。

---

## 一、文件结构：都是三层，但分工不同

### Claude Code：索引型架构
Claude Code 的记忆目录通常在 `~/.claude/projects/<项目>/memory/` 下，核心是一个**指针系统**：

- **`MEMORY.md`**：严格限制在 **~200 行 / 25KB** 以内。它不是内容仓库，而是一个**索引**（index），每行大概这样：
  ```markdown
  - [Title](file.md) — one-line hook
  ```
- **`logs/YYYY/MM/YYYY-MM-DD.md`**：每日追加的原始日志（append-only）。
- **Topic files**：实际的详细记忆内容，由 `MEMORY.md` 里的链接指向。

这个设计的精妙之处在于：**小索引保证每次启动都能快速加载，大内容按需读取。**

> 源码依据：`src/services/autoDream/consolidationPrompt.ts` 中明确提到 `MEMORY.md` 是 "an index, not a dump"，并设置了 `MAX_ENTRYPOINT_LINES` 限制。

### OpenClaw：时间线+长期记忆
OpenClaw 的记忆文件默认在 agent workspace（如 `~/.openclaw/workspace`）下：

- **`MEMORY.md`**：长期记忆本身。直接存 durable facts、preferences、decisions。**每次 DM 会话启动时自动注入系统提示词。**
- **`memory/YYYY-MM-DD.md`**：每日笔记。今天和昨天的文件会自动加载到上下文里。
- **`DREAMS.md`**（实验性）：人类可读的 Dream Diary，记录背景整合的摘要。

> 源码依据：`docs/concepts/memory.md` — "`MEMORY.md` — long-term memory... Loaded at the start of every DM session."

**对比**：Claude Code 的 `MEMORY.md` 是**目录索引**，内容分散在各 topic 文件；OpenClaw 的 `MEMORY.md` 是**正文本身**，直接参与每次会话。

---

## 二、记忆写入：谁在写？怎么写？

### Claude Code：双轨制（主代理写 + 后台子代理兜底）

Claude Code 有两套自动写入机制：

1. **`extractMemories`**（每次查询后触发）
   - 在主代理输出最终回答后，后台 fork 一个子代理。
   - 子代理读取本次会话的新消息，决定要不要写入记忆文件。
   - **互斥设计**：如果主代理在当轮已经自己动手写了记忆，后台提取就会跳过，避免重复。
   - 子代理最多跑 5 个 turn，不写入 transcript。

2. **`autoDream`**（周期性整合）
   - 触发条件：**距上次整合 >= 24 小时** 且 **>= 5 个新会话**。
   - 通过一个只读 forked agent 执行四阶段：Orient → Gather → Consolidate → Prune。
   - Bash 权限被锁死在只读（`ls`, `grep`, `cat` 等），只能写记忆目录里的文件。

> 源码依据：`src/services/extractMemories/extractMemories.ts` 的 `hasMemoryWritesSince` 互斥检查，以及 `src/services/autoDream/autoDream.ts` 的时间/会话门控。

### OpenClaw：Flush 提醒 + 用户/代理主动写

OpenClaw 没有一个持续跑的后台子代理去「自动摘录」会话。它的写入逻辑更**工具化**：

- **自动 flush**：在 compaction（上下文压缩）之前，OpenClaw 会静默提醒 agent：「该写记忆了」。把当前会话里还没落地的重要事实保存到文件。
- **用户随时说**：你只要说 "Remember that I prefer TypeScript"，agent 就会自己写到 `MEMORY.md` 或当天日志里。
- **Dreaming（可选）**：需要手动开启。后台通过 cron 调度，按 Light → Deep → REM 三阶段把短期信号晋升为长期记忆。

> 源码依据：`docs/concepts/memory.md` 的 "Automatic memory flush" 与 `docs/concepts/dreaming` 的 "opt-in and disabled by default"。

**对比**：Claude Code 是**代理主动帮我记**，OpenClaw 是**提醒我该记了+我自己开口记**。一个偏自动化，一个偏显式控制。

---

## 三、搜索/召回：grep vs 向量语义

这是差异最大的一点。

### Claude Code：grep-only（有限搜索）

根据泄露源码的分析（以及 `consolidationPrompt.ts` 中的提示），Claude Code 的 Dream 子代理在查找信息时，主要依赖：

- `ls` / `cat` 直接浏览记忆目录
- `grep -rn "<term>"` 在 JSONL  transcripts 中做关键词搜索

多篇技术分析指出 Claude Code 的搜索是 **"grep-only"**，没有启用向量语义检索。

> 参考：`src/services/autoDream/consolidationPrompt.ts` 中教导子代理 "grep the JSONL transcripts for narrow terms"。

### OpenClaw：Hybrid Search（向量 + 关键词）

OpenClaw 的 `memory_search` 是**一等工具**。默认引擎基于 **SQLite + sqlite-vec**，同时做了：

- **向量相似性搜索**（语义匹配，换说法也能找到）
- **关键词匹配**（精确命中 ID、代码符号等）

只要配置了任意支持的 embedding provider（OpenAI / Gemini / Voyage / Mistral），搜索就会自动启用。还有可选的 QMD 后端支持 rerank 和查询扩展。

> 源码依据：`docs/concepts/memory.md` — "`memory_search` uses **hybrid search** -- combining vector similarity with keyword matching."

**对比**：Claude Code 靠**文件系统遍历+grep**找记忆，OpenClaw 靠**嵌入向量数据库**做语义召回。一个简单直接，一个工程更重、检索能力更强。

---

## 四、Dream/整合：一个用来「瘦身」，一个用来「晋升」

两边都有 Dream/Consolidation 概念，但设计目标不同。

### Claude Code 的 Dream：自愈合索引

Claude Code 的 autoDream 更像一个**文件系统整理器**：
- 合并重复 topic
- 把相对日期换成绝对日期
- 删除过时的记忆
- 保障 `MEMORY.md` 不超过 200 行

它的核心目标是 **self-healing memory** ——让记忆文件保持精简、一致、可快速加载。

### OpenClaw 的 Dreaming：带门槛的信号晋升

OpenClaw 的 dreaming 实验性功能（默认关闭）更像一个**信息筛选器**：

| 阶段 | 作用 |
|------|------|
| **Light** | 整理近期短期信号，去重，暂存 |
| **Deep** | 评分+门槛过滤，只有高分、多次被召回、查询来源多样的候选才会写入 `MEMORY.md` |
| **REM** | 提炼主题和反思，不写入长期记忆 |

Deep phase 有明确的 **minScore / minRecallCount / minUniqueQueries** 三个门槛。不及格的信号会被丢弃，保证 `MEMORY.md` 是**高信号密度**的。

> 源码依据：`docs/concepts/dreaming` 的 phase model 和 threshold gates 描述。

**对比**：Claude Code 的 Dream 解决的是**文件膨胀和一致性问题**；OpenClaw 的 Dreaming 解决的是**信号质量和晋升控制问题**。

---

## 五、安全与隔离：沙盒思维的差异

### Claude Code：子代理沙盒

在 `extractMemories.ts` 中，Claude Code 通过 `createAutoMemCanUseTool` 对 forked 子代理做了严格的工具权限限制：

- 允许：`FILE_READ`, `GREP`, `GLOB`
- 允许 Bash：但必须是 `isReadOnly` 命令
- 允许 `FILE_EDIT` / `FILE_WRITE`：**仅当路径在 auto-memory 目录内**

这就把「自动记笔记」的子代理锁在了一个**只读探索+限定写入**的笼子里。

### OpenClaw：没有持续的 forks，靠运行时注入

OpenClaw 没有一个常驻的记忆子代理在跑。记忆工具（`memory_search`, `memory_get`）由 `memory-core` 插件提供，直接在主循环里调用。因此它没有 Claude Code 那种 forked agent 的安全问题，但也意味着**记忆写入的权责完全在主代理自己身上**。

**对比**：Claude Code 用**子代理隔离**解决自动写入的安全问题；OpenClaw 用**不 fork**来回避这个问题，把写入交给用户和主代理显式控制。

---

## 六、扩展性：闭合系统 vs 插件生态

### Claude Code：内置、闭合
从源码看，Claude Code 的记忆系统是其内部 `memdir/` 模块的一部分， deeply coupled 在产品主逻辑里：
- `memdir/paths.ts` 管理路径解析
- `memdir/memdir.js` 管理入口点规则
- `services/autoDream/` 管理整合逻辑

用户能调的配置很有限（主要是 `.claude/settings.json` 里的 `autoMemoryEnabled` 和 `autoMemoryDirectory`）。

### OpenClaw：可插拔后端

OpenClaw 的记忆系统是**插件化**的：

- 默认：`memory-core` + 内置 SQLite 引擎
- 可选：`memory-qmd`（本地 sidecar，带 rerank）
- 可选：`memory-honcho`（AI-native 跨会话记忆）
- 可选：`memory-wiki`（结构化知识库层，支持矛盾追踪和 dashboard）

> 源码依据：`docs/concepts/memory.md` 的 Memory backends 卡片组。

**对比**：Claude Code 的记忆是**产品功能**，OpenClaw 的记忆是**平台能力**。

---

## 七、一句话怎么选？

| 场景 | 推荐 |
|------|------|
| 你是一个编码工具，每天跑几十轮会话，需要自动归档 | Claude Code 的自动 extract + Dream 更省心 |
| 你是一个多面手 Agent，跨频道、跨用户，需要高质量召回 | OpenClaw 的 hybrid search + 可选 wiki 层更稳健 |
| 你担心后台子代理乱写文件 | OpenClaw 的显式写入+可选 dreaming 更可控 |
| 你追求极简实现，不想依赖 embedding provider | Claude Code 的纯文件+grep 更轻量 |

---

## 三条可执行动作

1. **如果你用 OpenClaw，先把 embedding provider 配了** —— 这是 `memory_search` hybrid 模式生效的前提，也是它和 Claude Code grep 路线拉开差距的关键。推荐先塞一个 OpenAI 或 Gemini 的 API key。

2. **如果你自己写 agent 记忆系统，直接抄 Claude Code 的「索引+限制」模式** —— 把入口文件（如 `MEMORY.md`）限制在 200 行以内，内容拆到 topic 文件，用链接指向。这个招数对长会话启动速度提升非常明显。

3. **不要让后台子代理拥有无限制的写权限** —— Claude Code 的 `createAutoMemCanUseTool` 是个很好的参考：只读 Bash + 限定目录写入。任何做自动记忆归档的 agent，都应该有这个隔离意识。

---

## 参考源码/文档

- Claude Code 泄露源码：`/Volumes/zhangstExtern/openclaw/workspace/stone/claude-code-leaked/src/services/autoDream/autoDream.ts`
- Claude Code 泄露源码：`/Volumes/zhangstExtern/openclaw/workspace/stone/claude-code-leaked/src/services/extractMemories/extractMemories.ts`
- Claude Code 泄露源码：`/Volumes/zhangstExtern/openclaw/workspace/stone/claude-code-leaked/src/services/autoDream/consolidationPrompt.ts`
- OpenClaw 文档：`/Users/zhangst/work/code/moltbot/docs/concepts/memory.md`
- OpenClaw 文档：`https://docs.openclaw.ai/concepts/dreaming`
