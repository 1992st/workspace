# 记忆继承系统 - Quick Start

## 🚀 快速开始

### 运行测试

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone

# 基础测试
node scripts/test-memory-inheritance.js

# 功能验证
node scripts/verify-memory-inheritance.js
```

---

## 📦 核心模块

### 1. MemoryStore（记忆存储）

```javascript
import { MemoryStore, MemoryPriority } from './modules/memory-store.js';

const memoryStore = new MemoryStore();
await memoryStore.init();

// 添加记忆
await memoryStore.addCriticalMemory('ffmedia', '使用端口 9997', MemoryPriority.HIGH);
await memoryStore.addOperationMemory('ffmedia', '启动 RTSP 服务器');
await memoryStore.addFailureMemory('ffmedia', 'udhcpc 无法获取 DHCP');

// 查询记忆
const memories = memoryStore.queryMemories('ffmedia');
```

### 2. ContextBuilder（上下文构建）

```javascript
import ContextBuilder from './modules/context-builder.js';

const contextBuilder = new ContextBuilder();
const prompt = await contextBuilder.buildTaskPrompt('ffmedia', '继续测试');

console.log(prompt); // 包含记忆的增强 prompt
```

---

## 📚 文档

- `docs/MEMORY-INHERITANCE-SYSTEM.md` - 详细设计文档
- `docs/MEMORY-INHERITANCE-SUMMARY.md` - 设计总结
- `docs/MEMORY-INHERITANCE-COMPLETION-REPORT.md` - 完成报告

---

## 🎯 核心价值

### 记忆继承

```
subagent1 (失败) → 记忆存储 → subagent2 (知道 subagent1) → 记忆存储 → subagent3 (知道所有)
```

### 避免重复

- ✅ subagent2 知道 subagent1 做了什么
- ✅ subagent2 跳过重复的操作
- ✅ subagent2 尝试不同的方法

### 智能决策

- ✅ 基于记忆摘要
- ✅ 了解历史上下文
- ✅ 做出更智能的决策

---

## 📊 测试结果

### 基础测试

```
✅ 初始化 MemoryStore
✅ 添加测试记忆
✅ 查询记忆
✅ 生成上下文摘要
✅ 测试 ContextBuilder
✅ 构建任务 Prompt
```

### 功能验证

```
✅ subagent1 记忆存储
✅ subagent2 继承记忆
✅ subagent2 知道 subagent1 做了什么
✅ subagent2 避免重复操作
✅ 智能决策验证
```

---

## 📁 文件结构

```
stone/
├── modules/
│   ├── context-builder.js        # ContextBuilder 实现
│   └── memory-store.js           # MemoryStore 实现
├── scripts/
│   ├── test-memory-inheritance.js       # 基础测试
│   └── verify-memory-inheritance.js     # 功能验证
├── docs/
│   ├── MEMORY-INHERITANCE-SYSTEM.md     # 详细设计文档
│   ├── MEMORY-INHERITANCE-SUMMARY.md   # 设计总结
│   └── MEMORY-INHERITANCE-COMPLETION-REPORT.md # 完成报告
└── memory/
    ├── critical.json      # 关键决策记忆
    ├── operation.jsonl    # 操作记忆
    └── failure.jsonl      # 失败记忆
```

---

## 🔧 集成到 Stone

在 `WakeupManager` 中使用 `ContextBuilder`：

```javascript
import ContextBuilder from './context-builder.js';

class WakeupManager {
  constructor(stone) {
    this.contextBuilder = new ContextBuilder();
  }

  async spawnAgent(agentId, task) {
    // 构建增强的任务 prompt（包含记忆）
    const enhancedTask = await this.contextBuilder.buildTaskPrompt(agentId, task);

    const result = await sessions_spawn({
      agentId: agentId,
      task: enhancedTask,  // ✅ 使用增强的任务
      mode: 'session',
      thread: true,
      label: `stone-wakeup-${agentId}`,
      runTimeoutSeconds: 1800,
    });

    return result;
  }
}
```

---

## 🎯 总结

**记忆继承系统** - 让 subagentN 继承所有之前失败尝试的记忆！

- ✅ 避免重复操作
- ✅ 从错误中学习
- ✅ 智能决策

**Stone Agent** 🗿
