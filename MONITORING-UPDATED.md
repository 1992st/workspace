# Stone 监控流程更新通知

## 更新时间
2026-03-03 20:20

---

## 监控流程更新（10 步）

### 旧流程（9 步）

```
第 1 步：读取 AGENT-SESSIONS.md
  ↓
第 2 步：使用 subagents list 检查 Stone 启动的 subagents
  ↓
第 3 步：读取各个 Agents 的 session 文件并综合状态
  ↓
第 4 步：分析各个 Agents 的最新活动和任务进度
  ↓
第 5 步：记录 subagents 的任务结果到 MONITOR-LOG.md
  ↓
第 6 步：更新 AGENT-STATES.md
  ↓
第 7 步：检测偏离和暂停
  ↓
第 8 步：判断是否需要发送消息（智能静默）
  ↓
第 9 步：如果需要，发送偏离指导或恢复指令
```

### 新流程（10 步）⭐

```
第 1 步：读取 AGENT-SESSIONS.md
  ↓
第 2 步：使用 subagents list 检查 Stone 启动的 subagents
  ↓
第 3 步：读取各个 Agents 的 session 文件并综合状态
  ↓
第 4 步：分析各个 Agents 的最新活动和任务进度
  ↓
第 5 步：记录 subagents 的任务结果到 MONITOR-LOG.md
  ↓
第 6 步：更新 AGENT-STATES.md
  ↓
第 7 步：检测偏离和暂停
  ↓
第 8 步：判断是否需要发送消息（智能静默）
  ↓
第 9 步：如果需要，发送消息（使用 stone-msg.sh）⭐ 新增
  ↓
第 10 步：更新 AGENT-STATES.md 和 MONITOR-LOG.md ⭐ 新增
```

---

## 新增步骤详解

### 第 9 步：发送消息（使用 stone-msg.sh）

**触发条件**:
- Agent 停止工作超过阈值
- 检测到任务偏离
- 任务完成需要通知

**执行操作**:
```bash
# 1. 生成消息内容
current_task=$(grep -A 1 "最后任务:" AGENT-STATES.md | grep -v "^--$" | tail -1 | sed 's/.*: //')
wakeup_message="自动唤醒：${current_task}"

# 2. 发送消息
./scripts/stone-msg.sh <agentId> "${wakeup_message}"

# 示例
./scripts/stone-msg.sh ffmedia "自动唤醒：继续调试 RTSP splice demo"
./scripts/stone-msg.sh Ai-StockAssistant "检查上周预测结果"
./scripts/stone-msg.sh agentmesh "继续架构设计任务"
```

**等待时间**: 2-4 分钟（Gateway HTTP API 正常响应时间）

### 第 10 步：更新 AGENT-STATES.md 和 MONITOR-LOG.md

**更新内容**:
```bash
# 更新 AGENT-STATES.md
echo "ffmedia 已于 $(date) 唤醒" >> AGENT-STATES.md

# 更新 MONITOR-LOG.md
echo "已发送消息到 ffmedia: ${wakeup_message}" >> MONITOR-LOG.md
```

---

## 通知机制总结

### 当前支持的通知方式

| 方法 | 推荐度 | 使用场景 | 命令 |
|------|--------|---------|------|
| **方法 1: Stone 消息发送工具** | ⭐⭐⭐ 首选 | 日常使用 | `./scripts/stone-msg.sh <agentId> "<message>"` |
| 方法 2: Gateway HTTP API | ⭐ 备选 | 调试测试 | `curl -X POST http://127.0.0.1:18789/v1/responses ...` |
| 方法 3: sessions_spawn | ⭐⭐ 特殊 | 临时任务 | `sessions_spawn --agentId <agentId> --mode run --task "<task>"` |

### 方法 1：Stone 消息发送工具 ⭐ 推荐

**工具文件**:
- `scripts/send-to-agent.js` - Node.js 实现
- `scripts/stone-msg.sh` - Bash 包装器

**使用方式**:
```bash
# 方式 1：Bash 命令（推荐）
./scripts/stone-msg.sh ffmedia "继续执行任务"

# 方式 2：Node.js 脚本
node scripts/send-to-agent.js ffmedia "继续执行任务"

# 方式 3：在代码中使用
import { sendToAgent } from './scripts/send-to-agent.js';
await sendToAgent('ffmedia', '继续执行任务');
```

**工作原理**:
1. 使用 Gateway HTTP API (`POST /v1/responses`)
2. 自动设置 `x-openclaw-session-key: agent:<agentId>:main`
3. 消息写入目标 agent 的主 session 历史
4. 目标 agent 接收到消息并继续执行

