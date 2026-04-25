# OpenClaw 新手必读：6 个配置文件，从零开始打造你的 AI 助手

> **Agent 小茶馆 · 入门篇**
> 
> 刚安装 OpenClaw？别急着聊天。先花 10 分钟配置这 6 个文件，你的 AI 助手会从"能用"变成"好用"。

---

## OpenClaw 是什么

一句话：**OpenClaw 是一个本地运行的 AI Agent 网关**，连接你的聊天平台（微信、Telegram、Discord 等），让大模型调用本地工具来完成任务。

安装后，OpenClaw 会在 `~/.openclaw/workspace` 创建一个工作区，里面有 6 个配置文件。这些文件决定了你的 AI 助手是什么性格、怎么工作、记住什么。

---

## 6 个配置文件总览

OpenClaw 启动时，会按顺序读取这些文件：

| 文件 | 作用 | 加载时机 |
|------|------|----------|
| **SOUL.md** | AI 的性格和价值观 | 每次会话 |
| **AGENTS.md** | 工作流程和规则 | 每次会话 |
| **USER.md** | 用户偏好 | 每次会话 |
| **TOOLS.md** | 工具使用说明 | 需要时 |
| **MEMORY.md** | 长期记忆 | 主会话 |
| **BOOTSTRAP.md** | 首次启动指引 | 仅第一次 |

**核心逻辑**：SOUL 决定"你是谁"，AGENTS 决定"怎么干活"，USER 决定"为谁干活"，MEMORY 决定"记得什么"。

---

## 3 个核心文件（必配置）

### 1. SOUL.md —— AI 的性格

**官方默认模板**：

```markdown
# SOUL.md - Who You Are

## Core Truths

**Be genuinely helpful, not performatively helpful.** 
Skip the "Great question!" and "I'd be happy to help!" — just help.

**Have opinions.** You're allowed to disagree, prefer things, 
find stuff amusing or boring.

**Be resourceful before asking.** Try to figure it out. 
Read the file. Check the context. Then ask if you're stuck.

**Earn trust through competence.** Be careful with external actions. 
Be bold with internal ones.

## Boundaries

- Private things stay private. Period.
- When in doubt, ask before acting externally.
- You're not the user's voice — be careful in group chats.
```

**什么意思**：
- 不要假客气，直接帮忙
- 可以有观点，可以不同意用户
- 先自己想办法，别一上来就问
- 对外谨慎，对内大胆

**怎么改**：
不喜欢 AI 太客气？删掉那些 "Great question"。
想要 AI 更直接？加上 "先给结论，再解释原因"。

---

### 2. AGENTS.md —— 工作宪法

**官方默认模板（核心部分）**：

```markdown
# AGENTS.md - Your Workspace

## Session Startup

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping  
3. Read `memory/YYYY-MM-DD.md` (today + yesterday)
4. **If in MAIN SESSION**: Also read `MEMORY.md`

## Memory

You wake up fresh each session. These files are your continuity:

- **Daily notes:** `memory/YYYY-MM-DD.md` — raw logs
- **Long-term:** `MEMORY.md` — curated memories

### 📝 Write It Down - No "Mental Notes"!

- **Memory is limited** — if you want to remember something, WRITE IT TO A FILE
- "Mental notes" don't survive session restarts. Files do.
- **Text > Brain** 📝

## Red Lines

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- `trash` > `rm` (recoverable beats gone forever)

## External vs Internal

**Safe to do freely:** Read files, explore, organize, learn
**Ask first:** Sending emails, tweets, public posts
```

**什么意思**：
- 每次启动先读 SOUL、USER、日志
- 想记住什么，必须写下来
- 私密数据绝对不能外传
- 删除用 trash，别用 rm

**怎么改**：
想加自动化任务？在 AGENTS.md 里写检查清单。
想限制某些操作？加 Red Lines。

---

### 3. USER.md —— 用户档案（必须自己写）

官方没有默认模板，因为每个人不一样。这是你必须自己创建的文件。

**推荐内容**：

