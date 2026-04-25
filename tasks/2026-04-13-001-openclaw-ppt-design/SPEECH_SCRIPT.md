# OpenClaw 功能拆解 —— 演讲稿

> **演讲时长**: 约 20-25 分钟
> **结构**: 10 页 PPT + 现场演示 + 杂谈

---

## 【开场】（1 分钟）

大家下午好。今天分享一个我过去几个月深度使用的开源项目 —— OpenClaw。

不聊产品、不聊生态，纯粹聊它的技术架构：它是怎么把 LLM 从"无状态的聊天机器人"变成"有上下文的工程助手"的。

---

## 【Slide 1: Cover】（跳过，停留 5 秒）

标题页。

---

## 【Slide 2: Overview】（2 分钟）

**核心问题**：LLM 是无状态的。你问它"我是谁"，它不知道；你让它"继续刚才的工作"，它一脸茫然。

**OpenClaw 的解法**：在 LLM 前面搭一条能力链 —— Inject → Assemble → Extend → Persist。

简单说，就是给 LLM 配一个"秘书系统"：
- 秘书知道你是谁（Inject）
- 秘书会整理上下文（Assemble）
- 秘书能调用外部工具（Extend）
- 秘书会记住你们聊过什么（Persist）

---

## 【Slide 3: 五层数据流】（3 分钟）

看这张图。你的请求进入 OpenClaw，会经过 5 层处理：

1. **Gateway 层**：根据 agentId + sessionKey 路由到正确的会话
2. **Session 层**：加载 history.jsonl（你们之前的对话历史）
3. **Bootstrap 层**：读取一堆 .md 文件（AGENTS.md, SOUL.md, TOOLS.md...）
4. **System Prompt 层**：把所有内容拼成一个巨大的字符串
5. **Runtime 层**：发给 LLM

**关键洞察**：你输入的 10 个字，背后触发了 ~85K 字符的系统上下文注入。

---

## 【Slide 4: Prompt 总览】（3 分钟）

System Prompt 由三部分组成：

- **硬编码规则** (~35%)：Safety、Execution Bias、Cron、CLI 命令...
- **工作区上下文** (~40%)：AGENTS.md、SOUL.md、TOOLS.md、MEMORY.md —— 这是你自定义的部分
- **动态环境** (~25%)：当前工作目录、环境变量、工具状态

**类比**：就像你给新员工发一本《员工手册》+ 项目 Wiki + 当日待办。

---

## 【Slide 5: 注入与拼装】（3 分钟）

以一句「你是谁？」为例，看 OpenClaw 做了什么：

1. 检查是否完成 Bootstrap（`hasCompletedBootstrapTurn()`）
2. 如果是 compaction 后的请求，重新注入上下文
3. 按顺序拼装：硬编码 → 项目上下文 → 动态环境
4. 最终生成一个巨大的 Prompt 发给 LLM

**感受**：用户的 4 个字 → 系统的 ~85K 字符。这就是"工程化"的意义 —— 把复杂留给自己，把简单留给用户。

---

## 【Slide 6: Skills】（3 分钟）

Skills 是可插拔的能力包。

**工作流程**：
- 用户请求匹配 skill（关键词匹配）
- OpenClaw 必须读取 SKILL.md
- 严格执行里面的步骤

**以 device-build-debug 为例**：
1. SSH 登录远程服务器
2. 执行 make 编译
3. rsync 同步固件
4. adb 推送到设备并验证

**父子传递优化**：父 agent 的 skillsSnapshot 直接传给子 agent，跳过重复扫描。

---

## 【Slide 7: Memory】（3 分钟）

Memory 是可替换的记忆后端。

**架构**：
- 落盘 → 分块（chunk · hash）→ 向量检索
- 支持内置向量索引和 qmd 外部后端

**关键 API**：`registerMemoryCapability()` —— 让不同的 Memory Provider 可以插拔。

**设计哲学**：记忆是 Agent 的"大脑"，但不应该绑定到具体实现。你可以用文件、用向量数据库、用任何你想要的存储。

---

## 【Slide 8: 效率与主动性】（2 分钟）

框架在后台默默做的三件事：

1. **Auto-Compaction**：80 轮对话压缩成 3 条 summary，Token 不够时自动触发
2. **Snapshot**：子代理秒启动，继承父上下文
3. **Heartbeat**：30 分钟自动巡检，清理僵尸会话

这些都是"Invisible to user"的 —— 用户无感知，但体验更流畅。

---

## 【Slide 9: Agent 杂谈】（3 分钟）

接下来聊点轻松的 —— 从 Claude Code 泄露源码看 Agent 的未来趋势。

**五大实验性功能**：

