# Stone 任务管理系统 - 快速开始指南（更新版）

## 📋 文档信息

- **版本**: v2.0
- **更新日期**: 2026-03-03 11:25
- **变更说明**: 修复 OpenClaw 规范符合性问题，更新使用指南

---

## 🎯 概述

Stone 任务管理系统允许你通过 Stone 给 Agent 指派临时任务，这些任务会通过 subagent 执行，并与主线任务协调，避免冲突。

**核心特性**:
- ✅ 使用 OpenClaw 标准工具（sessions_spawn, sessions_list, sessions_history）
- ✅ Subagent 命名符合 OpenClaw 规范（UUID + label）
- ✅ 基于规则的冲突检测
- ✅ 完整的任务监控和查询

---

## 🚀 快速开始

### 1. 初始化任务系统

任务系统会在第一次使用时自动初始化，但你也可以手动初始化：

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
node task-manager.js init
```

**生成的目录结构**:
```
stone/
├── tasks/
│   ├── active/              # 活跃任务
│   ├── completed/           # 已完成任务
│   ├── failed/              # 失败任务
│   ├── archived/            # 归档任务
│   ├── task-registry.json   # 任务注册表
│   └── task-history.md     # 任务历史
```

### 2. 创建任务

```bash
node task-manager.js create "任务标题" <agentId> [priority]
```

**示例**:
```bash
# 给 ffmedia 创建一个高优先级任务
node task-manager.js create "诊断 RTSP 连接问题" ffmedia high

# 给 Ai-StockAssistant 创建一个普通优先级任务
node task-manager.js create "检查上周预测结果" Ai-StockAssistant
```

**参数说明**:
- `任务标题`: 任务的描述性标题
- `<agentId>`: Agent ID（如 ffmedia, agentmesh, Ai-StockAssistant）
- `[priority]`: 优先级（high, medium, low，默认 medium）

### 3. 查询任务

#### 查询所有任务
```bash
node task-manager.js list
```

#### 查询特定 Agent 的任务
```bash
node task-manager.js list ffmedia
```

#### 查询特定状态的任务
```bash
node task-manager.js list ffmedia running
node task-manager.js list ffmedia completed
node task-manager.js list ffmedia failed
```

### 4. 显示任务详情

```bash
node task-manager.js show <taskId>
```

**示例**:
```bash
node task-manager.js show task-20260303T02593-3wa
```

### 5. 查看统计信息

```bash
node task-manager.js stats
```

---

## 📊 任务状态

### 任务状态

| 状态 | Emoji | 说明 |
|------|-------|------|
| pending | ⏳ | 任务已创建，等待执行 |
| running | 🔄 | 任务正在执行 |
| completed | ✅ | 任务已完成 |
| failed | ❌ | 任务执行失败 |
| blocked | 🚫 | 任务被阻塞 |
| paused | ⏸️ | 任务已暂停 |
| cancelled | ⏭️ | 任务已取消 |

### 步骤状态

| 状态 | Emoji | 说明 |
|------|-------|------|
| pending | ⏳ | 步骤等待执行 |
| running | 🔄 | 步骤正在执行 |
| completed | ✅ | 步骤已完成 |
| failed | ❌ | 步骤执行失败 |
| skipped | ⏭️ | 步骤被跳过 |

---

## 🔧 OpenClaw 集成

### Subagent Session 格式

**Session ID**: `<uuid>`（OpenClaw 自动生成）

**Label**: `task:<taskId>:step:<stepId>:<description>`

**示例**:
```javascript
{
  sessionId: "123e4567-e89b-12d3-a456-426614174000",  // UUID
  label: "task:001:step:001:diagnose-network"        // 可读标签
}
```

### OpenClaw 工具使用

**创建 subagent**:
```javascript
const subagent = await sessions_spawn({
  agentId: task.agentId,
  mode: 'run',
  task: step.description,
  label: `task:${task.taskId}:step:${step.stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`
});
```

**查询 subagents**:
```javascript
const sessions = await sessions_list({ kinds: ['subagent'] });
const taskSubagents = sessions.filter(s =>
  s.label && s.label.startsWith(`task:${taskId}:`)
);
```

**查询 subagent 历史**:
```javascript
const history = await sessions_history({
  sessionKey: sessionId,
  includeTools: true
});
```

---

## 💡 使用场景

### 场景 1: 创建任务

用户通过 Stone 指派任务：
```
"Stone，给 ffmedia 指派一个任务：诊断 RTSP 连接问题"
```

Stone 处理：
1. 创建任务
2. 定义步骤（检查网络、检查设备、测试连接）
3. 执行任务（通过 subagent）
4. 报告结果

### 场景 2: 查询任务状态

用户查询：
```
"Stone，查询 ffmedia 的任务状态"
```

Stone 处理：
1. 读取任务列表
2. 显示任务详情
3. 显示步骤进度

### 场景 3: 监控任务

Stone 定期监控：
1. 检查任务状态
2. 检查 subagent 状态
3. 更新任务进度
4. 处理超时任务

---

## 📂 文件结构

```
stone/
├── tasks/
│   ├── active/              # 活跃任务
│   │   ├── task-001.json
│   │   └── task-002.json
│   ├── completed/           # 已完成任务
│   ├── failed/              # 失败任务
│   ├── archived/            # 归档任务
│   ├── task-registry.json   # 任务注册表
│   └── task-history.md     # 任务历史
├── task-manager.js          # 任务管理器
├── TASK-MANAGEMENT-DESIGN-V2.md           # 优化后的设计文档
├── TASK-MANAGEMENT-OPENCLAW-COMPLIANCE.md  # OpenClaw 规范符合性检查
├── TASK-MANAGEMENT-OPTIMIZATION-SUMMARY.md  # 优化总结
├── OPENCLAW-INTEGRATION.md  # OpenClaw 集成指南
└── ...                     # 其他文档
```

---

## 📚 详细文档

### 设计文档

- **TASK-MANAGEMENT-DESIGN-V2.md** - 优化后的设计文档（符合 OpenClaw 规范）
- **TASK-MANAGEMENT-DESIGN.md** - 初始设计文档

### 检查与优化

- **TASK-MANAGEMENT-OPENCLAW-COMPLIANCE.md** - OpenClaw 规范符合性检查
- **TASK-MANAGEMENT-OPTIMIZATION-SUMMARY.md** - 优化总结

### 集成指南

- **OPENCLAW-INTEGRATION.md** - OpenClaw 集成指南（详细）
- **Stone AGENTS.md** - 有关 Stone 的完整信息

### 实现文档

- **TASK-MANAGEMENT-IMPLEMENTATION-REPORT.md** - 实现报告
- **TASK-MANAGEMENT-SUMMARY.md** - 实现总结

---

## 🔍 常见问题

### 1. 如何查询特定任务的 subagents？

**使用 label 过滤**:
```javascript
const sessions = await sessions_list({ kinds: ['subagent'] });
const taskId = 'task-001';
const taskSubagents = sessions.filter(s =>
  s.label && s.label.startsWith(`task:${taskId}:`)
);
```

### 2. 如何检查 subagent 是否完成？

**查询历史，检查最后一条消息**:
```javascript
const history = await sessions_history({ sessionKey: sessionId });
const lastMessage = history[history.length - 1];
const content = lastMessage.message?.content || '';

