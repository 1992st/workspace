# Stone Agent - Business Partner

🗿 **Stone** 是一个专业的 Business Partner Agent，负责协调和管理所有 Agents 的运行。

基于事件驱动架构，实现实时监控、自动唤醒、结果分析和继续执行。

## 📋 功能特性

### ✅ 实时监控
- 每 5 分钟查询 subagent 状态
- 自动检测异常和偏离
- 智能静默模式（正常时不打扰）

### 🔄 自动唤醒
- 检测停滞的 Agents（> 1 小时）
- 自动唤醒并重试
- 指数退避重试机制（最多 3 次）

### 🔍 结果处理
- 分析 subagent 结果
- 判断任务是否完成
- 自动生成下一步任务
- 继续执行未完成的任务

### 📊 报告和通知
- 每 30 分钟生成监控报告
- 异常自动发送到飞书群
- 详细的日志记录

## 🏗️ 架构

```
Stone (主入口)
├── EventListener (事件监听器)
│   └── 每 5 分钟查询 subagent 状态
├── WakeupManager (唤醒管理器)
│   ├── 唤醒 agent
│   ├── 等待完成
│   └── 处理结果
├── ResultHandler (结果处理器)
│   ├── 分析结果
│   ├── 判断完成
│   └── 生成下一步任务
├── StatusMonitor (状态监控器)
│   └── 周期性监控（30 分钟）
└── Storage (存储管理)
    └── 数据持久化
```

## 🚀 快速开始

### 1. 部署 Stone

详见 [部署指南](DEPLOYMENT.md)。

### 2. 发送测试消息

通过 OpenClaw 向 Stone 发送消息：

```bash
openclaw agent stone --message "测试：你好，Stone！"
```

### 3. 查看监控报告

```bash
tail -f /Volumes/zhangstExtern/openclaw/workspace/stone/MONITOR-LOG.md
```

## 📚 文档

- **快速开始**：[QUICK-START.md](QUICK-START.md)
- **部署指南**：[DEPLOYMENT.md](DEPLOYMENT.md)
- **架构文档**：[README-ARCHITECTURE.md](README-ARCHITECTURE.md)
- **实现总结**：[IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md)
- **身份文档**：[AGENTS.md](AGENTS.md)
- **SOUL**：[SOUL.md](SOUL.md)

## 🎯 工作流程

### 启动流程

```
Stone.start()
  ├─ 初始化存储
  ├─ 启动事件监听器（每 5 分钟查询）
  ├─ 启动唤醒管理器（监听 abort 事件）
  ├─ 启动结果处理器（处理完成结果）
  └─ 启动状态监控器（由 cron 触发）
```

### 监控流程

```
StatusMonitor.runMonitoring() [每 30 分钟]
  ├─ 遍历所有 agents
  ├─ 检查最后活跃时间
  ├─ 检查 subagent 状态
  ├─ 判断是否需要唤醒
  │   └─ 停滞 > 1 小时 → 唤醒
  │   └─ 有 abort → 唤醒
  ├─ 发送报告到飞书群
  └─ 记录日志
```

### 唤醒流程

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

## 📊 配置

Stone 的配置在 `core/config.js`：

```javascript
export const CONFIG = {
  workspace: '/Volumes/zhangstExtern/openclaw/workspace/stone/',

  monitoring: {
    interval: 30, // 监控间隔（分钟）
  },

  feishu: {
    groupId: 'oc_5347fa823df2385fe75516285e7c215b', // 飞书群 ID
  },

  agents: {
    ffmedia: {
      workspace: '/Users/zhangst/.openclaw/workspace/ffmedia/',
      monitoringFrequency: 'hourly',
      requirementsFile: 'requirements/ffmedia.md',
    },
    agentmesh: {
      workspace: '/Users/zhangst/.openclaw/workspace/agentmesh/',
      monitoringFrequency: 'daily',
      requirementsFile: 'requirements/agentmesh.md',
    },
    'Ai-StockAssistant': {
      workspace: '/Users/zhangst/.openclaw/workspace/Ai-StockAssistant/',
      monitoringFrequency: 'hourly',
      requirementsFile: 'requirements/ai-stock.md',
    },
  },

  subagents: {
    maxRetries: 3, // 最多重试 3 次
    waitTimeoutSeconds: 300, // 等待超时（秒）
    queryIntervalSeconds: 300, // 查询间隔（秒）
    maxConcurrent: 5, // 最大并发数
  },
};
```

## 🛠️ 故障排除

### 问题：Agent 无法启动

**解决方案**：
1. 检查 Agent 配置文件是否存在
2. 检查 OpenClaw 是否正确配置
3. 查看日志文件

### 问题：定时任务不执行

**解决方案**：
1. 检查 cron 配置
2. 检查 OpenClaw 的 cron 服务是否运行
3. 查看 cron 日志

### 问题：工具调用失败

**解决方案**：
1. 检查工具权限配置
2. 确认工具在 config.json 中启用
3. 查看错误日志

## 📈 版本历史

### v5.0 (2026-03-02) - 事件驱动架构

- ✅ 完整的事件驱动架构
- ✅ 实时监控（5 分钟粒度）
- ✅ 自动唤醒和重试
- ✅ 结果分析和继续执行
- ✅ 周期性监控（兼容旧逻辑）
- ✅ 模块化代码结构

### v4.0 (2026-03-01) - 智能静默模式

- ✅ 智能静默模式
- ✅ 自我审查和复盘机制
- ✅ 飞书群集成

### v3.0 (2026-03-01) - 重命名为 Stone

- ✅ 重命名为 Stone
- ✅ 多 Agent 联合分析
- ✅ 合并 Cron 任务

### v2.0 (2026-03-01) - 多 Agent 管理

- ✅ 多 Agent 联合分析
- ✅ 合并 Cron 任务
- ✅ 强制重新读取（无缓存）

### v1.0 (2026-03-01) - 初始版本

- ✅ 基础监控功能
- ✅ 状态跟踪
- ✅ 偏离检测

## 🤝 贡献

Stone 是一个事件驱动的 Business Partner Agent，欢迎贡献代码和提出建议！

## 📄 许可

MIT License

---

**Stone v5.0 - 事件驱动架构** 🗿