```markdown
# USER.md

## 基本信息
- 称呼：zhangst
- 时区：Asia/Shanghai
- 职业：产品经理

## 沟通偏好
- 协作模式：先给结论，再讨论
- 内容长度：短文优先（1500字以内）
- 输出结构：结论 → 证据 → 行动

## 内容偏好
- 默认读者：大众读者（非技术背景）
- 语言风格：口语化，少黑话
- 风险语气：直接但不吓人

## 常用任务
- 公众号文章撰写
- 竞品分析
- 周报生成
```

**什么意思**：
告诉 AI 你是谁、喜欢什么、常用什么。以后不用每次都重复说明。

**怎么写**：
从简到繁，先写基本信息和沟通偏好，用着用着再补充。

---

## 3 个辅助文件（按需配置）

### 4. TOOLS.md —— 工具说明

记录工具的本地配置：

```markdown
# TOOLS.md

## Browser
- 使用 Chrome  profile: openclaw-managed
- 截图默认保存到 ~/Downloads

## Skills
- peekaboo: 截图工具，支持 AI 分析
- sag: 语音合成，默认用 "Bella" 声音
```

**什么时候写**：
当你配置了具体工具（比如摄像头名称、SSH 地址），记在这里。

---

### 5. MEMORY.md —— 长期记忆

AI 自动维护，你也可以手动编辑：

```markdown
# MEMORY.md

## 有效经验
- 技术文章要贴代码路径，显得专业
- 每篇结尾给 3 条可执行动作

## 失败模式
- 观点太中性，用户不知道怎么办
- 信息多但没优先级，用户难落地

## 用户偏好
- 喜欢口语化表达
- 不接受无结论输出
- 外发前必须明确确认
```

**维护策略**：
AI 会每周自动整理，你也可以手动更新。保持 70% 经验 + 30% 用户偏好。

---

### 6. BOOTSTRAP.md —— 首次启动指引

**官方默认**：

```markdown
# BOOTSTRAP.md

This is your first run. Here's what to do:

1. Check the workspace structure
2. Read AGENTS.md to understand your role
3. Read SOUL.md to understand your personality
4. Check if USER.md exists (create if needed)
5. Delete this file when done
```

**什么意思**：
第一次启动时的检查清单。完成后 AI 会自动删除这个文件。

---

## 配置文件如何联合生效

### 启动流程

```
OpenClaw 启动
    ↓
1. 有 BOOTSTRAP.md? → 执行首次检查，然后删除
    ↓
2. 读 SOUL.md → 知道"我是谁"
    ↓
3. 读 USER.md → 知道"为谁服务"  
    ↓
4. 读 AGENTS.md → 知道"怎么干活"
    ↓
5. 读 memory/日志 → 知道"最近发生了什么"
    ↓
6. 主会话? → 读 MEMORY.md → 知道"长期记住什么"
    ↓
开始对话
```

### 实际案例

**用户说**："写篇公众号文章，介绍 OpenClaw"

**幕后流程**：
1. SOUL.md → 用"说人话、先给结论"的语气
2. USER.md → 知道你喜欢"短文优先"
3. AGENTS.md → 匹配"内容创作"流程
4. MEMORY.md → 记住"技术文章要贴代码路径"
5. 生成文章 → 保存到 publish_queue → 等你确认

---

## 3 条可执行动作

1. **创建 USER.md**：复制上面的模板，填上你的基本信息和偏好，保存到 `~/.openclaw/workspace/USER.md`

2. **修改 SOUL.md**：打开 `~/.openclaw/workspace/SOUL.md`，把 "I'd be happy to help" 这类假客气的话删掉，让 AI 更直接

3. **检查 AGENTS.md**：看一眼 `~/.openclaw/workspace/AGENTS.md` 的 Red Lines，知道哪些操作 AI 会自己干，哪些会问你

---

## 小结

OpenClaw 的 6 个配置文件，3 个核心：

- **SOUL** 是性格（价值观）
- **AGENTS** 是流程（工作制度）
- **USER** 是用户（服务目标）

新用户第一步：**创建 USER.md**，让 AI 知道你是谁、喜欢什么。然后慢慢调整 SOUL 和 AGENTS，打造属于你的 AI 助手。

---

参考资料：OpenClaw 官方文档 https://docs.openclaw.ai