if (content.includes('completed') || content.includes('✅')) {
  console.log('Completed');
}
```

### 3. Subagent Session Key 格式是什么？

**Session ID**: `<uuid>`（OpenClaw 自动生成）

**Label**: `task:<taskId>:step:<stepId>:<description>`

**示例**:
```
Session ID: 123e4567-e89b-12d3-a456-426614174000
Label: task:001:step:001:diagnose-network
```

### 4. 任务文件存储在哪里？

**Stone 工作空间**:
```
/Volumes/zhangstExtern/openclaw/workspace/stone/tasks/
```

**不是 Agent 的工作空间**:
```
❌ /Users/zhangst/.openclaw/workspace/ffmedia/tasks/
```

---

## ⚠️ 注意事项

1. **OpenClaw 规范**:
   - ✅ 使用 sessions_spawn 创建 subagent
   - ✅ 使用 sessions_list 查询 subagents
   - ✅ 使用 sessions_history 查询 subagent 状态
   - ❌ 不要使用自定义的 session key 格式

2. **Subagent 命名**:
   - ✅ 使用 label 指定可读标签
   - ✅ 格式: `task:<taskId>:step:<stepId>:<description>`
   - ⚠️ Label 最大长度建议 < 100 字符

3. **文件路径**:
   - ✅ 任务文件存储在 Stone 的工作空间
   - ❌ 不要存储在 Agent 的工作空间

4. **轮询机制**:
   - ✅ 使用轮询检查 subagent 状态
   - ✅ 设置合理的超时时间（默认 1 小时）
   - ✅ 设置合理的轮询间隔（推荐 5 秒）

---

## 🚀 下一步

1. **创建任务**: 使用 `node task-manager.js create`
2. **查询任务**: 使用 `node task-manager.js list` 和 `node task-manager.js show`
3. **监控任务**: Stone 会自动监控任务状态
4. **查看统计**: 使用 `node task-manager.js stats`

---

## 📖 相关文档

- **OpenClaw 集成指南**: `OPENCLAW-INTEGRATION.md`
- **优化后的设计文档**: `TASK-MANAGEMENT-DESIGN-V2.md`
- **OpenClaw 规范符合性检查**: `TASK-MANAGEMENT-OPENCLAW-COMPLIANCE.md`
- **优化总结**: `TASK-MANAGEMENT-OPTIMIZATION-SUMMARY.md`
- **Stone AGENTS.md**: 有关 Stone 的完整信息

---

**Stone Agent** 🗿 | 任务管理系统 v2.0 | 符合 OpenClaw 规范 ✅
