# Session + Thread 方案实施报告

**创建时间**: 2026-03-02 17:40
**状态**: ⚠️ 部分可行，需要调整方案

---

## 📋 实施情况

### ✅ 已完成

1. **修改 WakeupManager.js**
   - 将 `mode: 'run'` 改为 `mode: 'session'`
   - 添加 `thread: true`
   - 使用固定 label 便于后续查找

2. **修改 monitor-simple.js**
   - 添加 `executeIntervention()` 函数
   - 添加 `recordSessionMapping()` 函数
   - 集成自动干预逻辑

3. **创建测试脚本**
   - test-session-thread.js

---

## ⚠️ 发现的问题

### 核心问题

**在 Node.js 脚本中，无法使用 `sessions_spawn` 工具创建 session + thread 模式的 subagent。**

### 原因分析

#### 1. sessions_spawn 工具限制

`sessions_spawn` 是一个 OpenClaw 工具，只能在 OpenClaw agent 环境中使用。

```javascript
// ✅ 在 OpenClaw agent 环境中（当前对话）
sessions_spawn({
  agentId: 'ffmedia',
  task: '...',
  mode: 'session',
  thread: true,
})

// ❌ 在 Node.js 脚本中（无法直接调用）
const { sessions_spawn } = require('...');  // 不存在这样的模块
```

#### 2. Gateway HTTP API 限制

Gateway HTTP API 只提供 `/v1/responses` 端点，用来向 Agent 发送消息，**不是创建 session**。

```bash
# ✅ 向 Agent 发送消息
curl -X POST http://127.0.0.1:18789/v1/responses \
  -H "x-openclaw-agent-id: ffmedia" \
  -d '{"model": "openclaw", "input": "消息内容"}'

# ❌ 创建 session + thread 模式的 subagent
# 没有这样的 API 端点
```

#### 3. OpenClaw CLI 限制

`openclaw agent` 命令可以运行 agent，但不支持 `mode: 'session'` 和 `thread: true` 这些高级参数。

```bash
# ✅ 运行 agent（创建新的 session）
openclaw agent --agent ffmedia --message "消息内容"

# ❌ 创建 session + thread 模式的 subagent
# openclaw agent 不支持这些参数
```

---

## 🔄 调整后的方案

### 方案 A：保持手动干预（推荐）

**工作流程**：
1. Stone 检测到问题（abort/停滞）
2. Stone 发送飞书报告，包含：
   - 问题描述
   - 调试建议
   - **明确的下一步指令**
3. 用户看到报告
4. **用户在当前对话中告诉我"继续执行"**
5. Stone 使用 `sessions_spawn` 唤醒 agent（session + thread 模式）
6. Stone 捕获完成报告，自动继续执行

**优点**：
- 完全可行
- Stone 可以使用 `sessions_spawn` 工具（在当前对话环境中）
- 可以实现 session + thread 模式
- 用户保持控制权

**缺点**：
- 需要用户手动触发第二步
- 不是完全自动化

**实施难度**：低（10 分钟）

---

### 方案 B：使用 Gateway API 的半自动化

**工作流程**：
1. Stone 检测到问题（abort/停滞）
2. Stone 使用 `openclaw agent` 命令唤醒 agent（创建新的 session）
3. Stone 通过 Gateway HTTP API `/v1/responses` 向 Agent 发送消息
4. Stone 读取 session 文件捕获完成报告
5. Stone 通过 Gateway HTTP API 继续发送新任务

**优点**：
- 可以在 Node.js 脚本中实现
- 相对自动化

**缺点**：
- **无法实现 session + thread 模式**（每次都是新的 session）
- 无法使用 `sessions_send` 继续执行
- 功能受限

**实施难度**：中（30 分钟）

---

### 方案 C：保持当前模式（monitor-only）

**工作流程**：
1. Stone 检测到问题（abort/停滞）
2. Stone 发送飞书报告
3. 用户手动干预

**优点**：
- 简单直接
- 无需修改代码

**缺点**：
- 完全手动
- 无法自动继续执行

