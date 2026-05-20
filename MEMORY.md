# MEMORY.md - Stone 记忆系统

## 概述

Stone 的记忆系统确保每个 subagent 都能继承之前所有尝试的记忆，从而避免重复操作并从错误中学习。

---

## 核心功能

### 1. 记忆分层存储

```
MemoryStore
  ├─ Critical Memory (critical.json)     - 关键决策（永久）
  ├─ Operation Memory (operation.jsonl)   - 操作记录（30 天，最多 1000 条）
  └─ Failure Memory (failure.jsonl)       - 失败记录（7 天，最多 100 条）
```

### 2. 记忆继承

```
subagent1 (失败) → 记忆存储 → subagent2 (知道 subagent1) → 记忆存储 → subagent3 (知道所有)
```

### 3. 上下文构建

ContextBuilder 从多个来源收集记忆，组装成完整的上下文摘要：

- AGENT-STATES.md - Agent 当前状态
- MONITOR-LOG.md - 历史监控记录
- MemoryStore - 分层记忆
- Session 文件 - 失败尝试摘要

---

## 使用示例

### 添加记忆

```javascript
import { MemoryStore, MemoryPriority } from './modules/memory-store.js';

const memoryStore = new MemoryStore();
await memoryStore.init();

// 添加关键决策记忆
await memoryStore.addCriticalMemory('ffmedia', '使用端口 9997 作为 RTSP 输出端口');

// 添加操作记忆
await memoryStore.addOperationMemory('ffmedia', '启动 4 个 RTSP 输入服务器');

// 添加失败记忆
await memoryStore.addFailureMemory('ffmedia', 'eth0 无 IP 地址，udhcpc 无法获取 DHCP');
```

### 查询记忆

```javascript
// 查询某个 Agent 的所有记忆
const memories = memoryStore.queryMemories('ffmedia');

// 生成上下文摘要
const summary = memoryStore.generateContextSummary('ffmedia');
console.log(summary);
// {
//   agentId: 'ffmedia',
//   criticalDecisions: [...],
//   recentOperations: [...],
//   recentFailures: [...]
// }
```

### 构建任务 Prompt

```javascript
import ContextBuilder from './modules/context-builder.js';

const contextBuilder = new ContextBuilder();

// 构建包含记忆的增强任务 prompt
const enhancedTask = await contextBuilder.buildTaskPrompt('ffmedia', '继续测试 RTSP 拼接');

console.log(enhancedTask);
// 包含：
// - Agent 当前状态
// - 历史上下文摘要
// - 记忆摘要（关键决策、最近操作、最近失败）
// - 之前的失败尝试
// - 最近的错误信息
```

---

## 核心价值

### 避免重复

- ✅ subagent2 知道 subagent1 做了什么
- ✅ subagent2 跳过重复的操作
- ✅ subagent2 尝试不同的方法

### 智能决策

- ✅ 基于记忆摘要
- ✅ 了解历史上下文
- ✅ 做出更智能的决策

### 自动清理

- ✅ 自动清理过期记忆
- ✅ 自动删除最旧的记忆（超出限制时）
- ✅ 初始化时执行清理

---

## 记忆类型

### Critical Memory（关键决策）

- **存储位置**: `memory/critical.json`
- **TTL**: 永久
- **容量**: 无限制
- **优先级**: HIGH
- **用途**: 存储关键决策（如端口配置、架构选择等）

### Operation Memory（操作记录）

- **存储位置**: `memory/operation.jsonl`
- **TTL**: 30 天
- **容量**: 1000 条
- **优先级**: MEDIUM
- **用途**: 记录操作历史

### Failure Memory（失败记录）

- **存储位置**: `memory/failure.jsonl`
- **TTL**: 7 天
- **容量**: 100 条
- **优先级**: MEDIUM
- **用途**: 记录失败原因

---

## 文件结构

```
stone/
├── MEMORY.md                           # 本文档
├── MEMORY-INHERITANCE-README.md        # Quick Start
├── modules/
│   ├── memory-store.js                 # MemoryStore 实现
│   └── context-builder.js             # ContextBuilder 实现
├── memory/
│   ├── critical.json                   # 关键决策记忆
│   ├── operation.jsonl                 # 操作记忆
│   └── failure.jsonl                   # 失败记忆
└── docs/
    ├── MEMORY-INHERITANCE-SYSTEM.md    # 详细设计文档
    ├── MEMORY-INHERITANCE-SUMMARY.md  # 设计总结
    └── MEMORY-INHERITANCE-COMPLETION-REPORT.md # 完成报告
```

---

## 版本历史

- **v1.0** (2026-03-06 09:23)
  - ✅ 初始化记忆系统
  - ✅ 实现 MemoryStore（分层存储、自动清理）
  - ✅ 实现 ContextBuilder（上下文构建、任务 Prompt 生成）
  - ✅ 创建 MEMORY.md 入口文档
  - 📋 修复问题：
    - memory-store.js: 添加初始化时清理过期记忆的功能
    - context-builder.js: 修复 AGENT-STATES.md 的读取逻辑（匹配实际格式）
  - 📋 效果：
    - 初始化时自动清理过期记忆
    - 正确读取 Agent 状态（状态、最后活动、停滞时长、说明）
    - 记忆系统完整可用

---

## 相关文档

- `MEMORY-INHERITANCE-README.md` - Quick Start
- `docs/MEMORY-INHERITANCE-SYSTEM.md` - 详细设计文档
- `docs/MEMORY-INHERITANCE-SUMMARY.md` - 设计总结
- `docs/MEMORY-INHERITANCE-COMPLETION-REPORT.md` - 完成报告

---

**Stone Agent** 🗿
