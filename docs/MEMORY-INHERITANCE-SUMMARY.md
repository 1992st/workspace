# 记忆继承系统 - 设计总结

## 设计目标

**核心问题**：subagentN 如何继承之前所有失败尝试的记忆？

**解决方案**：
1. ✅ 分层记忆存储（长期/短期/失败）
2. ✅ 智能记忆继承（ContextBuilder）
3. ✅ 记忆去重和压缩
4. ✅ 持久化存储

---

## 系统架构

### 整体流程

```
subagent1 (失败)
  ↓
MemoryStore.addFailureMemory('ffmedia', 'udhcpc 无法获取 DHCP')
  ↓
记忆存储到 memory/failure.jsonl
  ↓
subagent2 被唤醒
  ↓
ContextBuilder.buildContext('ffmedia')
  ├─ readAgentStatus() → AGENTS.md
  ├─ readHistorySummary() → MONITOR-LOG.md
  ├─ generateContextSummary() → MemoryStore ✨
  └─ readFailedSessions() → Session 文件
  ↓
组装成完整的上下文摘要
  ↓
包含记忆的 Prompt 发送给 subagent2
  ↓
subagent2 知道 subagent1 做了什么
  ↓
避免重复操作，尝试不同的方法
```

---

## 核心模块

### 1. MemoryStore（记忆存储管理器）

**文件**: `modules/memory-store.js`

**职责**:
- 分层存储记忆
- 记忆去重和合并
- 记忆压缩和清理
- 记忆查询和检索

**存储结构**:

```
memory/
├── critical.json     # 关键决策记忆（永久）
├── operation.jsonl   # 操作记忆（30 天）
└── failure.jsonl     # 失败记忆（7 天）
```

**关键方法**:

```javascript
// 添加记忆
await memoryStore.addCriticalMemory(agentId, decision, priority);
await memoryStore.addOperationMemory(agentId, operation, priority);
await memoryStore.addFailureMemory(agentId, failure, priority);

// 查询记忆
const memories = memoryStore.queryMemories(agentId, types);

// 生成上下文摘要
const summary = memoryStore.generateContextSummary(agentId);

// 合并记忆（去重）
const mergedCount = await memoryStore.mergeMemories(newMemories);

// 压缩记忆
const compressed = await memoryStore.compressMemories(agentId, type);
```

---

### 2. ContextBuilder（上下文构建器）

**文件**: `modules/context-builder.js`

**职责**:
- 从多个来源收集记忆
- 组装成完整的上下文摘要
- 生成增强的任务 prompt

**工作流程**:

```
ContextBuilder.buildTaskPrompt(agentId, task)
  ↓
buildContext(agentId)
  ├─ readAgentStatus() → 当前状态
  ├─ readHistorySummary() → 历史记录
  ├─ generateContextSummary() → 记忆摘要 ✨
  └─ readFailedSessions() → 失败尝试
  ↓
构建 Prompt
  ├─ 当前状态
  ├─ 记忆摘要 ✨
  ├─ 失败尝试
  └─ 最近的错误
  ↓
返回增强的任务 prompt
```

**生成示例**:

```markdown
## 历史上下文摘要

### 当前状态
- **状态**: 🔴 阻塞
- **最后活动**: 2026-03-02 20:47
- **最后任务**: 继续测试 demo_rtsp_multi_splice

### 记忆摘要 ✨

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
...

### 最近的错误
...

---

## 你的任务

配置设备网络，继续测试 demo_rtsp_multi_splice

### 重要提示
- 你已经知道之前的所有失败尝试和错误
- 避免重复之前的错误操作
- 基于"历史上下文摘要"中的信息，采用不同的策略
- 如果遇到相同的问题，尝试不同的解决方法
```

---

## 记忆类型

### 1. 关键决策记忆（Critical Decision）

**存储**: `memory/critical.json`

**特点**:
- 无容量限制
- 永久保留
- 必须保留（Priority: HIGH）

**何时添加**:
- 重要的配置变更
- 关键的架构决策
- 无法回退的操作

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

---

### 2. 操作记忆（Operation）

**存储**: `memory/operation.jsonl`

**特点**:
- 最多 1000 条
- 保留 30 天
- 可压缩（Priority: MEDIUM）

**何时添加**:
- 每次执行重要操作
- 每次状态变更
- 每次完成一个阶段

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

---

### 3. 失败记忆（Failure）

**存储**: `memory/failure.jsonl`

**特点**:
- 最多 100 条
- 保留 7 天
- 可压缩（Priority: MEDIUM）

**何时添加**:
- subagent 失败
- 操作失败
- 检测到异常

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

---

## 记忆继承流程

### 场景：ffmedia 网络配置失败

#### 第 1 次尝试（subagent1）

```javascript
// subagent1 执行
await memoryStore.addOperationMemory('ffmedia', '尝试使用 udhcpc 获取 IP 地址');

// 失败
await memoryStore.addFailureMemory('ffmedia', 'udhcpc 无法获取 DHCP，持续广播');
```

**记忆存储**:
- `memory/operation.jsonl`: 1 条操作记忆
- `memory/failure.jsonl`: 1 条失败记忆

---

#### 第 2 次尝试（subagent2）

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
```

**Prompt 包含记忆**:
```markdown
### 记忆摘要

#### 最近操作 (1 条)
- **2026-03-02T20:47:00.000Z**: 尝试使用 udhcpc 获取 IP 地址

#### 最近失败 (1 条)
- **2026-03-02T20:47:30.000Z**: udhcpc 无法获取 DHCP，持续广播
```

**subagent2 的决策**:
- ✅ 知道之前尝试过 udhcpc
- ✅ 跳过 udhcpc（已尝试并失败）
- ✅ 尝试其他方法（如手动配置 IP）

---

#### 第 3 次尝试（subagent3）

```javascript
// ContextBuilder 构建上下文
const context = await contextBuilder.buildContext('ffmedia');

