# Stone Agent - 事件驱动架构

## 📋 概述

Stone 是一个专业的 Business Partner Agent，负责协调和管理所有 Agents 的运行。基于事件驱动架构，实现实时监控、自动唤醒、结果分析和继续执行。

## 🏗️ 架构设计

### 核心模块

```
stone/
├── core/                    # 核心模块
│   ├── index.js            # 主入口（Stone 类）
│   ├── config.js           # 配置管理
│   └── utils.js            # 工具函数
│
├── modules/                 # 功能模块
│   ├── event-listener.js   # 事件监听器（实时检测 subagent 状态）
│   ├── wakeup-manager.js   # 唤醒管理器（唤醒 agent、等待完成、处理结果）
│   ├── result-handler.js  # 结果处理器（分析结果、判断完成、生成下一步任务）
│   └── status-monitor.js   # 状态监控器（周期性监控，兼容旧逻辑）
│
├── storage/                 # 存储管理
│   └── index.js           # 存储接口（读写 AGENT-STATES.md、日志等）
│
├── start.js                # 主启动脚本
├── monitor-cron.js        # 监控 cron 脚本（30 分钟周期）
│
└── AGENTS.md               # Stone 身份和职责
```

## 🔄 工作流程

### 1. 启动流程

```
Stone.start()
  ├─ 初始化存储
  ├─ 启动事件监听器
  │   └─ 每 5 分钟查询 subagent 状态（sessions_list）
  ├─ 启动唤醒管理器
  │   └─ 监听 abort 事件，自动重试
  ├─ 启动结果处理器
  │   └─ 处理 subagent 完成结果
  └─ 启动状态监控器
      └─ 周期性监控（由 cron 触发）
```

### 2. 监控流程

```
StatusMonitor.runMonitoring()  [每 30 分钟]
  ├─ 遍历所有 agents
  ├─ 检查最后活跃时间
  ├─ 检查 subagent 状态
  ├─ 判断是否需要唤醒
  │   └─ 停滞 > 1 小时 → 唤醒
  │   └─ 有 abort → 唤醒
  ├─ 发送报告到飞书群
  └─ 记录日志
```

### 3. 唤醒流程

```
WakeupManager.wakeupAndMonitor(agentId, task)
  ├─ 唤醒 subagent (sessions_spawn)
  ├─ 等待完成 (sessions_history 轮询)
  │   └─ 每 10 秒查询一次，最多 5 分钟
  ├─ 处理结果
  │   ├─ 完成 → ResultHandler.handleResult
  │   ├─ 超时 → 发送告警
  │   └─ 错误 → 发送告警
  └─ 返回结果
```

### 4. 事件监听流程

```
EventListener.start()
  ├─ 每 5 分钟查询 subagent 状态
  ├─ 检测 abort
  │   └─ 触发 onSubagentAbort 事件
  │       └─ WakeupManager.handleSubagentAbort
  │           ├─ 检查重试次数
  │           ├─ 未超过 3 次 → 重新唤醒
  │           └─ 超过 3 次 → 发送告警
  └─ 检测完成
      └─ 触发 onSubagentEnd 事件
          └─ ResultHandler.handleResult
              ├─ 判断是否完成
              ├─ 完成 → 发送完成通知
              └─ 未完成 → 继续执行
```

### 5. 结果处理流程

```
ResultHandler.handleResult(agentId, lastMessage)
  ├─ 分析结果
  │   ├─ 读取需求文件
  │   ├─ 判断是否完成
  │   ├─ 判断是否需要继续
  │   ├─ 检查是否有阻塞
  │   └─ 检查是否有错误
  ├─ 完成
  │   ├─ 更新 Agent 状态
  │   ├─ 发送完成通知
  │   └─ 记录到存储
  └─ 未完成
      ├─ 生成下一步任务
      ├─ 唤醒 agent 继续执行
      └─ 记录到存储
```

## 🎯 核心特性

### 1. 事件驱动

