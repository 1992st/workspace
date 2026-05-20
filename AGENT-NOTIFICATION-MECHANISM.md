# Agent 通知机制分析

## 当前通知方式

Stone 支持多种给其他 agent 发送消息的方式：

---

## 方法 1：Stone 消息发送工具 ⭐ 推荐（最小改动）

### 工具文件
- `scripts/send-to-agent.js` - Node.js 实现（底层）
- `scripts/stone-msg.sh` - Bash 包装器（推荐）

### 使用方式

#### 方式 1：Bash 命令（推荐）
```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
./scripts/stone-msg.sh <agentId> "<message>"
```

**示例**:
```bash
./scripts/stone-msg.sh ffmedia "继续执行任务"
./scripts/stone-msg.sh Ai-StockAssistant "检查上周预测"
./scripts/stone-msg.sh agentmesh "继续架构设计"
```

#### 方式 2：Node.js 脚本
```bash
node scripts/send-to-agent.js <agentId> "<message>"
```

#### 方式 3：在代码中使用
```javascript
import { sendToAgent } from './scripts/send-to-agent.js';

await sendToAgent('ffmedia', '继续执行任务');
```

### 工作原理
1. **Stone** 调用 `stone-msg.sh` 发送消息
2. **脚本** 使用 Gateway HTTP API (`POST /v1/responses`)
3. **Gateway** 转发消息到目标 agent 的主 session
4. **目标 agent** 接收到消息并继续执行

### 关键要点
- ✅ **自动创建 session**：如果 agent 的 main session 不存在，Gateway 会自动创建
- ✅ **无需配置**：目标 agent 不需要任何配置或代码修改
- ✅ **持久化**：消息记录在 agent 的 session 历史
- ✅ **支持多轮对话**：可以连续发送多条消息
- ⚠️ **响应时间**：2-4 分钟（Gateway HTTP API 正常行为）

### 适用场景
- ✅ 唤醒停止的 agent
- ✅ 发送偏离指导
- ✅ 任务完成通知
- ✅ 监控中的自动通知

### 测试结果
| Agent | 测试 | 结果 |
|-------|------|------|
| ffmedia | stone-msg.sh | ✅ 成功（~120 秒）|
| Ai-StockAssistant | send-to-agent.js | ✅ 成功（~180 秒）|
| agentmesh | stone-msg.sh | ✅ 成功（~240 秒）|

---

## 方法 2：Gateway HTTP API（底层）

### 使用方式
```bash
curl -X POST http://127.0.0.1:18789/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <GATEWAY_TOKEN>" \
  -H "x-openclaw-session-key: agent:<agentId>:main" \
  -d '{
    "model": "openclaw",
    "input": "唤醒消息内容"
  }'
```

### 关键要点
- ✅ 最底层的 API 调用
- ✅ 完全控制请求参数
- ⚠️ 需要手动设置 headers
- ⚠️ 代码复杂度高

### 适用场景
- ⚠️ 调试和测试
- ⚠️ 特殊需求（非标准场景）

---

## 方法 3：sessions_spawn（创建 Subagent）

### 使用方式
```bash
sessions_spawn \
  --agentId <agentId> \
  --mode run \
  --task "任务描述"
```

### 关键要点
- ✅ 创建子 agent 执行任务
- ✅ 任务完成后自动通知
- ❌ 不保留到主 session
- ❌ 不支持多轮对话

### 适用场景
- ⚠️ 临时任务（诊断、修复、测试）
- ⚠️ 持续解决问题（多步骤任务）

---

## 通知方式对比

| 特性 | 方法 1（推荐）| 方法 2（底层）| 方法 3（subagent）|
|------|------------|-------------|----------------|
| 易用性 | ⭐⭐⭐ 简单 | ⭐ 复杂 | ⭐⭐ 中等 |
| 代码复杂度 | 低 | 高 | 中 |
| 持久化 | ✅ 写入主 session | ✅ 写入主 session | ❌ 不保留 |
| 支持多轮对话 | ✅ 支持 | ✅ 支持 | ❌ 不支持 |
| 响应时间 | 2-4 分钟 | 2-4 分钟 | 后台运行 |
| 需要配置 agent | ❌ 不需要 | ❌ 不需要 | ❌ 不需要 |
| 自动创建 session | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **推荐度** | ⭐⭐⭐ **首选** | ⭐ 备选 | ⭐⭐ 特殊场景 |

---

## 当前通知机制总结

### Stone 监控中的使用

**监控流程中的通知步骤**:
1. 检测到 Agent 需要唤醒或指导
2. 生成通知消息
3. 使用 `stone-msg.sh` 发送消息
4. 更新 AGENT-STATES.md 记录操作
5. 在 MONITOR-LOG.md 记录消息内容

**示例代码**:
```bash
# 1. 生成消息
current_task=$(grep -A 1 "最后任务:" AGENT-STATES.md | grep -v "^--$" | tail -1 | sed 's/.*: //')
wakeup_message="自动唤醒：${current_task}"

# 2. 发送消息
./scripts/stone-msg.sh ffmedia "${wakeup_message}"

# 3. 记录操作
echo "ffmedia 已于 $(date) 唤醒" >> AGENT-STATES.md
echo "已发送消息到 ffmedia: ${wakeup_message}" >> MONITOR-LOG.md
```

### 消息持久化

所有消息都会持久化到 agent 的 session 历史：

```bash
# 查看消息历史
cat ~/.openclaw/agents/ffmedia/sessions/*.jsonl | grep "Stone 消息"

# 或者使用 sessions_list
sessions_list | grep ffmedia
```

---

## 关键发现

### 1. 自动创建 Session

✅ **无需配置**：Gateway 会自动创建 `agent:<agentId>:main` session

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

### 3. 支持的 Agents

当前支持的所有 agents：
- `ffmedia` - 视频处理 Agent
- `agentmesh` - Agent 智能协作网络
- `Ai-StockAssistant` - 股票分析 Agent

---

## 使用场景映射

| 场景 | 推荐方法 | 命令 |
|------|---------|------|
| 唤醒停止的 agent | 方法 1 | `./scripts/stone-msg.sh ffmedia "继续执行"` |
| 发送偏离指导 | 方法 1 | `./scripts/stone-msg.sh agent "指导内容"` |
| 任务完成通知 | 方法 1 | `./scripts/stone-msg.sh agent "任务完成"` |
| 临时诊断任务 | 方法 3 | `sessions_spawn --agentId agent --mode run --task "诊断"` |
| 调试 HTTP API | 方法 2 | `curl -X POST ...` |

---

## 更新后的监控流程

### Stone 定期监控（更新版）

```
第 1 步：读取 AGENT-SESSIONS.md
  ↓
第 2 步：检查 subagents list
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

### 消息发送流程（新增）

```
监控检测到 Agent 需要唤醒或指导
  ↓
1. 生成消息内容
   - 从 AGENT-STATES.md 读取当前任务
   - 生成唤醒消息或指导消息
  ↓
2. 使用 stone-msg.sh 发送消息
   - 调用 `./scripts/stone-msg.sh <agentId> "<message>"`
   - 等待 Gateway 响应（2-4 分钟）
  ↓
3. 记录操作
   - 更新 AGENT-STATES.md（记录唤醒时间）
   - 更新 MONITOR-LOG.md（记录消息内容）
  ↓
4. 继续监控
```

---

## 总结

### 核心优势

Stone 消息发送工具（方法 1）的优势：

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
**文档版本**: v1.0
**更新时间**: 2026-03-03 20:20