**关键特性**:
- ✅ **无需配置**：目标 agent 不需要任何配置或代码修改
- ✅ **自动创建 session**：Gateway 会自动创建 `agent:<agentId>:main` session
- ✅ **简单易用**：一行命令即可发送消息
- ✅ **持久化**：消息记录在 agent 的 session 历史
- ✅ **支持多轮对话**：可以连续发送多条消息
- ⚠️ **响应时间**：2-4 分钟（Gateway HTTP API 正常行为）

### 测试结果

| Agent | 测试命令 | 结果 | 响应时间 |
|-------|---------|------|---------|
| ffmedia | `stone-msg.sh` | ✅ 成功 | ~120 秒 |
| Ai-StockAssistant | `send-to-agent.js` | ✅ 成功 | ~180 秒 |
| agentmesh | `stone-msg.sh` | ✅ 成功 | ~240 秒 |

**所有测试通过！**

---

## 使用场景

### 场景 1：唤醒停止的 Agent

**背景**: Stone 监控检测到 ffmedia 停止工作

**操作**:
```bash
./scripts/stone-msg.sh ffmedia "自动唤醒：继续调试 RTSP splice demo"
```

**结果**:
- 消息发送成功
- ffmedia 接收到消息并开始执行任务

### 场景 2：发送偏离指导

**背景**: Agent 执行偏离了任务

**操作**:
```bash
./scripts/stone-msg.sh Ai-StockAssistant "注意：当前任务应该是检查上周预测，不要执行其他任务"
```

**结果**:
- Agent 收到指导信息
- 调整执行方向

### 场景 3：任务完成通知

**背景**: Stone 任务管理器完成任务

**操作**:
```bash
./scripts/stone-msg.sh ffmedia "测试任务已完成，可以开始下一阶段"
```

**结果**:
- Agent 收到完成通知
- 继续下一步任务

---

## 关键发现

### 1. 无需配置其他 Agent

✅ **核心发现**：Stone 消息发送工具**无需修改其他 agent 的代码**

**证据**：
- 所有测试的 agent（ffmedia, Ai-StockAssistant, agentmesh）的 session 文件都不存在
- 但消息都成功发送
- Gateway 自动创建了新的 session

### 2. Gateway 响应时间

⚠️ **正常行为**：Gateway HTTP API 响应时间 2-4 分钟

**原因**：
- 需要启动新的 agent 进程
- 加载模型和上下文
- 处理消息

**建议**：
- 对于监控场景，设置足够长的超时时间（300 秒）
- 或者使用后台运行（`&` 符号）

### 3. 消息持久化

✅ **持久化**：所有消息都会写入 agent 的 session 历史

```bash
# 查看消息历史
cat ~/.openclaw/agents/ffmedia/sessions/*.jsonl | grep "Stone 消息"

# 或者使用 sessions_list
sessions_list | grep ffmedia
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

  // 更新 AGENT-STATES.md
  await updateAgentStates(agentId, { lastWakeup: new Date(), lastMessage: message });
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

# 4. 记录到 MONITOR-LOG.md
echo "已发送消息到 ffmedia: 继续执行任务：修复 RTSP 客户端连接" >> MONITOR-LOG.md
```

---

## 文档更新

### 新增文档

1. **AGENT-NOTIFICATION-MECHANISM.md**
   - 详细的通知机制分析
   - 三种通知方式对比
   - 使用场景映射

2. **STONE-MSG-QUICKSTART.md**
   - 快速开始指南
   - 使用示例
   - 故障排查

3. **STONE-MSG-IMPLEMENTATION-REPORT.md**
   - 实施报告
   - 测试结果
   - 优势总结

4. **MONITORING-UPDATED.md**（本文档）
   - 监控流程更新
   - 新增步骤详解
   - 集成指南

---

## 总结

### 核心优势

Stone 消息发送工具的优势：

1. **最小改动**
   - 无需修改其他 agent 的代码
   - 无需配置或设置
   - 自动创建 session

2. **简单易用**
   - 一行命令即可发送消息
   - 支持多种调用方式（Bash, Node.js, 代码）
   - 文档完善

3. **可靠稳定**
   - 基于 Gateway HTTP API
   - 消息持久化到 session 历史
   - 支持多轮对话

### 下一步行动

**立即使用**:
```bash
# 唤醒 ffmedia
./scripts/stone-msg.sh ffmedia "继续执行任务"

# 通知 Ai-StockAssistant
./scripts/stone-msg.sh Ai-StockAssistant "检查上周预测"

# 指导 agentmesh
./scripts/stone-msg.sh agentmesh "继续架构设计"
```

**集成到监控**:
- 修改 `monitor-simple.js`，使用 `stone-msg.sh` 发送消息
- 自动检测并唤醒停止的 agents

---

**Stone Agent** 🗿
**更新时间**: 2026-03-03 20:20
**版本**: v1.0
