# 记忆继承系统设计文档

## 概述

Stone 的记忆继承系统确保每个 subagent 都能继承之前所有失败尝试的记忆，从而避免重复操作并从错误中学习。

---

## 系统架构

### 1. 记忆分层架构

```
┌─────────────────────────────────────────────────┐
│          ContextBuilder (构建器)                │
│  - 从多个来源收集记忆                            │
│  - 组装成完整的上下文摘要                        │
└────────────┬────────────────────────────────────┘
             │
             ├─→ AGENTS.md (当前状态)
             ├─→ MONITOR-LOG.md (历史记录)
             ├─→ MemoryStore (分层记忆)
             └─→ Session 文件 (失败尝试)
```

### 2. 记忆存储架构

```
MemoryStore (分层存储)
  ├─ Critical Memory (关键决策)
  │   └─ 存储位置: memory/critical.json
  │   └─ 容量: 无限制
  │   └─ TTL: 永久
  │
  ├─ Operation Memory (操作记录)
  │   └─ 存储位置: memory/operation.jsonl
  │   └─ 容量: 1000 条
  │   └─ TTL: 30 天
  │
  └─ Failure Memory (失败记录)
      └─ 存储位置: memory/failure.jsonl
      └─ 容量: 100 条
      └─ TTL: 7 天
```

---

## 核心模块

### 1. MemoryStore（记忆存储管理器）

**文件**: `modules/memory-store.js`

**功能**:
- 分层存储记忆（长期/短期/失败）
- 智能记忆压缩
- 记忆去重和合并
- 记忆查询和检索

**关键方法**:

```javascript
// 添加关键决策记忆
await memoryStore.addCriticalMemory('ffmedia', '使用端口 9997 作为 RTSP 输出端口');

// 添加操作记忆
await memoryStore.addOperationMemory('ffmedia', '启动 4 个 RTSP 输入服务器');

// 添加失败记忆
await memoryStore.addFailureMemory('ffmedia', 'eth0 无 IP 地址，udhcpc 无法获取 DHCP');

// 查询记忆
const memories = memoryStore.queryMemories('ffmedia');

// 生成上下文摘要
const summary = memoryStore.generateContextSummary('ffmedia');
```

**记忆优先级**:

```javascript
MemoryPriority = {
  HIGH: 'high',      // 必须保留（关键决策）
  MEDIUM: 'medium',  // 可压缩（操作记录）
  LOW: 'low',        // 可删除（一般操作）
};
```

---

### 2. ContextBuilder（上下文构建器）

**文件**: `modules/context-builder.js`

**功能**:
- 从 AGENTS.md 读取最新状态
- 从 MONITOR-LOG.md 读取历史记录
- 从 MemoryStore 读取记忆
- 从失败 session 文件读取摘要
- 组装成完整的上下文摘要

**工作流程**:

```
ContextBuilder.buildTaskPrompt(agentId, task)
  ↓
buildContext(agentId)
  ├─ readAgentStatus() → AGENTS.md
  ├─ readHistorySummary() → MONITOR-LOG.md
  ├─ generateContextSummary() → MemoryStore
  └─ readFailedSessions() → Session 文件
  ↓
构建 Prompt
  ├─ 当前状态
  ├─ 记忆摘要（新增）
  ├─ 失败尝试
  └─ 最近的错误
  ↓
返回增强的任务 prompt
```

---

## 记忆类型

### 1. 关键决策记忆（Critical Decision）

**存储**: `memory/critical.json`

**用途**: 存储重要的决策和配置

**示例**:
```json
{
  "id": "1772456000000-abc123",
  "agentId": "ffmedia",
  "type": "critical_decision",
  "decision": "使用端口 9997 作为 RTSP 输出端口",
  "priority": "high",
  "timestamp": 1772456000000,
  "created": "2026-03-02T20:47:00.000Z"
}
```

**何时添加**:
- 重要的配置变更
- 关键的架构决策
- 无法回退的操作

---

### 2. 操作记忆（Operation）

