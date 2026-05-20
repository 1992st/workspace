# Stone 任务管理系统 - 快速开始

## 概述

Stone 任务管理系统允许你通过 Stone 给 Agent 指派临时任务，这些任务会通过 subagent 执行，并与主线任务协调，避免冲突。

---

## 快速开始

### 1. 初始化任务系统

任务系统会在第一次使用时自动初始化，但你也可以手动初始化：

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/stone
node task-manager.js init
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

## 任务状态

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

## Subagent 命名规范

Stone 会自动为每个步骤创建 subagent，命名格式如下：

```
agent:<agentId>:task:<taskId>:step:<stepId>:<description>
```

**示例**:
```
agent:ffmedia:task:001:step:001:diagnose-network
agent:ffmedia:task:001:step:002:check-device
agent:ffmedia:task:001:step:003:test-rtsp
```

通过这个命名规范，你可以轻松关联所有相关 subagents，串联上下文记忆。

---

## 文件结构

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
├── TASK-MANAGEMENT-DESIGN.md           # 设计文档
└── TASK-MANAGEMENT-IMPLEMENTATION-REPORT.md  # 实现报告
```

---

## 使用场景

### 场景 1: 诊断问题

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

## 与主线任务的冲突处理

Stone 会自动检测任务与主线任务的冲突，并根据策略处理：

**冲突处理策略**:
- `parallel`: 允许同时执行
- `sequential`: 按队列顺序执行
- `pause-main`: 暂停主线任务，执行临时任务
- `pause-others`: 暂停其他任务
- `merge`: 合并相似任务
- `reject`: 拒绝执行

---

## 下一步

1. **创建任务**: 使用 `node task-manager.js create`
2. **查询任务**: 使用 `node task-manager.js list` 和 `node task-manager.js show`
3. **监控任务**: Stone 会自动监控任务状态
4. **查看统计**: 使用 `node task-manager.js stats`

---

## 详细文档

- **设计文档**: `TASK-MANAGEMENT-DESIGN.md`
- **实现报告**: `TASK-MANAGEMENT-IMPLEMENTATION-REPORT.md`
- **Stone AGENTS.md**: 有关 Stone 的完整信息

---

**Stone Agent** 🗿 | 任务管理系统 v1.0
