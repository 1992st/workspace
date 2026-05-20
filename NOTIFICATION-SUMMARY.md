# Stone 通知机制 - 更新摘要

## ✅ 已完成

Stone 现在可以给其他 agent 发送消息了！

---

## 📦 实施内容（最小改动）

### 新增文件

1. **`scripts/send-to-agent.js`** (2,212 字节)
   - Node.js 消息发送工具
   - 使用 Gateway HTTP API

2. **`scripts/stone-msg.sh`** (571 字节)
   - Bash 包装器，一行命令即可发送

3. **文档**
   - `STONE-MSG-QUICKSTART.md` - 快速开始指南
   - `STONE-MSG-IMPLEMENTATION-REPORT.md` - 实施报告
   - `AGENT-NOTIFICATION-MECHANISM.md` - 通知机制分析
   - `MONITORING-UPDATED.md` - 监控流程更新

---

## 🚀 立即使用

### 方式 1：Bash 命令（推荐）

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone

# 唤醒 ffmedia
./scripts/stone-msg.sh ffmedia "继续执行任务"

# 通知 Ai-StockAssistant
./scripts/stone-msg.sh Ai-StockAssistant "检查上周预测"

# 指导 agentmesh
./scripts/stone-msg.sh agentmesh "继续架构设计"
```

### 方式 2：Node.js 脚本

```bash
node scripts/send-to-agent.js <agentId> "<message>"
```

---

## ✅ 测试结果

| Agent | 测试 | 结果 |
|-------|------|------|
| ffmedia | ✅ 成功 | ~120 秒 |
| Ai-StockAssistant | ✅ 成功 | ~180 秒 |
| agentmesh | ✅ 成功 | ~240 秒 |

---

## 🎯 关键特性

### ✅ 无需配置

- **无需修改其他 agent 的代码**
- **无需配置或设置**
- Gateway 自动创建 session

### ✅ 简单易用

- 一行命令即可发送消息
- 支持多种调用方式
- 文档完善

### ✅ 可靠稳定

- 基于 Gateway HTTP API
- 消息持久化到 session 历史
- 支持多轮对话

---

## 📋 监控流程更新

### 旧流程（9 步）→ 新流程（10 步）

**新增步骤**：
- 第 9 步：发送消息（使用 stone-msg.sh）
- 第 10 步：更新 AGENT-STATES.md 和 MONITOR-LOG.md

### 通知方式对比

| 方法 | 推荐度 | 使用场景 |
|------|--------|---------|
| **stone-msg.sh** | ⭐⭐⭐ 首选 | 日常使用 |
| Gateway HTTP API | ⭐ 备选 | 调试测试 |
| sessions_spawn | ⭐⭐ 特殊 | 临时任务 |

---

## 💡 使用场景

### 场景 1：唤醒停止的 Agent

```bash
./scripts/stone-msg.sh ffmedia "自动唤醒：继续调试 RTSP splice demo"
```

### 场景 2：发送偏离指导

```bash
./scripts/stone-msg.sh Ai-StockAssistant "注意：当前任务应该是检查上周预测"
```

### 场景 3：任务完成通知

```bash
./scripts/stone-msg.sh ffmedia "测试任务已完成，可以开始下一阶段"
```

---

## 📁 文档

- **快速开始**: `STONE-MSG-QUICKSTART.md`
- **通知机制**: `AGENT-NOTIFICATION-MECHANISM.md`
- **监控更新**: `MONITORING-UPDATED.md`
- **实施报告**: `STONE-MSG-IMPLEMENTATION-REPORT.md`

---

## 🎉 总结

**Stone 现在可以方便地给其他 agent 发送消息了！**

- ✅ 最小改动（无需配置其他 agent）
- ✅ 简单易用（一行命令）
- ✅ 可靠稳定（持久化记录）
- ✅ 测试通过（所有 agents）

---

**Stone Agent** 🗿
**更新时间**: 2026-03-03 20:20