**存储**: `memory/operation.jsonl`

**用途**: 存储详细的操作记录

**示例**:
```json
{
  "id": "1772456000000-def456",
  "agentId": "ffmedia",
  "type": "operation",
  "operation": "启动 4 个 RTSP 输入服务器（端口 8554-8557）",
  "priority": "medium",
  "timestamp": 1772456000000,
  "created": "2026-03-02T20:47:00.000Z"
}
```

**何时添加**:
- 每次执行重要操作
- 每次状态变更
- 每次完成一个阶段

---

### 3. 失败记忆（Failure）

**存储**: `memory/failure.jsonl`

**用途**: 存储失败的尝试和错误

**示例**:
```json
{
  "id": "1772456000000-ghi789",
  "agentId": "ffmedia",
  "type": "failure",
  "failure": "eth0 无 IP 地址，udhcpc 无法获取 DHCP",
  "priority": "medium",
  "timestamp": 1772456000000,
  "created": "2026-03-02T20:47:00.000Z"
}
```

**何时添加**:
- subagent 失败
- 操作失败
- 检测到异常

---

## 使用示例

### 场景 1：ffmedia 网络配置失败

#### 1. 第一次尝试（subagent1）

```javascript
// subagent1 执行
await memoryStore.addOperationMemory('ffmedia', '尝试使用 udhcpc 获取 IP 地址');

// 失败
await memoryStore.addFailureMemory('ffmedia', 'udhcpc 无法获取 DHCP，持续广播');
```

#### 2. 第二次尝试（subagent2）

```javascript
// ContextBuilder 构建上下文
const context = await contextBuilder.buildContext('ffmedia');

// context.memories 包含:
{
  criticalDecisions: [],
  recentOperations: [
    {
      operation: '尝试使用 udhcpc 获取 IP 地址',
      created: '2026-03-02T20:47:00.000Z'
    }
  ],
  recentFailures: [
    {
      failure: 'udhcpc 无法获取 DHCP，持续广播',
      created: '2026-03-02T20:47:00.000Z'
    }
  ]
}

// subagent2 知道之前尝试过 udhcpc，可以跳过或尝试其他方法
```

---

## Prompt 示例

### 增强后的任务 Prompt

```markdown
## 历史上下文摘要

### 当前状态
- **状态**: 🔴 阻塞
- **最后活动**: 2026-03-02 20:47
- **最后任务**: 继续测试 demo_rtsp_multi_splice

### 记忆摘要

#### 关键决策 (2 条)
- **2026-03-02T20:45:00.000Z**: 使用端口 9997 作为 RTSP 输出端口
- **2026-03-02T20:46:00.000Z**: 使用 /live/test 作为 RTSP 输出路径

#### 最近操作 (5 条)
- **2026-03-02T20:47:00.000Z**: 启动 4 个 RTSP 输入服务器（端口 8554-8557）
- **2026-03-02T20:46:30.000Z**: 修改源代码（端口 9999→9997）
- **2026-03-02T20:46:00.000Z**: 推送 libffmedia.so 到 /oem/
- **2026-03-02T20:45:30.000Z**: 重新编译 demo_rtsp_multi_splice
- **2026-03-02T20:45:00.000Z**: 下载编译产物

#### 最近失败 (1 条)
- **2026-03-02T20:47:30.000Z**: eth0 无 IP 地址，udhcpc 无法获取 DHCP

### 之前的尝试 (3 次)

#### 尝试 #1: bd6654e5
- **结果**: aborted
- **任务**: 尝试使用 udhcpc 获取 IP 地址
- **错误**:
  - udhcpc: broadcasting discover

### 最近的错误
- udhcpc: broadcasting discover
- eth0 接口无 IP 地址

---

## 你的任务

设备已恢复（adb devices 显示 device），继续之前的任务：

1. 配置设备网络
2. 验证 4 个 RTSP 输入服务器
3. 验证 demo_rtsp_multi_splice 的 RTSP 输出

### 重要提示
- 你已经知道之前的所有失败尝试和错误
- 避免重复之前的错误操作
- 基于"历史上下文摘要"中的信息，采用不同的策略
- 如果遇到相同的问题，尝试不同的解决方法
```