- **实时检测**：每 5 分钟查询 subagent 状态
- **事件触发**：abort、完成、错误都会触发事件
- **自动重试**：最多 3 次，指数退避

### 2. 自动化

- **自动唤醒**：停滞 > 1 小时自动唤醒
- **自动重试**：abort 自动重试
- **自动继续**：任务未完成自动继续执行

### 3. 容错性

- **超时处理**：5 分钟超时，发送告警
- **错误处理**：捕获所有异常，记录日志
- **重试机制**：最多 3 次重试，失败后告警

### 4. 监控报告

- **周期监控**：每 30 分钟生成监控报告
- **飞书群通知**：异常自动发送到飞书群
- **日志记录**：所有操作记录到文件

## 📊 配置说明

### config.js

```javascript
export const CONFIG = {
  workspace: '/Volumes/zhangstExtern/openclaw/workspace/stone/',

  monitoring: {
    interval: 30, // 分钟
  },

  feishu: {
    groupId: 'oc_5347fa823df2385fe75516285e7c215b',
  },

  agents: {
    ffmedia: {
      workspace: '/Users/zhangst/.openclaw/workspace/ffmedia/',
      monitoringFrequency: 'hourly',
      requirementsFile: 'requirements/ffmedia.md',
    },
    // ...
  },

  subagents: {
    maxRetries: 3, // 最多重试 3 次
    waitTimeoutSeconds: 300, // 等待超时 5 分钟
    queryIntervalSeconds: 300, // 查询间隔 5 分钟
    maxConcurrent: 5, // 最大并发 5 个
  },
};
```

## 🚀 使用方法

### 1. 启动 Stone（持续运行）

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
node start.js
```

### 2. 手动触发监控

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
node monitor-cron.js
```

### 3. 定时监控（Cron）

在 OpenClaw 配置中添加 cron 任务：

```json
{
  "cron": {
    "stone-monitor": {
      "schedule": "*/30 * * * *",
      "command": "cd /Volumes/zhangstExtern/openclaw/workspace/stone && node monitor-cron.js"
    }
  }
}
```

## 📈 数据流

```
Agent (ffmedia)
  ↓ (sessions_spawn)
Subagent (agent:ffmedia:subagent:xxx)
  ↓ (执行任务)
Stone 事件监听器
  ↓ (检测 abort/完成)
Stone 唤醒管理器
  ↓ (重试/等待完成)
Stone 结果处理器
  ↓ (分析结果)
继续执行 or 完成通知
  ↓
飞书群 / 日志文件
```

## 🎨 状态机

```
Agent 状态:
  - unknown → running → completed
  - running → abort → retry (max 3) → error
  - running → timeout → error

Subagent 状态:
  - waiting → running → completed
  - waiting → running → aborted → retry
  - waiting → running → error
  - waiting → running → timeout
```

## 🔧 调试

### 查看日志

```bash
# 查看监控日志
tail -f /Volumes/zhangstExtern/openclaw/workspace/stone/MONITOR-LOG.md

# 查看 Agent 状态
cat /Volumes/zhangstExtern/openclaw/workspace/stone/AGENT-STATES.md

# 查看告警
ls -la /Volumes/zhangstExtern/openclaw/workspace/stone/alerts/
```

### 手动测试

```javascript
import { getStone } from './core/index.js';

const stone = getStone();
await stone.start();

// 手动触发监控
await stone.statusMonitor.runMonitoring();

// 手动唤醒 agent
await stone.wakeupManager.wakeupAndMonitor('ffmedia', '测试任务');
```

## 📝 待办事项

- [ ] 实现真正的 lifecycle 事件监听（替代 sessions_list 轮询）
- [ ] 实现 agent.wait 阻塞等待（替代 sessions_history 轮询）
- [ ] 增加飞书群消息发送
- [ ] 增加自我审查和复盘功能
- [ ] 增加冲突检测和解决功能
- [ ] 增加性能监控和优化

## 🤝 贡献

Stone 是一个事件驱动的 Business Partner Agent，欢迎贡献代码和提出建议！

## 📄 许可

MIT License
