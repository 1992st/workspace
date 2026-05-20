# ContextBuilder 使用指南

## 功能说明

**ContextBuilder** 是 Stone 的核心模块，负责为 subagent 构建完整的历史上下文。

---

## 解决的问题

### 问题场景

```
ffmedia 主 session
  ↓
subagent1 (失败 - 缺少 libffmedia.so)
  ↓
subagent2 (继续部署 - 需要知道 subagent1 做了什么)
  ↓
subagent3 (再继续 - 需要知道 subagent1 和 subagent2 做了什么)
```

**传统方式的问题**：
- ❌ subagent2 不知道 subagent1 做了什么
- ❌ subagent3 不知道 subagent1 和 subagent2 做了什么
- ❌ 可能重复执行相同的操作
- ❌ 无法从之前的错误中学习

**ContextBuilder 的解决方案**：
- ✅ 从 AGENTS.md 读取最新状态
- ✅ 从 MONITOR-LOG.md 读取所有监控记录
- ✅ 从失败 session 文件读取摘要
- ✅ 组装成完整的上下文摘要
- ✅ 在 prompt 中传递给 subagent

---

## 工作流程

### 1. Stone 检测到需要唤醒 agent

```
监控 → 检测到阻塞/停滞 → 决定唤醒 agent
```

### 2. ContextBuilder 构建上下文

```
ContextBuilder.buildTaskPrompt(agentId, task)
  ↓
├─ 读取 AGENTS.md → 当前状态
├─ 读取 MONITOR-LOG.md → 历史记录
├─ 读取失败 session → 失败尝试
└─ 组装上下文摘要
```

### 3. 增强后的 prompt 发送给 subagent

```
## 历史上下文摘要

### 当前状态
- **状态**: 🔴 阻塞
- **最后活动**: 2026-03-02 10:18
- **最后任务**: 继续测试 demo_rtsp_multi_splice

### 之前的尝试 (3 次)

#### 尝试 #1: bd6654e5
- **结果**: aborted
- **任务**: 从编译服务器下载代码...
- **错误**:
  - libffmedia.so: cannot open shared object file

#### 尝试 #2: ceb28b68
- **结果**: aborted
- **任务**: 尝试推送 libffmedia.so...
- **错误**:
  - adb: error: failed to copy

#### 尝试 #3: 62f86e1a
- **结果**: aborted
- **任务**: 检查设备状态...
- **错误**:
  - devices: offline

### 最近的错误
- libffmedia.so: cannot open shared object file
- adb: error: failed to copy
- devices: offline

---

## 你的任务

设备已恢复（adb devices 显示 device），继续之前的任务：

1. 重新部署代码到 RK3588（如果需要）
2. 启动 4 个 RTSP 服务器
3. 运行 demo_rtsp_multi_splice 测试
...

### 重要提示
- 你已经知道之前的所有失败尝试和错误
- 避免重复之前的错误操作
- 基于"历史上下文摘要"中的信息，采用不同的策略
- 如果遇到相同的问题，尝试不同的解决方法
```

---

## 使用方法

### 在 WakeupManager 中使用

```javascript
import ContextBuilder from './context-builder.js';

class WakeupManager {
  constructor(stone) {
    this.contextBuilder = new ContextBuilder();
  }

  async spawnAgent(agentId, task) {
    // 🔧 构建增强的任务 prompt
    const enhancedTask = await this.contextBuilder.buildTaskPrompt(agentId, task);

    const result = await sessions_spawn({
      agentId: agentId,
      task: enhancedTask,  // 使用增强的任务
      mode: 'session',
      thread: true,
      label: `stone-wakeup-${agentId}`,
      runTimeoutSeconds: 1800,
    });

    return result;
  }
}
```

### 在 monitor-simple.js 中使用

```javascript
import ContextBuilder from './context-builder.js';

const contextBuilder = new ContextBuilder();

async function executeIntervention(agentId, priority) {
  console.log(`\n🔄 执行干预: ${agentId}...`);

  // 构建增强的任务
  const task = '继续之前的任务';
  const enhancedTask = await contextBuilder.buildTaskPrompt(agentId, task);

  // 唤醒 agent
  const result = await sessions_spawn({
    agentId: agentId,
    task: enhancedTask,
    mode: 'run',
    label: `stone-wakeup-${agentId}`,
    runTimeoutSeconds: 1800,
  });

  return result;
}
```

