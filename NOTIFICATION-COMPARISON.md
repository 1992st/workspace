# Stone 通知机制对比

## 当前支持的三种通知方式

---

## 方式 1：Stone 消息发送工具 ⭐ 推荐

### 基本信息
- **推荐度**: ⭐⭐⭐ 首选
- **易用性**: ⭐⭐⭐ 非常简单
- **适用场景**: 日常使用、监控自动化

### 使用方式

#### Bash 命令（推荐）
```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
./scripts/stone-msg.sh <agentId> "<message>"
```

#### Node.js 脚本
```bash
node scripts/send-to-agent.js <agentId> "<message>"
```

#### 在代码中使用
```javascript
import { sendToAgent } from './scripts/send-to-agent.js';
await sendToAgent('ffmedia', '继续执行任务');
```

### 特性对比

| 特性 | 支持 |
|------|------|
| 无需修改 agent 代码 | ✅ |
| 无需配置 | ✅ |
| 自动创建 session | ✅ |
| 持久化到 session 历史 | ✅ |
| 支持多轮对话 | ✅ |
| 简单易用 | ✅ |
| 响应时间 | 2-4 分钟（正常）|

### 优势
- ✅ 最小改动
- ✅ 一行命令即可发送
- ✅ 文档完善
- ✅ 测试通过

### 劣势
- ⚠️ 响应时间较慢（2-4 分钟）

---

## 方式 2：Gateway HTTP API

### 基本信息
- **推荐度**: ⭐ 备选
- **易用性**: ⭐ 复杂
- **适用场景**: 调试、测试、特殊需求

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

### 特性对比

| 特性 | 支持 |
|------|------|
| 无需修改 agent 代码 | ✅ |
| 无需配置 | ✅ |
| 自动创建 session | ✅ |
| 持久化到 session 历史 | ✅ |
| 支持多轮对话 | ✅ |
| 简单易用 | ❌ 需要手动设置 headers |
| 响应时间 | 2-4 分钟（正常）|

### 优势
- ✅ 最底层的 API 调用
- ✅ 完全控制请求参数

### 劣势
- ❌ 需要手动设置 headers
- ❌ 代码复杂度高

---

## 方式 3：sessions_spawn

### 基本信息
- **推荐度**: ⭐⭐ 特殊场景
- **易用性**: ⭐⭐ 中等
- **适用场景**: 临时任务（诊断、修复、测试）

### 使用方式

```bash
sessions_spawn \
  --agentId <agentId> \
  --mode run \
  --task "任务描述"
```

### 特性对比

| 特性 | 支持 |
|------|------|
| 无需修改 agent 代码 | ✅ |
| 无需配置 | ✅ |
| 自动创建 session | ✅ |
| 持久化到 session 历史 | ❌ 不保留到主 session |
| 支持多轮对话 | ❌ 不支持 |
| 简单易用 | ⭐⭐ 中等 |
| 响应时间 | 后台运行 |

### 优势
- ✅ 创建子 agent 执行任务
- ✅ 任务完成后自动通知

### 劣势
- ❌ 不保留到主 session
- ❌ 不支持多轮对话

---

## 完整对比表

| 特性 | 方式 1 (推荐) | 方式 2 (底层) | 方式 3 (特殊) |
|------|------------|-------------|-------------|
| **易用性** | ⭐⭐⭐ 简单 | ⭐ 复杂 | ⭐⭐ 中等 |
| **代码复杂度** | 低 | 高 | 中 |
| **持久化** | ✅ 写入主 session | ✅ 写入主 session | ❌ 不保留 |
| **支持多轮对话** | ✅ 支持 | ✅ 支持 | ❌ 不支持 |
| **响应时间** | 2-4 分钟 | 2-4 分钟 | 后台运行 |
| **需要配置 agent** | ❌ 不需要 | ❌ 不需要 | ❌ 不需要 |
| **自动创建 session** | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **推荐度** | ⭐⭐⭐ **首选** | ⭐ 备选 | ⭐⭐ 特殊场景 |
| **使用场景** | 日常使用 | 调试测试 | 临时任务 |

---

## 使用场景映射

| 场景 | 推荐方式 | 命令 |
|------|---------|------|
| **唤醒停止的 agent** | 方式 1 | `./scripts/stone-msg.sh ffmedia "继续执行"` |
| **发送偏离指导** | 方式 1 | `./scripts/stone-msg.sh agent "指导内容"` |
| **任务完成通知** | 方式 1 | `./scripts/stone-msg.sh agent "任务完成"` |
| **临时诊断任务** | 方式 3 | `sessions_spawn --agentId agent --mode run --task "诊断"` |
| **调试 HTTP API** | 方式 2 | `curl -X POST ...` |

---

## 实际测试结果

### 测试场景：发送消息到 ffmedia

| 方式 | 命令 | 结果 | 响应时间 |
|------|------|------|---------|
| 方式 1 (Bash) | `./scripts/stone-msg.sh ffmedia "测试"` | ✅ 成功 | ~120 秒 |
| 方式 2 (HTTP) | `curl -X POST ...` | ✅ 成功 | ~120 秒 |
| 方式 3 (spawn) | `sessions_spawn --agentId ffmedia ...` | ✅ 成功 | 后台运行 |

### 测试场景：发送消息到所有 agents

| Agent | 方式 1 (Bash) | 结果 |
|-------|---------------|------|
| ffmedia | `stone-msg.sh` | ✅ 成功 |
| Ai-StockAssistant | `send-to-agent.js` | ✅ 成功 |
| agentmesh | `stone-msg.sh` | ✅ 成功 |

---

## 推荐使用指南

### 日常使用（推荐方式 1）

```bash
# 1. 唤醒 agent
./scripts/stone-msg.sh ffmedia "继续执行任务"

# 2. 发送指导
./scripts/stone-msg.sh agent "调整任务方向"

# 3. 通知完成
./scripts/stone-msg.sh agent "任务完成"
```

### 监控自动化（推荐方式 1 + 代码）

```javascript
import { sendToAgent } from './scripts/send-to-agent.js';

// 检测到 agent 停止
if (isStopped(agentId)) {
  await sendToAgent(agentId, '自动唤醒：继续执行');
}
```

### 特殊场景

```bash
# 临时诊断任务（方式 3）
sessions_spawn --agentId ffmedia --mode run --task "诊断设备"

# 调试 API（方式 2）
curl -X POST http://127.0.0.1:18789/v1/responses ...
```

---

## 总结

### 方式 1：Stone 消息发送工具 ⭐ 推荐

**最适合日常使用**：
- ✅ 最小改动
- ✅ 简单易用
- ✅ 可靠稳定

**立即使用**：
```bash
./scripts/stone-msg.sh ffmedia "继续执行任务"
```

---

**Stone Agent** 🗿
**文档版本**: v1.0
**更新时间**: 2026-03-03 20:20