// context.memories 包含所有之前的记忆:
{
  criticalDecisions: [],
  recentOperations: [
    {
      operation: '尝试使用 udhcpc 获取 IP 地址',
      created: '2026-03-02T20:47:00.000Z'
    },
    {
      operation: '手动配置 IP 地址 192.168.150.120',
      created: '2026-03-02T21:00:00.000Z'
    }
  ],
  recentFailures: [
    {
      failure: 'udhcpc 无法获取 DHCP，持续广播',
      created: '2026-03-02T20:47:30.000Z'
    },
    {
      failure: '手动配置 IP 后仍无法连接',
      created: '2026-03-02T21:05:00.000Z'
    }
  ]
}
```

**subagent3 的决策**:
- ✅ 知道之前尝试过 udhcpc（失败）
- ✅ 知道之前尝试过手动配置 IP（失败）
- ✅ 跳过这两种方法
- ✅ 尝试其他方法（如重启设备）

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

**优势**:
- ✅ 读取速度极快（内存 vs 磁盘）
- ✅ 减少文件 I/O

---

### 2. 增量持久化

新增记忆时使用追加模式，避免重写整个文件：

```javascript
// 追加操作记忆
await fs.appendFile(this.operationMemoryPath, JSON.stringify(memory) + '\n');
```

**优势**:
- ✅ 不需要重写整个文件
- ✅ 性能更好

---

### 3. 异步清理

在后台异步清理过期记忆，不阻塞主流程：

```javascript
// 添加记忆后异步清理
this.cleanupOperationMemory(); // 不 await
```

**优势**:
- ✅ 不阻塞主流程
- ✅ 自动维护记忆数量

---

### 4. 记忆去重

在添加新记忆时，自动检测并去重：

```javascript
// 检测到重复记忆，不会添加
await memoryStore.addOperationMemory('ffmedia', '启动 RTSP 服务器'); // 已存在
```

**优势**:
- ✅ 避免重复记忆
- ✅ 节省存储空间

---

## 扩展性

### 1. 跨 Agent 记忆共享

```javascript
// ffmedia 可以读取 agentmesh 的记忆
const agentmeshMemories = memoryStore.queryMemories('agentmesh');
```

**应用场景**:
- Agent 之间共享经验
- Agent 学习其他 Agent 的成功方法

---

### 2. 记忆标签

```javascript
// 为记忆添加标签
await memoryStore.addOperationMemory('ffmedia', '启动 RTSP 服务器', {
  tags: ['network', 'rtsp', 'server'],
  phase: 'initialization'
});
```

**应用场景**:
- 按标签查询记忆
- 按阶段过滤记忆

---

### 3. 记忆搜索

```javascript
// 根据关键词搜索记忆
const results = memoryStore.searchMemories('ffmedia', 'udhcpc');
```

**应用场景**:
- 快速查找相关记忆
- 支持模糊搜索

---

## 测试

### 运行测试脚本

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
node scripts/test-memory-inheritance.js
```

**测试内容**:
1. 初始化 MemoryStore
2. 添加测试记忆
3. 查询记忆
4. 生成上下文摘要
5. 测试 ContextBuilder
6. 构建任务 Prompt
7. 测试记忆去重

---

## 集成到 Stone

### 在 WakeupManager 中使用

```javascript
import ContextBuilder from './context-builder.js';

class WakeupManager {
  constructor(stone) {
    this.contextBuilder = new ContextBuilder();
  }

  async spawnAgent(agentId, task) {
    // 🔧 使用 ContextBuilder 构建增强的任务 prompt
    const enhancedTask = await this.contextBuilder.buildTaskPrompt(agentId, task);

    const result = await sessions_spawn({
      agentId: agentId,
      task: enhancedTask,  // ✅ 使用增强的任务（包含记忆）
      mode: 'session',
      thread: true,
      label: `stone-wakeup-${agentId}`,
      runTimeoutSeconds: 1800,
    });

    return result;
  }
}
```

### 在监控完成后记录记忆

```javascript
// ffmedia 完成后记录记忆
await memoryStore.addOperationMemory('ffmedia', '成功启动 4 个 RTSP 输入服务器');

// ffmedia 失败后记录记忆
await memoryStore.addFailureMemory('ffmedia', '网络配置失败：eth0 无 IP 地址');
```

---

## 总结

**记忆继承系统** 的核心价值：

1. ✅ **完整继承**：subagentN 继承所有之前失败尝试的记忆
2. ✅ **避免重复**：基于历史记忆，避免重复相同的操作
3. ✅ **从错误中学习**：记忆存储失败经验，subagent 可以学习
4. ✅ **智能决策**：基于记忆摘要，subagent 做出更智能的决策
5. ✅ **持久化存储**：记忆分层存储，长期保留关键决策
6. ✅ **性能优化**：内存缓存、增量持久化、异步清理
7. ✅ **扩展性强**：支持跨 Agent 共享、标签、搜索

**最终效果**：

```
subagent1 (失败) → 记忆存储 → subagent2 (知道 subagent1) → 记忆存储 → subagent3 (知道 subagent1 和 subagent2)
```

每个 subagent 都有完整的上下文，可以智能地继续执行任务！

---

**相关文件**:
- `modules/memory-store.js` - MemoryStore 实现
- `modules/context-builder.js` - ContextBuilder 实现
- `docs/MEMORY-INHERITANCE-SYSTEM.md` - 详细设计文档
- `scripts/test-memory-inheritance.js` - 测试脚本
- `memory/` - 记忆存储目录

**Stone Agent** 🗿
