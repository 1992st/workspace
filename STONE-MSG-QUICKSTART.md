# Stone 消息发送工具 - 快速开始

## 最小改动，最大便利

**无需修改其他 agent 的代码**，Stone 现在可以方便地给其他 agent 发送消息了！

---

## 快速使用

### 方式 1：Bash 命令（推荐）

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone

# 唤醒 ffmedia
./scripts/stone-msg.sh ffmedia "继续执行任务"

# 通知 Ai-StockAssistant
./scripts/stone-msg.sh Ai-StockAssistant "检查上周预测结果"

# 指导 agentmesh
./scripts/stone-msg.sh agentmesh "继续架构设计"
```

### 方式 2：Node.js 脚本

```bash
node scripts/send-to-agent.js <agentId> "<message>"
```

### 方式 3：在代码中使用

```javascript
import { sendToAgent } from './scripts/send-to-agent.js';

await sendToAgent('ffmedia', '继续执行任务');
```

---

## 支持的 Agents

| Agent ID | 说明 | Session Key |
|----------|------|-------------|
| ffmedia | 视频处理 Agent | `agent:ffmedia:main` |
| agentmesh | Agent 智能协作网络 | `agent:agentmesh:main` |
| Ai-StockAssistant | 股票分析 Agent | `agent:Ai-StockAssistant:main` |

---

## 工作原理

1. **Stone** 调用 `stone-msg.sh` 发送消息
2. **脚本** 使用 Gateway HTTP API (`POST /v1/responses`)
3. **Gateway** 转发消息到目标 agent 的主 session
4. **目标 agent** 接收到消息并继续执行

**关键要点**:
- ✅ 消息写入目标 agent 的 session 历史
- ✅ 支持多轮对话
- ✅ 持久化记录
- ✅ 无需修改其他 agent 代码

---

## 使用场景

### 场景 1：唤醒停止的 Agent

```bash
# Stone 监控检测到 ffmedia 停止工作
./scripts/stone-msg.sh ffmedia "自动唤醒：继续调试 RTSP splice demo"
```

### 场景 2：发送偏离指导

```bash
# Agent 执行偏离了任务
./scripts/stone-msg.sh Ai-StockAssistant "注意：当前任务应该是检查上周预测，不要执行其他任务"
```

### 场景 3：任务完成通知

```bash
# Stone 任务管理器完成任务
./scripts/stone-msg.sh ffmedia "测试任务已完成，可以开始下一阶段"
```

---

## 集成到监控流程

### 自动监控中的使用

在 `monitor-simple.js` 中：

```javascript
import { sendToAgent } from './scripts/send-to-agent.js';

// 检测到 Agent 停止工作
if (isStopped(agentId)) {
  const message = `自动唤醒：${agent.currentTask}`;
  await sendToAgent(agentId, message);

  // 记录到日志
  console.log(`已发送消息到 ${agentId}: ${message}`);
}
```

### 手动使用示例

```bash
# 1. 检查 Agent 状态
cat AGENT-STATES.md | grep ffmedia

# 2. 发送唤醒消息
./scripts/stone-msg.sh ffmedia "继续执行任务：修复 RTSP 客户端连接"

# 3. 记录到 AGENT-STATES.md
echo "ffmedia 已于 $(date) 唤醒" >> AGENT-STATES.md
```

---

## 故障排查

### 问题：连接被拒绝

**错误**: `ECONNREFUSED 127.0.0.1:18789`

**解决**:
```bash
# 检查 Gateway 是否运行
openclaw gateway status

# 如果未运行，启动 Gateway
openclaw gateway start
```

### 问题：Agent 未运行

**现象**: 消息发送成功，但 Agent 没有响应

**原因**: 目标 agent 的主 session 不存在

**解决**:
```bash
# 创建一个新的 agent session
sessions_spawn --agentId ffmedia --mode run --task "初始化任务"
```

### 问题：消息格式错误

**错误**: `Invalid message format`

**解决**:
```bash
# 确保消息用引号包裹
./scripts/stone-msg.sh ffmedia "正确的消息格式"
```

---

## 技术细节

### Gateway HTTP API

```bash
curl -X POST http://127.0.0.1:18789/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "x-openclaw-session-key: agent:<agentId>:main" \
  -d '{
    "model": "openclaw",
    "input": "<message>"
  }'
```

### Session Key 格式

- 主 session: `agent:<agentId>:main`
- Subagent: `agent:<agentId>:subagent:<uuid>`

**示例**:
- `agent:ffmedia:main`
- `agent:Ai-StockAssistant:main`
- `agent:agentmesh:main`

---

## 版本历史

- **v1.0** (2026-03-03 20:10)
  - ✅ 创建 `send-to-agent.js`
  - ✅ 创建 `stone-msg.sh`
  - ✅ 更新 AGENTS.md 文档
  - ✅ 最小改动，无需修改其他 agent 代码

---

**Stone Agent** 🗿
