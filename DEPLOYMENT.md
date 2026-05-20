# Stone Agent - 部署指南

## 📋 部署概述

Stone 是一个 OpenClaw Agent，需要通过 OpenClaw 的机制运行。

## 🚀 部署步骤

### 1. 确认 Agent 配置

检查 OpenClaw 的 Agent 配置文件（通常在 `~/.openclaw/agents/`）：

```bash
ls -la ~/.openclaw/agents/
```

确保存在 `stone` 目录，或者创建它：

```bash
mkdir -p ~/.openclaw/agents/stone
```

### 2. 创建 Agent 配置文件

在 `~/.openclaw/agents/stone/` 创建以下文件：

#### AGENTS.md（如果不存在）
```markdown
# AGENTS.md - Stone (Business Partner)

## 我是谁

我是 Stone，一个专业的 Business Partner，负责协调和管理所有 Agents 的运行。

## 我的角色

1. **监控和协调**
   - 监控所有 Agents 的运行状态
   - 检测偏离和异常
   - 协调多 Agent 联合执行

2. **自动唤醒**
   - 检测停滞的 Agents
   - 自动唤醒并重试
   - 继续执行未完成的任务

3. **结果处理**
   - 分析 subagent 结果
   - 判断任务是否完成
   - 生成下一步任务

## 我管理的 Agents

- ffmedia
- agentmesh
- Ai-StockAssistant
```

#### config.json
```json
{
  "id": "stone",
  "description": "Business Partner Agent - 专业的业务合作伙伴",
  "model": "zai/glm-4.7",
  "runtime": "subagent",
  "workspace": "/Volumes/zhangstExtern/openclaw/workspace/stone",
  "memory": "~/.openclaw/workspace/custom/memory/daily/",
  "tools": {
    "sessions_list": true,
    "sessions_spawn": true,
    "sessions_send": true,
    "sessions_history": true,
    "message": true,
    "memory_search": true,
    "memory_get": true,
    "read": true,
    "write": true,
    "edit": true
  }
}
```

### 3. 测试 Stone

通过 OpenClaw 向 Stone 发送测试消息：

```bash
openclaw agent stone --message "测试：你好，Stone！"
```

或者通过聊天界面发送消息给 Stone Agent。

### 4. 配置定时监控（可选）

在 OpenClaw 的 cron 配置中添加定时监控任务：

编辑 `~/.openclaw/config.json` 或相应的配置文件：

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

## 🔍 验证部署

### 1. 检查 Agent 是否可用

```bash
openclaw agent list
```

应该看到 `stone` 在列表中。

### 2. 发送测试消息

```bash
openclaw agent stone --message "测试消息"
```

应该收到 Stone 的回复。

### 3. 检查日志

检查 Stone 的运行日志：

```bash
tail -f ~/.openclaw/logs/stone.log
```

或者检查监控日志：

```bash
tail -f /Volumes/zhangstExtern/openclaw/workspace/stone/MONITOR-LOG.md
```

## 📊 运行模式

Stone 支持两种运行模式：

### 1. 消息触发模式（推荐）

Stone 通过接收消息来触发监控：

- **定时监控**：每 30 分钟通过 cron 触发
- **手动触发**：手动发送"运行监控"消息
- **事件触发**：通过事件监听器自动触发

### 2. 持续运行模式（可选）

如果需要 Stone 持续运行监听事件，可以通过 OpenClaw 的机制实现：

```bash
# 启动 Stone 持续运行
openclaw agent stone --message "启动持续监控"
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

## 📝 配置说明

### 核心配置

Stone 的核心配置在 `/Volumes/zhangstExtern/openclaw/workspace/stone/core/config.js`：

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
    // ...
  },

  subagents: {
    maxRetries: 3, // 最多重试 3 次
    waitTimeoutSeconds: 300, // 等待超时（秒）
    queryIntervalSeconds: 300, // 查询间隔（秒）
    maxConcurrent: 5, // 最大并发数
  },
};
```

### 修改配置后重启

修改配置后，需要重启 Agent：

```bash
openclaw agent stone --message "重启配置"
```

## 📚 更多文档

- **快速开始**：QUICK-START.md
- **架构文档**：README-ARCHITECTURE.md
- **实现总结**：IMPLEMENTATION-SUMMARY.md
- **身份文档**：AGENTS.md
- **SOUL**：SOUL.md

## 🤝 获取帮助

如果遇到问题，请：
1. 查看日志文件
2. 检查配置文件
3. 查看文档
4. 在飞书群提问

---

**部署成功后，Stone 将自动开始监控所有 Agents！** 🗿