---

## 配置

### 读取失败 session 的数量

默认读取最近 10 个 session。可以在 `ContextBuilder.readFailedSessions` 中修改：

```javascript
// 取最近 N 个
const recentFiles = fileStats.slice(0, N);
```

### 读取 session 摘要的行数

默认读取最后 50 行。可以在 `ContextBuilder.readSessionSummary` 中修改：

```javascript
// 取最后 N 行
const recentLines = lines.slice(-N);
```

### 读取 MONITOR-LOG.md 的记录数

默认读取最近 5 条记录。可以在 `ContextBuilder.readHistorySummary` 中修改：

```javascript
// 取最近 N 条记录
const recentSections = relevantSections.slice(-N);
```

---

## 优势

### 1. 完整的历史上下文

- ✅ subagent 知道之前所有失败的尝试
- ✅ subagent 知道之前的错误信息
- ✅ subagent 可以从错误中学习

### 2. 避免重复操作

- ✅ subagent 不会重复执行相同的失败操作
- ✅ subagent 会采用不同的策略

### 3. 智能恢复

- ✅ subagent 基于"历史上下文摘要"做出智能决策
- ✅ subagent 避免重复犯错

### 4. 持续改进

- ✅ 每次失败都会被记录
- ✅ 后续 subagent 可以学习并改进

---

## 限制

### 1. Token 限制

- ⚠️ 完整的历史上下文可能超过模型的 token 限制
- ⚠️ 需要摘要和过滤（默认已实现）

### 2. 信息丢失

- ⚠️ 摘要可能会丢失一些细节
- ⚠️ 需要在 AGENTS.md 中手动更新关键信息

### 3. 性能开销

- ⚠️ 读取多个文件和 session 可能会增加延迟
- ⚠️ 需要优化性能（使用缓存）

---

## 最佳实践

### 1. 定期更新 AGENTS.md

在 AGENTS.md 中手动更新关键信息：

```markdown
## ffmedia

### 当前状态：🔄 运行中

**最后任务**: 继续测试 demo_rtsp_multi_splice

**最新进展**:
- ✅ 设备已恢复
- ✅ 代码已部署
- 🔄 正在启动 RTSP 服务器
```

### 2. 在 MONITOR-LOG.md 中记录关键事件

Stone 会自动记录监控事件，但也可以手动添加：

```markdown
## 2026-03-02 20:50 - 自动唤醒（ffmedia）

### 触发原因
设备已恢复

### 唤醒操作
- 使用 sessions_spawn
- 包含历史上下文

### 结果
subagent 正在执行任务
```

### 3. 限制历史上下文的长度

通过修改配置来限制历史上下文的长度：

```javascript
// 只读取最近 3 个失败的 session
const recentFiles = fileStats.slice(0, 3);

// 只读取最近 20 行
const recentLines = lines.slice(-20);

// 只读取最近 3 条监控记录
const recentSections = relevantSections.slice(-3);
```

---

## 示例场景

### 场景 1：ffmedia 设备离线

```
尝试 #1: 设备 offline
  → 错误：adb devices 显示 offline

尝试 #2: 重启 ADB
  → 错误：仍然 offline

尝试 #3: 用户修复设备
  → 设备恢复 online

尝试 #4: 使用 ContextBuilder
  → subagent 知道前 3 次尝试
  → 跳过重启 ADB（已尝试过）
  → 直接继续部署代码
```

### 场景 2：agentmesh 编译错误

```
尝试 #1: Rust 编译错误
  → 错误：类型不匹配

尝试 #2: 修复类型错误
  → 错误：接口签名不匹配

尝试 #3: 修复接口签名
  → 错误：Message 重复声明

尝试 #4: 使用 ContextBuilder
  → subagent 知道前 3 次修复
  → 跳过已修复的问题
  → 继续修复新的问题
```

---

## 总结

**ContextBuilder** 是 Stone 的核心功能，确保：

1. ✅ subagent 继承之前所有失败尝试的记忆
2. ✅ subagent 避免重复操作
3. ✅ subagent 从错误中学习
4. ✅ subagent 基于历史上下文做出智能决策

**最终效果**：

```
subagent1 (失败) → subagent2 (知道 subagent1) → subagent3 (知道 subagent1 和 subagent2)
```

每个 subagent 都有完整的上下文，可以智能地继续执行任务。
