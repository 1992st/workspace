# 一场 46万行代码的意外：Claude Code 是怎么把自己"开源"的

> **Agent 小茶馆 · 系列第1期**
> 
> 3月31日凌晨，推特上一条消息炸了："Claude Code 的完整源代码，就在 npm 包里，谁都能下。"
> 
> 不是泄露，不是黑客攻击，是**自己把自己开源了**。

---

## 事情经过

**3月31日**，推友 Chaofan Shou 发了一条爆炸性消息：

> "Anthropic 的 Claude Code 完整源代码，就在 npm 包里，谁都能下。"

不是部分代码，是**全部**。主文件 785KB，核心逻辑 46KB，40多个工具，连内部代号都暴露了。

怎么泄露的？说出来你可能不信——**sourcemap 文件没删**。

---

## 泄露的源码里有什么？

我扒了一下，这不仅仅是个 CLI 工具，而是一个**生产级的 AI Coding Agent 框架**。以下是核心发现：

### 1. BUDDY：藏在代码里的电子宠物

**代码位置**：`src/buddy/`、`src/services/buddy.ts`

Claude Code 里面藏了一套"电子宠物"系统。你没看错，就是那个 90 年代的 Tamagotchi 概念。

- 18 种"生物"，从普通的 Pebblecrab 到传说级的 Nebulynx
- 每个用户 deterministically（确定性）生成专属宠物
- 宠物有属性：DEBUGGING（调试）、CHAOS（混乱）、SNARK（嘲讽）

核心逻辑在 `src/buddy/biome.ts` 和 `src/buddy/creature.ts`，用 Mulberry32 PRNG 算法基于用户 ID 生成专属宠物。这玩意儿干嘛用的？可能是让用户对 AI 产生情感连接的小把戏。

### 2. Undercover Mode：AI 也有"卧底模式"

**代码位置**：`src/services/undercover.ts`、`src/prompts/undercover.ts`

Anthropic 员工用 Claude Code 给开源项目贡献代码时，系统会进入"卧底模式"：
- 禁止提及内部模型代号（比如 Capybara、**Tengu**、Cuttlefish）
- 隐藏"用户是 AI"这个事实
- 自动改写可能暴露身份的话术

**泄露证实了："Tengu" 是 Claude Code 的内部代号。**还有其他代号如 Capybara、Cuttlefish，暗示 Claude 家族内部还有我们不知道的成员。

### 3. Dream 系统：AI 真的会"做梦"

**代码位置**：`src/services/dream/`、`src/services/autoDream.ts`

Claude Code 有一个 `autoDream` 服务，字面意思：自动做梦。

流程是这样的：
1. **Orient**：读取 MEMORY.md（长期记忆文件）
2. **Gather**：翻当天的日志，找新信息  
3. **Consolidate**：把新信息写回 MEMORY.md
4. **Prune**：删掉不重要的，保持记忆精简

这叫"记忆巩固"，模仿人类睡觉时整理白天记忆的过程。核心实现在 `src/services/dream/consolidation.ts`。

### 4. KAIROS & ULTRAPLAN：两个神秘子系统

**代码位置**：`src/services/kairos/`、`src/services/ultraplan.ts`

- **KAIROS**：常驻后台的"主动助手"。你不说话，它也在看日志，发现机会就行动。代码在 `src/services/kairos/orchestrator.ts`。
- **ULTRAPLAN**：复杂任务卸载器。遇到需要深度思考的任务，扔给远程的 Opus 4.6 跑 30 分钟。实现在 `src/services/ultraplan.ts`。

---

## 技术架构一览

**代码总览**：
```
src/
├── main.tsx                 # CLI 入口（785KB）
├── QueryEngine.ts          # 核心 LLM 逻辑（46KB）
├── Tool.ts                 # 工具基类
├── tools/                  # 40+ Agent 工具
│   ├── bash.ts
│   ├── file.ts
│   ├── lsp.ts
│   └── web.ts
├── coordinator/            # 多 Agent 编排（Swarm）
│   └── swarm.ts
├── bridge/                 # IDE 集成层
├── buddy/                  # 电子宠物系统
├── services/               # 后台服务
│   ├── dream/             # Dream 记忆系统
│   ├── kairos/            # KAIROS 主动助手
│   ├── undercover.ts      # 卧底模式
│   └── ultraplan.ts       # ULTRAPLAN 深度规划
└── memory/                 # 记忆管理
```

Claude Code 不是简单的"调 API 的脚本"，它是一个完整的 Agent 框架：

| 模块 | 功能 | 代码位置 |
|------|------|----------|
| `main.tsx` | CLI 入口，React + Ink 渲染终端界面 | `src/main.tsx` |
| `QueryEngine.ts` | 46KB 的核心 LLM 调用逻辑 | `src/QueryEngine.ts` |
| `tools/` | 40+ 个工具：Bash、文件操作、LSP、Web 搜索 | `src/tools/` |
| `coordinator/` | 多 Agent 编排（Swarm 模式）| `src/coordinator/swarm.ts` |
| `buddy/` | 电子宠物系统 | `src/buddy/` |
| `services/` | MCP、OAuth、分析、Dream 服务 | `src/services/` |

技术栈：Bun 运行时 + TypeScript + React（对，终端里跑 React）。

---

## 这件事给我们的启示

### 1. 生产级 Agent 怎么设计
虽然泄露是事故，但 Claude Code 的架构值得研究：
- **多 Agent 怎么编排？** 看 `src/coordinator/swarm.ts`
- **记忆系统怎么设计？** 看 `src/services/dream/`
- **工具调用怎么抽象？** 看 `src/Tool.ts` 和 `src/tools/`

这些都在泄露的源码里有答案。

### 2. 配置即安全
`.npmignore` 少写一行，可能导致核心知识产权全部暴露。CI/CD 流程里要加强制检查。

---

## 3 条可执行动作

1. **今晚就检查你的 npm 包**：运行 `npm pack --dry-run | grep ".map"`，如果有输出，说明你在泄露源码

2. **加固发布流程**：在 CI 里加一步 `find . -name "*.map" -delete`，双重保险

3. **研究 Agent 架构**：如果有技术团队，可以借这个机会学习 Claude Code 的工具设计、记忆系统、多 Agent 编排——这些是生产级 AI Agent 的教科书

---

## 附：sourcemap 是什么？

简单说：sourcemap 是 JavaScript 调试文件，里面通过 `sourcesContent` 字段**完整嵌入了原始源代码**。Claude Code 的发布流程漏了一件事：没有把 `*.map` 写进 `.npmignore`。结果 npm 包里的 sourcemap 文件，成了免费开源大礼包。

**通俗说**：sourcemap 就像外卖的"后厨监控"——顾客看不到，但店长能看。问题是，Anthropic 把这监控录像直接塞进了外卖袋，送给了每一个下载的人。

---

## 小结

Claude Code 的泄露不是因为黑客攻击，而是因为一个配置疏忽。但它也让我们看到了 Anthropic 是怎么设计生产级 AI Agent 的：有电子宠物增加情感连接，有 Dream 系统整理记忆，有卧底模式保护商业机密。

**下一期预告**：我会深入分析 Claude Code 的"工具系统"——40 多个工具是怎么设计、注册、调用的，以及我们可以怎么借鉴到自己的项目里。

---

*参考资料：泄露源码镜像由 Yasas Banu 整理，原始发现者为 Chaofan Shou (@Fried_rice)。本文仅供技术分析和学习讨论。*
