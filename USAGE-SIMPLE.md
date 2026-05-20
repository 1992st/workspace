# Stone 监控 - 使用指南（简化版）

## 📋 概述

Stone 现在可以在 **当前 OpenClaw 会话**中运行，不需要作为独立进程。

## 🚀 运行方式

### 选项 1: 使用简化监控脚本（推荐）

在当前会话中运行：

```javascript
// 读取并执行监控脚本
import { runMonitoring } from './monitor-simple.js';
await runMonitoring();
```

这会：
1. 检查所有 Agents 状态
2. 更新 AGENT-STATES.md
3. 记录到 MONITOR-LOG.md
4. 检测需要干预的情况
5. 生成监控报告

### 选项 2: 使用现有监控流程

继续使用当前会话中的监控逻辑：
1. 读取 AGENT-STATES.md
2. 检查 session 文件
3. 生成报告
4. 检测偏离

### 选项 3: 手动干预

直接向 Agent 发送恢复指令：

```javascript
// 唤醒 ffmedia
sessions_spawn({
  agentId: 'agent:ffmedia:main',
  task: '继续执行编译和部署任务',
  model: 'glm-4.7',
  mode: 'run'
});
```

## 🎯 监控逻辑

### 状态判断

| 状态 | 条件 | 说明 |
|------|------|------|
| 🟢 Normal | 停滞 < 阈值 | 正常工作 |
| 🟡 Stopped | 停滞 ≥ 阈值 | 超过阈值，需检查 |
| 🔴 Aborted | 检测到 abort | Agent 异常退出 |
| ⚪ Unknown | 无 session 或消息 | 无法确定状态 |

### 阈值设置

| Agent | 阈值 | 优先级 |
|-------|-------|-------|
| ffmedia | 60 分钟 (1 小时) | High |
| agentmesh | 1440 分钟 (24 小时) | Medium |
| Ai-StockAssistant | 60 分钟 (1 小时) | Medium |

### 干预条件

**自动干预**（简化版只记录，不执行）：
1. Agent 状态 = Aborted
2. Agent 优先级 = High
3. 停滞时长 > 阈值

**人工干预**：
1. 检查记录的干预建议
2. 决定是否执行干预
3. 通过 sessions_spawn 唤醒 Agent

## 📊 输出文件

### AGENT-STATES.md
```markdown
| Agent | 状态 | 最后活动 | 停滞时长 | 说明 |
|-------|------|---------|---------|------|
| ffmedia | 🟢 Normal | 2026-03-02 15:00 | 5 | 正常工作 |
```

### MONITOR-LOG.md
```markdown
## 2026-03-02T15:30:00.000Z

### ffmedia
- 状态: normal
- 最后活动: 2026-03-02T15:00:00.000Z
- 停滞: 5
- 说明: Last activity 5 min ago
- Abort: 否
```

### alerts/
```
alerts/
├── ffmedia-1740935400000.json
├── agentmesh-1740936000000.json
└── Ai-StockAssistant-1740936600000.json
```

## 🔍 当前建议

### 立即行动（高优先级）
- ✅ **无需干预**：所有 Agents 状态正常
- ⏰ **定时监控**：建议每 30 分钟运行一次监控

### 待观察（中等优先级）
- ffmedia: 最后活动 04:30（11 小时前），需要确认是否正常
- agentmesh: 最后活动 05:02（10.5 小时前），需要确认编译状态
- Ai-StockAssistant: 最后活动 04:25（11.3 小时前），准备执行新任务

## 📝 下一步

1. **确认 Agent 状态**：
   ```bash
   # 检查 ffmedia
   ls -lt ~/.openclaw/agents/ffmedia/sessions/ | head -3
   
   # 检查 agentmesh
   ls -lt ~/.openclaw/agents/agentmesh/sessions/ | head -3
   
   # 检查 Ai-StockAssistant
   ls -lt ~/.openclaw/agents/Ai-StockAssistant/sessions/ | head -3
   ```

2. **手动唤醒**（如果需要）：
   ```javascript
   // 向 ffmedia 发送恢复指令
   sessions_spawn({
     agentId: 'agent:ffmedia:main',
     task: '继续执行未完成的任务',
     mode: 'run'
   });
   ```

3. **检查最新日志**：
   ```bash
   # ffmedia
   tail -50 ~/.openclaw/agents/ffmedia/sessions/*.jsonl
   
   # agentmesh
   tail -50 ~/.openclaw/agents/agentmesh/sessions/*.jsonl
   
   # Ai-StockAssistant
   tail -50 ~/.openclaw/agents/Ai-StockAssistant/sessions/*.jsonl
   ```

---

## ✅ 总结

**最完整的方案**：**选项 1（简化监控脚本）+ 人工决策**

理由：
1. ✅ Stone 在当前会话中运行，符合 OpenClaw Agent 设计
2. ✅ 不需要修改 v5.0 代码，避免导入问题
3. ✅ 检测和记录功能完整
4. ✅ 提供干预建议，由人工决策是否执行
5. ✅ 生成完整的监控报告和日志

**使用方法**：
1. 向 Stone 发送"运行监控"消息
2. Stone 检查所有 Agents 状态
3. Stone 生成报告和干预建议
4. 人工决定是否执行干预
5. 如果需要，向 Stone 发送"执行干预：ffmedia"消息

---

🗿 **Stone 监控已就绪！**