---

## 优化策略

### 1. 记忆压缩

当记忆数量超过阈值时，使用 LLM 进行压缩：

```javascript
// 压缩操作记忆
const compressed = await memoryStore.compressMemories('ffmedia', MemoryType.OPERATION);

// 从 100 条压缩到 10 条摘要
```

### 2. 记忆去重

在添加新记忆时，自动检测并去重：

```javascript
// 检测到重复记忆，不会添加
await memoryStore.addOperationMemory('ffmedia', '启动 RTSP 服务器'); // 已存在
```

### 3. 记忆过期

自动清理过期的记忆：

- 操作记忆：30 天后自动删除
- 失败记忆：7 天后自动删除
- 关键决策：永久保留

---

## 配置选项

### MemoryStore 配置

```javascript
{
  maxOperationMemories: 1000,      // 最多保留 1000 条操作记忆
  maxFailureMemories: 100,         // 最多保留 100 条失败记忆
  operationMemoryTTL: 30 * 24 * 60 * 60 * 1000, // 30 天
  failureMemoryTTL: 7 * 24 * 60 * 60 * 1000,    // 7 天
}
```

### ContextBuilder 配置

```javascript
{
  maxCriticalMemories: 10,         // 最多显示 10 条关键决策
  maxOperationMemories: 20,        // 最多显示 20 条最近操作
  maxFailureMemories: 10,          // 最多显示 10 条最近失败
}
```

---

## 性能优化

### 1. 内存缓存

MemoryStore 使用内存缓存，避免频繁读取文件：

```javascript
this.cache = {
  critical: null,   // 关键决策记忆缓存
  operation: [],     // 操作记忆缓存
  failure: [],       // 失败记忆缓存
};
```

### 2. 增量持久化

新增记忆时使用追加模式，避免重写整个文件：

```javascript
// 追加操作记忆
await fs.appendFile(this.operationMemoryPath, JSON.stringify(memory) + '\n');
```

### 3. 异步清理

在后台异步清理过期记忆，不阻塞主流程：

```javascript
// 添加记忆后异步清理
this.cleanupOperationMemory(); // 不 await
```

---

## 扩展性

### 1. 跨 Agent 记忆共享

```javascript
// ffmedia 可以读取 agentmesh 的记忆
const agentmeshMemories = memoryStore.queryMemories('agentmesh');
```

### 2. 记忆标签

```javascript
// 为记忆添加标签
await memoryStore.addOperationMemory('ffmedia', '启动 RTSP 服务器', {
  tags: ['network', 'rtsp', 'server'],
  phase: 'initialization'
});
```

### 3. 记忆搜索

```javascript
// 根据关键词搜索记忆
const results = memoryStore.searchMemories('ffmedia', 'udhcpc');
```

---

## 总结

**记忆继承系统** 的核心价值：

1. ✅ **完整继承**：subagentN 继承所有之前失败尝试的记忆
2. ✅ **避免重复**：基于历史记忆，避免重复相同的操作
3. ✅ **从错误中学习**：记忆存储失败经验，subagent 可以学习
4. ✅ **智能决策**：基于记忆摘要，subagent 做出更智能的决策
5. ✅ **持久化存储**：记忆分层存储，长期保留关键决策

**最终效果**：

```
subagent1 (失败) → 记忆存储 → subagent2 (知道 subagent1) → 记忆存储 → subagent3 (知道 subagent1 和 subagent2)
```

每个 subagent 都有完整的上下文，可以智能地继续执行任务！

---

**相关文档**:
- `docs/CONTEXT-BUILDER.md` - ContextBuilder 详细使用指南
- `docs/CONTEXT-BUILDER-SOLUTION.md` - 解决方案总结
- `modules/context-builder.js` - ContextBuilder 实现
- `modules/memory-store.js` - MemoryStore 实现