1. **BUDDY**：终端电子宠物。骨骼-灵魂双架构，让 AI 有"人格"。
2. **Dream System**：自动记忆整理。三层渐进压缩，解决长对话记忆衰减。
3. **KAIROS**：主动式助手。Always-On 感知，从"你问我答"到"我主动帮你"。
4. **Swarm**：多智能体协调。一群 Claude 协同作战，原生并发架构。
5. **TeamMemory**：团队共享记忆。让 AI 理解团队上下文。

**趋势洞察**：
> 情感连接 → 记忆延续 → 主动介入 → 能力扩展 → 组织融入

AI 正在从"工具"向"伙伴"进化。我们不是在造更好的工具，而是在造更好的伙伴。

---

## 【Slide 10: P100 案例】（现场演示，5 分钟）

理论讲完了，看一个真实案例。

**场景**：嵌入式固件开发 —— 编译、烧录、调试一条龙。

**用户只说一句话**："帮我编译并烧录到设备上，调试固件"

**背后激活的四个子系统**：
1. Bootstrap：加载 5 个核心 .md 文件
2. Skills：命中 device-build-debug
3. Memory：检索历史 IP、编译参数
4. System Prompt：拼接 SSH 配置 + Sandbox 规则

**执行链**：SSH (Compile) → rsync (Flash) → adb (Debug)

**现场演示**：（切换到终端，实际操作演示）

---

## 【现场演示脚本】（5-8 分钟）

### 演示 1：P100-recordpen 编译流程

```bash
# 1. 展示项目结构
ls -la ~/workspace/P100-recordpen/

# 2. 启动 OpenClaw 会话
openclaw agent start P100-recordpen

# 3. 输入请求
"帮我编译固件并烧录到设备上"

# 4. 展示 Agent 的思考过程
# - 读取 SKILL.md
# - SSH 连接到编译服务器
# - 执行 make 命令
# - rsync 同步固件
# - adb 推送并验证

# 5. 展示 Memory 检索
"用之前的编译配置"
```

### 演示 2：其他案例（可选）

**案例 A：AI-StockAssistant**（股票分析）
- 定时任务：每天早上 9 点自动分析市场
- 记忆功能：记住用户关注的股票列表
- Skills：获取实时行情、技术分析、生成报告

**案例 B：Agent 观察室**（内容创作）
- 深度研究：分析 Claude 源码 TODO
- 自动写作：生成技术文档
- 发布流程：保存草稿到 mdnice

**案例 C：Stone**（业务伙伴）
- 多 Agent 协作：Stone 调用 ffmedia 处理视频
- 跨会话记忆：记住业务上下文

---

## 【Slide 11: Summary】（1 分钟）

四个关键词总结 OpenClaw：

- **Inject**：注入上下文
- **Assemble**：拼装 Prompt
- **Extend**：扩展能力
- **Persist**：持久记忆

> Engineering, not magic.

谢谢大家。有问题欢迎交流。

---

## 【附录：Q&A 准备】

### 可能的问题 1：OpenClaw 和 LangChain 有什么区别？
**答**：LangChain 是 Library，OpenClaw 是 Framework + Runtime。LangChain 给你组件，OpenClaw 给你完整的"会话生命周期管理"。

### 可能的问题 2：Memory 的实现细节？
**答**：默认使用 qmd 向量索引，支持 pluggable backend。接口是 `memory_search` 和 `memory_get`，语义化检索。

### 可能的问题 3：Skills 和 MCP 的关系？
**答**：Skills 是 OpenClaw 原生能力，MCP 是 Anthropic 推的标准。OpenClaw 通过 `mcporter` 同时支持两种协议。

### 可能的问题 4： Claude 的实验性功能什么时候发布？
**答**：从源码完成度看，Dream System 接近生产，预计 2026 Q2；BUDDY 和 Swarm 在 Beta，预计 2026 Q3；KAIROS 和 TeamMemory 还在 Alpha，可能要到 2026 Q4 或 2027。

### 可能的问题 5：如何开始使用 OpenClaw？
**答**：官方仓库：https://github.com/openclaw/openclaw。推荐从 `openclaw doctor` 开始，然后读 `AGENTS.md` 和 `SOUL.md` 的模板。

---

## 【演讲技巧提示】

1. **节奏控制**：技术细节部分（Slide 3-7）放慢，杂谈部分（Slide 9）加快
2. **互动点**：在"85K 字符"和"Invisible to user"处可以停顿，让观众消化
3. **演示准备**：确保网络连接、SSH 密钥、设备连接都提前准备好
4. **备用方案**：如果演示失败，准备几张截图作为 backup

---

*演讲稿版本: 1.0*  
*更新日期: 2026-04-16*  
*作者: Agent观察室*