**实施难度**：无（0 分钟）

---

## 💡 推荐方案

### 推荐方案：方案 A（保持手动干预 + session + thread）

**理由**：
1. **完全可行**：Stone 可以在当前对话环境中使用 `sessions_spawn`
2. **功能完整**：可以实现 session + thread 模式
3. **用户控制**：用户可以确认后再继续执行
4. **实施简单**：不需要修改现有代码

**实施步骤**：
1. Stone 检测到问题，发送飞书报告（已完成）
2. 报告中包含明确的下一步指令
3. 用户确认后，在当前对话中告诉我"继续执行"
4. Stone 使用 `sessions_spawn` 唤醒 agent（session + thread 模式）
5. Stone 捕获完成报告，自动继续执行

**示例对话**：
```
用户: 继续 ffmedia 的调试工作

Stone: 好的，我来唤醒 ffmedia 继续调试...

[sessions_spawn: ffmedia, mode='session', thread=true]

ffmedia: 我收到任务了，开始调试...

[ffmedia 完成任务]

Stone: 检测到 ffmedia 完成调试，分析结果...
Stone: 建议下一步：重启 RK3588 设备
Stone: 正在发送继续指令...

[sessions_send: "重启 RK3588 设备"]

ffmedia: 正在重启设备...
```

---

## 📊 方案对比

| 特性 | 方案 A（推荐） | 方案 B（半自动） | 方案 C（当前） |
|------|--------------|----------------|---------------|
| 实施难度 | 低 | 中 | 无 |
| 自动化程度 | 中（用户确认） | 高 | 低 |
| session + thread | ✅ 支持 | ❌ 不支持 | ❌ 不支持 |
| 持续执行 | ✅ 支持 | ⚠️ 部分支持 | ❌ 不支持 |
| 用户控制权 | ✅ 高 | ⚠️ 中 | ✅ 高 |
| 功能完整性 | ✅ 完整 | ⚠️ 受限 | ❌ 不支持 |

---

## 🎯 结论

### ✅ Session + Thread 模式可行，但需要调整实施方式

**核心发现**：
- `sessions_spawn` 工具只能在 OpenClaw agent 环境中使用
- Stone 可以在当前对话环境中使用 `sessions_spawn`
- 但在 Node.js 监控脚本中无法使用 `sessions_spawn`

**推荐方案**：
- **方案 A**：保持手动干预 + session + thread
- 在当前对话中使用 `sessions_spawn`
- 实现完整的 session + thread 功能

**下一步**：
1. 用户确认采用方案 A
2. 优化飞书报告格式，包含明确的下一步指令
3. 在当前对话中实现 session + thread 模式的 agent 唤醒

---

## 📝 代码修改记录

### 已修改的文件

1. `/Volumes/zhangstExtern/openclaw/workspace/stone/modules/wakeup-manager.js`
   - ✅ 将 `mode: 'run'` 改为 `mode: 'session'`
   - ✅ 添加 `thread: true`
   - ✅ 使用固定 label

2. `/Volumes/zhangstExtern/openclaw/workspace/stone/monitor-simple.js`
   - ✅ 添加 `executeIntervention()` 函数
   - ✅ 添加 `recordSessionMapping()` 函数
   - ⚠️ 依赖 `sessions_spawn` 工具（在 Node.js 中不可用）

3. `/Volumes/zhangstExtern/openclaw/workspace/stone/test-session-thread.js`
   - ⚠️ 测试脚本无法运行（依赖 `openclaw` CLI 命令）

---

## 📌 待确认问题

1. **采用哪个方案**？
   - 方案 A（推荐）：手动干预 + session + thread
   - 方案 B：半自动化（无 session + thread）
   - 方案 C：保持当前模式

2. **如果采用方案 A**：
   - 优化飞书报告格式
   - 在当前对话中实现 session + thread 模式

3. **如果采用方案 B**：
   - 实现 Gateway API 调用逻辑
   - 放弃 session + thread 功能

---

**报告时间**: 2026-03-02 17:40
**Stone Agent** 🗿
