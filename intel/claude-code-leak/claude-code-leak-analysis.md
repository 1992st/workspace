# Claude Code 源码泄露事件分析

## 事件背景

**时间**：2026年3月31日  
**发现者**：Chaofan Shou (@Fried_rice)  
**泄露范围**：Claude Code CLI 完整源代码（约 46万行）

## 泄露原因

Claude Code 在发布到 npm 时，**忘记排除 sourcemap 文件** (`.map`)。

Sourcemap 是 JavaScript/TypeScript 构建时生成的调试文件，里面通过 `sourcesContent` 字段**完整嵌入了原始源代码**。这相当于把没压缩的源码打包进了发布的 npm 包。

```json
{
  "version": 3,
  "sources": ["../src/main.tsx", "..."],
  "sourcesContent": ["// 完整的原始源代码..."]
}
```

## 泄露内容概览

这是一个**生产级的 AI Coding Agent**，核心特点：

### 1. 规模巨大
- 主入口文件 `main.tsx`：785KB（约 2万行）
- `QueryEngine.ts`：46KB（核心 LLM 逻辑）
- 40+ 个内置工具（Bash、文件、LSP、Web 等）

### 2. 技术栈
- **运行时**：Bun（优先）或 Node.js
- **UI**：React + Ink（终端渲染）
- **架构**：自定义多 Agent 编排系统

### 3. 内部功能揭秘

#### 🐣 BUDDY - 电子宠物系统
- 18 种"生物"（从普通 Pebblecrab 到传说级 Nebulynx）
- 基于用户 ID 的确定性随机（Mulberry32 PRNG）
- 每个宠物有 DEBUGGING、CHAOS、SNARK 等属性

#### 🕵️‍♂️ Undercover Mode（卧底模式）
Anthropic 员工用 Claude Code 参与开源项目时，系统会：
- 阻止泄露内部模型代号（如 Capybara、Tengu）
- 隐藏用户是 AI 的事实
- **证实了 "Tengu" 是 Claude Code 的内部代号**

#### 🌙 Dream 系统（记忆整理）
Claude Code 会在后台"做梦"来整理记忆：
1. Orient：读取 MEMORY.md
2. Gather：从日志找新信号
3. Consolidate：更新长期记忆
4. Prune：清理低效上下文

#### 🚀 KAIROS & ULTRAPLAN
- **KAIROS**：常驻后台的主动助手，监控日志并主动行动
- **ULTRAPLAN**：把复杂任务卸载到远程 Opus 4.6，可运行30分钟深度规划

## 目录结构

```
src/
├── main.tsx              # CLI 入口（Commander.js + React/Ink）
├── QueryEngine.ts        # 核心 LLM 逻辑（~46K）
├── Tool.ts               # 工具基类定义
├── tools/                # 40+ Agent 工具
├── services/             # 后端（MCP、OAuth、分析、Dream）
├── coordinator/          # 多 Agent 编排（Swarm）
├── bridge/               # IDE 集成层
└── buddy/                # 秘密电子宠物系统
```

## 安全启示

1. **sourcemap 是源码**：`.map` 文件不只是调试信息，它包含完整原始代码
2. **npm 发布检查**：必须确保 `*.map` 在 `.npmignore` 中
3. **生产构建配置**：Bun 默认生成 sourcemap，需显式禁用

## 3条可执行动作

1. **检查你的 npm 包**：运行 `npm pack --dry-run` 确认没有 `.map` 文件被打包
2. **加固 CI/CD**：在发布流程中加入 `find . -name "*.map" -delete` 清理步骤
3. **学习架构设计**：虽然源码泄露是事故，但 Claude Code 的多 Agent 编排、记忆系统、工具设计值得研究

---

## 后续

Anthropic 已删除问题版本，但这提醒所有人：**生产发布的构建产物需要严格审计**。即使是无意的配置疏忽，也可能导致核心知识产权完全暴露。

---

*本分析基于公开泄露的源码，仅供教育和研究目的。*
