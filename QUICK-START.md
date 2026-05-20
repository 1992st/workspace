# Stone Agent - 快速启动指南

## 🚀 快速开始

### 1. 测试 Stone

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
node test.js
```

**预期输出**：
```
==================================================
  🗿 Stone Agent - 测试
==================================================

✅ 获取 Stone 实例

📊 配置:
  Workspace: /Volumes/zhangstExtern/openclaw/workspace/stone/
  Agents: ffmedia, agentmesh, Ai-StockAssistant
  Feishu Group: oc_5347fa823df2385fe75516285e7c215b

💾 存储初始化...
✅ 存储初始化成功

📊 读取 Agent 状态:
  ffmedia: 未知 (未知)
  agentmesh: 未知 (未知)
  Ai-StockAssistant: 未知 (未知)

==================================================
  ✅ 测试完成
==================================================
```

### 2. 启动 Stone（持续运行）

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
node start.js
```

**预期输出**：
```
==================================================
  🗿 Stone Agent - 启动
==================================================
  时间: 2026-03-02 14:00:00
==================================================
✅ 存储初始化完成
✅ 事件监听器已启动
✅ 唤醒管理器已启动
✅ 结果处理器已启动
✅ 状态监控器已启动

==================================================
  🗿 Stone Agent - 运行中
==================================================
  监控 Agents: ffmedia, agentmesh, Ai-StockAssistant
==================================================

[2026-03-02 14:00:10] 📊 查询 subagent 状态...
  找到 0 个 subagents

💤 Stone 保持运行中... (Ctrl+C 退出)
```

### 3. 手动触发监控

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
node monitor-cron.js
```

**预期输出**：
```
========================================
  Stone - 监控 Cron 任务
========================================

时间: 2026-03-02T06:00:00.000Z

发送监控请求到 Stone Agent...
✅ 监控请求已发送

发送通知到飞书群...
✅ 飞书群通知已发送

========================================
  任务完成
========================================
```

## 📋 配置说明

### 编辑配置文件

打开 `core/config.js`：

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

## 🔍 查看日志

### 1. 监控日志

```bash
tail -f MONITOR-LOG.md
```

### 2. Agent 状态

```bash
cat AGENT-STATES.md
```

### 3. 告警记录

```bash
ls -la alerts/
cat alerts/ffmedia-abort-*.md
```

## 🎯 常见操作

### 1. 添加新的 Agent

1. 编辑 `core/config.js`，在 `agents` 中添加新 agent：
```javascript
agents: {
  'new-agent': {
    workspace: '/path/to/workspace/',
    monitoringFrequency: 'hourly',
    requirementsFile: 'requirements/new-agent.md',
  },
}
```

2. 运行 `update-states.js` 更新 AGENT-STATES.md：
```bash
node update-states.js
```

### 2. 修改监控间隔

编辑 `core/config.js`：
```javascript
monitoring: {
  interval: 60, // 改为 60 分钟
},
```

### 3. 修改重试次数

编辑 `core/config.js`：
```javascript
subagents: {
  maxRetries: 5, // 改为 5 次重试
},
```

## 🛠️ 故障排除

### 问题：Stone 启动失败

**解决方案**：
1. 检查 Node.js 版本（需要 v18+）
2. 检查文件权限
3. 查看错误日志

### 问题：事件监听器没有响应

**解决方案**：
1. 检查 `sessions_list` 工具是否可用
2. 检查网络连接
3. 查看控制台日志

### 问题：自动重试不工作

**解决方案**：
1. 检查 `maxRetries` 配置
2. 检查 `sessions_spawn` 工具是否可用
3. 查看 abort 记录

### 问题：飞书群没有收到消息

**解决方案**：
1. 检查 `groupId` 配置
2. 检查飞书群权限
3. 查看消息发送日志

## 📊 性能优化

### 1. 降低查询频率

编辑 `core/config.js`：
```javascript
subagents: {
  queryIntervalSeconds: 600, // 改为 10 分钟
},
```

### 2. 减少并发数

编辑 `core/config.js`：
```javascript
subagents: {
  maxConcurrent: 3, // 改为 3 个并发
},
```

### 3. 缩短等待超时

编辑 `core/config.js`：
```javascript
subagents: {
  waitTimeoutSeconds: 180, // 改为 3 分钟
},
```

## 📚 更多文档

- **架构文档**：README-ARCHITECTURE.md
- **实现总结**：IMPLEMENTATION-SUMMARY.md
- **身份文档**：AGENTS.md
- **SOUL**：SOUL.md

## 🤝 获取帮助

如果遇到问题，请：
1. 查看日志文件
2. 检查配置文件
3. 查看文档
4. 提交 Issue

---

**祝使用愉快！** 🗿
