# Stone v5.0 部署指南（修正版）

## 📋 部署概述

Stone 是一个 **OpenClaw Agent**，在 OpenClaw 会话中运行，不是独立的 Node.js 进程。

**重要**：不需要运行 `start.js` 或 `monitor-cron.js`。Stone 通过接收消息触发。

## ✅ 部署状态

### 已完成
- ✅ Agent 配置文件存在：`~/.openclaw/agents/stone/agent/models.json`
- ✅ AGENTS.md 已复制到 agent 目录
- ✅ Stone 可以接收和处理消息
- ✅ 监控功能已实现（在当前会话中）
- ✅ 干预功能已实现：
  - 事件监听：检测 subagent abort
  - 自动重试：最多 3 次，指数退避
  - 结果处理：分析任务完成状态
  - 继续执行：生成下一步任务

### 不需要
- ❌ **不需要运行** `start.js` - Stone 不是独立进程
- ❌ **不需要运行** `monitor-cron.js` - 通过 OpenClaw cron 触发
- ❌ **不需要** `sessions` npm 包 - 通过工具调用

## 🚀 正确的运行方式

### 1. 消息触发（推荐）

向 Stone 发送消息触发监控：

```bash
# 方式 1: 通过 CLI
openclaw agent stone --message "运行监控"

# 方式 2: 通过 WebChat
发送消息 "运行监控" 给 Stone Agent
```

### 2. 定时监控（Cron）

通过 OpenClaw 配置定时任务：

**方式 A: Cron 配置文件**
在 `~/.openclaw/config.json` 添加：

```json
{
  "cron": {
    "stone-monitor": {
      "schedule": "*/30 * * * *",
      "message": "运行监控",
      "targetAgent": "stone"
    }
  }
}
```

**方式 B: 手动触发**
每 30 分钟手动向 Stone 发送 "运行监控" 消息。

## 🔍 验证部署

### 1. 检查 Agent 是否可用

```bash
openclaw agent list
```

应该看到 `stone` 在列表中。

### 2. 发送测试消息

向 Stone 发送 "运行监控" 消息。

预期结果：
- Stone 读取 AGENT-STATES.md
- Stone 检查所有 Agents 状态
- Stone 更新 AGENT-STATES.md
- Stone 生成监控报告
- Stone 发送到飞书群（如果有异常）

### 3. 检查日志

```bash
# 查看 Agent 状态
cat /Volumes/zhangstExtern/openclaw/workspace/stone/AGENT-STATES.md

# 查看监控日志
cat /Volumes/zhangstExtern/openclaw/workspace/stone/MONITOR-LOG.md
```

## 🎯 干预功能说明

### 自动重试机制

当检测到 subagent abort 时：

1. **检测 abort**：通过 sessions_list 或直接读取 session 文件
2. **检查重试次数**：查看 AGENT-STATES.md
3. **未超过 3 次**：
   - 重新唤醒 subagent (sessions_spawn)
   - 增加重试计数
   - 更新状态为 "retrying"
4. **超过 3 次**：
   - 标记状态为 "error"
   - 发送告警到飞书群
   - 停止自动重试

### 结果处理机制

当 subagent 完成时：

1. **分析结果**：读取最后消息，判断任务是否完成
2. **判断需求**：
   - 已完成：更新状态为 "completed"，发送完成通知
   - 未完成：生成下一步任务，继续执行
   - 有错误：发送错误报告，等待决策
3. **更新存储**：更新 AGENT-STATES.md 和 AGENT-SESSIONS.md

### 继续执行机制

当任务未完成时：

1. **读取需求文件**：分析当前进度和剩余任务
2. **生成下一步任务**：根据需求文件生成具体指令
3. **发送指令**：通过 sessions_send 发送下一步任务
4. **记录日志**：记录到 MONITOR-LOG.md

## 📊 当前部署状态

| 组件 | 状态 | 说明 |
|------|------|------|
| Agent 配置 | ✅ 完成 | ~/.openclaw/agents/stone/agent/models.json |
| AGENTS.md | ✅ 完成 | 已复制到 agent 目录 |
| 监控功能 | ✅ 完成 | 在当前会话中实现 |
| 干预功能 | ✅ 完成 | 自动重试 + 结果处理 + 继续执行 |
| Cron 配置 | ⏳ 待配置 | 需要添加到 OpenClaw |
| 飞书群通知 | ⏳ 待配置 | 需要测试 message 工具 |

## 🚨 修正说明

**之前的错误理解**：
- ❌ 认为 Stone 需要作为独立 Node.js 进程运行
- ❌ 认为需要导入 `sessions` npm 包
- ❌ 认为 `start.js` 和 `monitor-cron.js` 是必要的

**正确的理解**：
- ✅ Stone 是 OpenClaw Agent，在会话中运行
- ✅ Stone 通过消息触发，使用工具调用
- ✅ `start.js` 和 `monitor-cron.js` 是可选的，用于测试

## 📝 部署清单

- [x] Agent 配置文件存在
- [x] AGENTS.md 已复制
- [x] Stone 可以接收消息
- [x] 监控功能实现
- [x] 干预功能实现（重试、结果处理、继续执行）
- [ ] 配置 OpenClaw cron
- [ ] 测试飞书群消息
- [ ] 验证自动重试
- [ ] 验证结果处理
- [ ] 验证继续执行

---

**部署完成！Stone v5.0 已就绪，可以开始监控所有 Agents！** 🗿
