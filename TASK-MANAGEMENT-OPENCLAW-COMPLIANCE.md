# Stone 任务管理系统 - OpenClaw 规范符合性检查与优化

## 📋 检查日期

2026-03-03 11:05

---

## 🔍 检查内容

### 1. OpenClaw 规范检查

#### 1.1 Subagent Session Key 格式

**当前设计**（问题 ⚠️）:
```
agent:<agentId>:task:<taskId>:step:<stepId>:<description>
```

**OpenClaw 规范**（正确 ✅）:
```
agent:<agentId>:subagent:<uuid>
```

**参考**: AGENTS.md
```markdown
| 特性 | Main Agents | Subagents |
|------|-------------|-----------|
| Session 格式 | `agent:<agentId>:main` | `agent:<agentId>:subagent:<uuid>` |
```

**问题**:
- ❌ OpenClaw 不支持自定义的 session key 格式
- ❌ Session key 是由 OpenClaw 自动生成的 UUID
- ❌ 无法通过 session key 查询 subagents（假设的格式）

**解决方案**:
```javascript
// ✅ 使用 label 参数指定可读标签
const subagent = await sessions_spawn({
  agentId: task.agentId,
  mode: 'run',
  task: step.description,
  label: `task:${task.taskId}:step:${step.stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`
});

// 返回值:
// {
//   sessionId: "123e4567-e89b-12d3-a456-426614174000",  // 自动生成的 UUID
//   label: "task:001:step:001:diagnose-network"        // 可读标签
// }
```

#### 1.2 Subagent 查询方式

**当前设计**（问题 ⚠️）:
```javascript
// ❌ 假设可以使用 session key 格式查询 subagents
const subagents = await subagents({
  action: 'list',
  filter: `agent:${agentId}:task:${taskId}:*`
});
```

**OpenClaw 规范**（正确 ✅）:
```javascript
// ✅ 使用 sessions_list 或 sessions_history 查询
const sessions = await sessions_list({
  kinds: ['subagent'],
  activeMinutes: 30
});

// 或者使用 sessions_history 查询特定 session
const history = await sessions_history({
  sessionKey: subagent.sessionId,
  includeTools: true
});
```

**问题**:
- ❌ subagents list 工具不支持自定义 session key 格式
- ❌ 需要通过 sessions_list 查询所有 sessions，然后过滤

**解决方案**:
```javascript
// ✅ 在任务文件中记录 subagent 的 sessionId 和 label
step.subagent = {
  sessionId: subagent.sessionId,  // OpenClaw 生成的 UUID
  label: subagent.label,          // 可读标签
  createdAt: new Date().toISOString()
};

// ✅ 查询时通过 taskId 匹配 label
const subagents = await sessions_list({ kinds: ['subagent'] });
const taskSubagents = subagents.filter(s =>
  s.label && s.label.startsWith(`task:${taskId}:`)
);
```

#### 1.3 Subagent 等待机制

**当前设计**（问题 ⚠️）:
```javascript
// ❌ 假设有一个 waitForSubagent 函数
const result = await waitForSubagent(subagent.sessionKey);
```

**OpenClaw 规范**（正确 ✅）:
```javascript
// ✅ 使用轮询机制检查 subagent 状态
async function waitForSubagent(sessionId, timeout = 3600000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const history = await sessions_history({
      sessionKey: sessionId,
      includeTools: true
    });

    // 检查是否有完成标记
    const lastMessage = history[history.length - 1];
    if (lastMessage && lastMessage.message) {
      const content = lastMessage.message.message?.content || lastMessage.message.content;

      if (content.includes('completed') ||
          content.includes('finished') ||
          content.includes('done') ||
          content.includes('✅')) {
        return { success: true, output: content };
      }

      if (content.includes('failed') ||
          content.includes('error') ||
          content.includes('❌')) {
        return { success: false, output: content };
      }
    }

    // 等待 5 秒后重试
    await new Promise(resolve => setTimeout(resolve, 5000));
  }

  return { success: false, output: 'Timeout' };
}
```

#### 1.4 文件路径规范

**当前设计**（问题 ⚠️）:
```
stone/
└── tasks/
    ├── active/
    ├── completed/
    └── ...
```

**OpenClaw 规范**（正确 ✅）:
```
stone/                              # Stone 的工作空间
└── tasks/                          # 任务目录
    ├── active/                      # 活跃任务
    ├── completed/                   # 已完成任务
    ├── failed/                      # 失败任务
    ├── archived/                    # 归档任务
    ├── task-registry.json           # 任务注册表
    └── task-history.md             # 任务历史
```

**问题**:
- ✅ 文件路径实际上是正确的
- ⚠️ 需要确保任务文件存储在 Stone 的工作空间，而不是 Agent 的工作空间

**解决方案**:
```javascript
// ✅ 使用 Stone 的工作空间路径
const TASK_DIR = path.join(STONE_WORKSPACE, 'tasks');

// ❌ 不要使用 Agent 的工作空间
const AGENT_TASK_DIR = path.join(AGENT_WORKSPACE, 'tasks');  // 错误
```

#### 1.5 工具使用规范

**当前设计**（问题 ⚠️）:
```javascript
// ❌ 使用 exec 工具执行命令
const result = await exec('subagents action=list');
```

**OpenClaw 规范**（正确 ✅）:
```javascript
// ✅ 使用 sessions_list 工具
const sessions = await sessions_list({
  kinds: ['subagent'],
  activeMinutes: 30
});

// ✅ 使用 sessions_history 工具
const history = await sessions_history({
  sessionKey: sessionId,
  includeTools: true
});
```

**问题**:
- ❌ subagents list 工具可能不存在或不可用
- ❌ 应该使用标准的 sessions_list 和 sessions_history 工具

**解决方案**:
```javascript
// ✅ 使用 OpenClaw 的标准工具
import { sessions_list, sessions_history, sessions_spawn } from 'openclaw';

// 查询 subagents
const subagents = await sessions_list({ kinds: ['subagent'] });

// 查询 subagent 历史
const history = await sessions_history({
  sessionKey: sessionId,
  includeTools: true
});

// 创建 subagent
const subagent = await sessions_spawn({
  agentId: task.agentId,
  mode: 'run',
  task: step.description,
  label: `task:${task.taskId}:step:${step.stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`
});
```

---

### 2. 设计优化建议

#### 2.1 优化 Subagent 命名

**当前设计**:
```
Subagent Session Key: agent:<agentId>:task:<taskId>:step:<stepId>:<description>
```

**优化后**:
```
Subagent Session ID: <uuid>（OpenClaw 自动生成）
Subagent Label: task:<taskId>:step:<stepId>:<description>
```

**实现**:
```javascript
// 创建 subagent 时指定 label
const subagent = await sessions_spawn({
  agentId: task.agentId,
  mode: 'run',
  task: `
任务上下文：
- 任务 ID: ${task.taskId}
- 任务标题: ${task.title}
- 任务描述: ${task.description}

当前步骤：
- 步骤 ID: ${step.stepId}
- 步骤标题: ${step.title}
- 步骤描述: ${step.description}

请执行此步骤，并在完成后报告结果。
  `.trim(),
  label: `task:${task.taskId}:step:${step.stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`
});

// 记录到任务文件
step.subagent = {
  sessionId: subagent.sessionId,
  label: subagent.label,
  createdAt: new Date().toISOString()
};
```

**优势**:
- ✅ 符合 OpenClaw 规范
- ✅ 使用标准工具
- ✅ 通过 label 串联上下文
- ✅ 不依赖自定义 session key 格式

#### 2.2 优化 Subagent 查询

**当前设计**:
```javascript
// ❌ 使用自定义 session key 格式查询
const subagents = await subagents({
  action: 'list',
  filter: `agent:${agentId}:task:${taskId}:*`
});
```

**优化后**:
```javascript
// ✅ 通过 label 查询
async function getTaskSubagents(taskId) {
  const sessions = await sessions_list({ kinds: ['subagent'] });
  const taskSubagents = sessions.filter(s =>
    s.label && s.label.startsWith(`task:${taskId}:`)
  );
  return taskSubagents;
}

// ✅ 通过 sessionId 查询（记录在任务文件中）
async function getStepSubagent(task, step) {
  if (step.subagent && step.subagent.sessionId) {
    const history = await sessions_history({
      sessionKey: step.subagent.sessionId,
      includeTools: true
    });
    return history;
  }
  return null;
}
```

**优势**:
- ✅ 使用标准工具
- ✅ 支持灵活查询
- ✅ 不依赖自定义格式

#### 2.3 优化任务文件结构

**当前设计**:
```json
{
  "taskId": "task-001",
  "steps": [
    {
      "stepId": "001",
      "subagent": {
        "sessionKey": "agent:ffmedia:task:001:step:001:diagnose-network",  // ❌ 错误
        ...
      }
    }
  ]
}
```

**优化后**:
```json
{
  "taskId": "task-001",
  "steps": [
    {
      "stepId": "001",
      "subagent": {
        "sessionId": "123e4567-e89b-12d3-a456-426614174000",  // ✅ 正确
        "label": "task:001:step:001:diagnose-network",      // ✅ 正确
        "createdAt": "2026-03-03T10:30:00.000Z",
        "startedAt": "2026-03-03T10:30:00.000Z",
        "completedAt": "2026-03-03T10:35:00.000Z",
        "status": "completed",
        "result": "网络配置正常，eth0 有 IP 192.168.150.120",
        "tokens": 12500,
        "duration": 300  // 5 分钟
      }
    }
  ]
}
```

**优势**:
- ✅ 符合 OpenClaw 规范
- ✅ 记录完整的 subagent 信息
- ✅ 支持后续查询和分析

#### 2.4 优化冲突检测

**当前设计**:
```javascript
// ❌ 使用 LLM 分析冲突
const conflicts = await detectConflicts(task, existingTasks, mainGoal);
```

**优化后**:
```javascript
// ✅ 基于规则的冲突检测
async function detectConflicts(task, existingTasks, mainGoal) {
  const conflicts = [];

  // 1. 检测任务标题是否重复
  const duplicateTitle = existingTasks.find(t =>
    t.title === task.title && t.status !== 'completed'
  );
  if (duplicateTitle) {
    conflicts.push({
      type: 'duplicate-title',
      taskId: duplicateTitle.taskId,
      severity: 'medium',
      suggestion: '任务标题重复，建议合并或修改'
    });
  }

  // 2. 检测是否有运行中的相同 Agent 任务
  const runningSameAgent = existingTasks.filter(t =>
    t.agentId === task.agentId && t.status === 'running'
  );
  if (runningSameAgent.length > 0) {
    conflicts.push({
      type: 'multiple-running',
      agentId: task.agentId,
      count: runningSameAgent.length,
      severity: 'low',
      suggestion: '同一 Agent 有多个运行中的任务，建议顺序执行'
    });
  }

  // 3. 检测资源冲突（假设有资源定义）
  if (task.resources) {
    for (const resource of task.resources) {
      const conflictingTasks = existingTasks.filter(t =>
        t.resources?.includes(resource) && t.status === 'running'
      );
      if (conflictingTasks.length > 0) {
        conflicts.push({
          type: 'resource-conflict',
          resource: resource,
          taskId: conflictingTasks[0].taskId,
          severity: 'high',
          suggestion: `资源 ${resource} 已被任务 ${conflictingTasks[0].taskId} 使用`
        });
      }
    }
  }

  return conflicts;
}
```

**优势**:
- ✅ 快速、可预测的冲突检测
- ✅ 不依赖 LLM
- ✅ 易于维护和扩展

---

### 3. 文档优化建议

#### 3.1 添加 OpenClaw 集成文档

**文件**: `OPENCLAW-INTEGRATION.md`

**内容**:
```markdown
# Stone 任务管理系统 - OpenClaw 集成指南

## 1. OpenClaw 工具使用

### 1.1 sessions_spawn

创建 subagent 执行任务。

**参数**:
- `agentId`: Agent ID（如 ffmedia）
- `mode`: 执行模式（run 或 session）
- `task`: 任务描述
- `label`: 可选标签（用于识别）

**示例**:
```javascript
const subagent = await sessions_spawn({
  agentId: 'ffmedia',
  mode: 'run',
  task: '检查网络配置',
  label: 'task:001:step:001:check-network'
});
```

**返回值**:
```javascript
{
  sessionId: "123e4567-e89b-12d3-a456-426614174000",
  label: "task:001:step:001:check-network"
}
```

### 1.2 sessions_list

列出所有 sessions。

**参数**:
- `kinds`: Session 类型（subagent）
- `activeMinutes`: 活跃时间范围（分钟）

**示例**:
```javascript
const sessions = await sessions_list({
  kinds: ['subagent'],
  activeMinutes: 30
});
```

### 1.3 sessions_history

查询 session 历史。

**参数**:
- `sessionKey`: Session ID
- `includeTools`: 是否包含工具调用

**示例**:
```javascript
const history = await sessions_history({
  sessionKey: '123e4567-e89b-12d3-a456-426614174000',
  includeTools: true
});
```

## 2. 最佳实践

### 2.1 Subagent 命名

使用 label 参数指定可读标签：

```javascript
const label = `task:${taskId}:step:${stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`;
```

### 2.2 Subagent 等待

使用轮询机制检查 subagent 状态：

```javascript
async function waitForSubagent(sessionId, timeout = 3600000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    const history = await sessions_history({
      sessionKey: sessionId,
      includeTools: true
    });

    // 检查完成标记
    // ...

    await new Promise(resolve => setTimeout(resolve, 5000));
  }

  return { success: false, output: 'Timeout' };
}
```

### 2.3 Subagent 查询

通过 label 查询 subagents：

```javascript
const sessions = await sessions_list({ kinds: ['subagent'] });
const taskSubagents = sessions.filter(s =>
  s.label && s.label.startsWith(`task:${taskId}:`)
);
```

## 3. 注意事项

1. **Session Key 格式**: OpenClaw 自动生成 UUID，不支持自定义格式
2. **Label 参数**: 使用 label 指定可读标签，方便查询
3. **轮询机制**: 使用轮询检查 subagent 状态，避免阻塞
4. **错误处理**: 妥善处理超时和错误情况
```

#### 3.2 添加 API 文档

**文件**: `API-REFERENCE.md`

**内容**:
```markdown
# Stone 任务管理系统 - API 参考

## 1. 任务管理 API

### 1.1 createTask(taskConfig)

创建任务。

**参数**:
- `title`: 任务标题
- `description`: 任务描述
- `agentId`: Agent ID
- `priority`: 优先级（high, medium, low）
- `steps`: 步骤数组
- `conflictResolution`: 冲突处理策略

**返回值**: 任务对象

**示例**:
```javascript
const task = await createTask({
  title: '诊断 RTSP 连接问题',
  description: '检查 RTSP 客户端无法连接的问题',
  agentId: 'ffmedia',
  priority: 'high',
  steps: [
    { title: '检查网络配置', description: '使用 ifconfig 检查网络' },
    { title: '检查设备状态', description: '使用 adb 检查设备' }
  ]
});
```

### 1.2 executeTask(taskId)

执行任务。

**参数**:
- `taskId`: 任务 ID

**返回值**: 任务对象

**示例**:
```javascript
const task = await executeTask('task-001');
```

### 1.3 getTask(taskId)

获取任务详情。

**参数**:
- `taskId`: 任务 ID

**返回值**: 任务对象

**示例**:
```javascript
const task = await getTask('task-001');
```

### 1.4 getTasksByAgent(agentId, statusFilter)

查询 Agent 的任务。

**参数**:
- `agentId`: Agent ID
- `statusFilter`: 状态过滤（可选）

**返回值**: 任务数组

**示例**:
```javascript
const tasks = await getTasksByAgent('ffmedia', 'running');
```

## 2. Subagent 管理 API

### 2.1 spawnSubagent(task, step)

创建 subagent 执行步骤。

**参数**:
- `task`: 任务对象
- `step`: 步骤对象

**返回值**: Subagent 信息

**示例**:
```javascript
const subagent = await spawnSubagent(task, step);
```

### 2.2 waitForSubagent(sessionId, timeout)

等待 subagent 完成。

**参数**:
- `sessionId`: Session ID
- `timeout`: 超时时间（毫秒）

**返回值**: 执行结果

**示例**:
```javascript
const result = await waitForSubagent('123e4567-e89b-12d3-a456-426614174000', 3600000);
```

### 2.3 getSubagentStatus(sessionId)

获取 subagent 状态。

**参数**:
- `sessionId`: Session ID

**返回值**: 状态信息

**示例**:
```javascript
const status = await getSubagentStatus('123e4567-e89b-12d3-a456-426614174000');
```

## 3. 冲突检测 API

### 3.1 detectConflicts(task, existingTasks, mainGoal)

检测任务冲突。

**参数**:
- `task`: 任务对象
- `existingTasks`: 现有任务数组
- `mainGoal`: 主线目标

**返回值**: 冲突数组

**示例**:
```javascript
const conflicts = await detectConflicts(task, existingTasks, mainGoal);
```

### 3.2 resolveConflicts(task, conflicts)

解决冲突。

**参数**:
- `task`: 任务对象
- `conflicts`: 冲突数组

**返回值**: 解决方案

**示例**:
```javascript
const resolution = await resolveConflicts(task, conflicts);
```
```

#### 3.3 添加架构文档

**文件**: `ARCHITECTURE.md`

**内容**:
```markdown
# Stone 任务管理系统 - 架构文档

## 1. 系统架构

### 1.1 组件图

```
┌─────────────────────────────────────────┐
│           Stone (任务管理器)            │
│                                         │
│  ┌─────────────┐  ┌──────────────┐   │
│  │ 任务管理    │  │ 冲突检测     │   │
│  │             │  │              │   │
│  │ - 创建      │  │ - 检测冲突   │   │
│  │ - 执行      │  │ - 处理冲突   │   │
│  │ - 查询      │  │              │   │
│  └─────────────┘  └──────────────┘   │
│                                         │
│  ┌─────────────┐  ┌──────────────┐   │
│  │ Subagent    │  │ 监控         │   │
│  │ 管理        │  │              │   │
│  │ - 创建      │  │ - 状态检查   │   │
│  │ - 等待      │  │ - 超时检测   │   │
│  │ - 查询      │  │              │   │
│  └─────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
         │                      │
         │ sessions_spawn       │ sessions_list
         │ sessions_history      │
         ↓                      ↓
┌─────────────────────────────────────────┐
│          OpenClaw Runtime               │
│                                         │
│  ┌─────────────┐  ┌──────────────┐   │
│  │ ffmedia     │  │ agentmesh    │   │
│  └─────────────┘  └──────────────┘   │
│                                         │
│  ┌─────────────┐  ┌──────────────┐   │
│  │ Ai-Stock    │  │ ...          │   │
│  │ Assistant   │  │              │   │
│  └─────────────┘  └──────────────┘   │
└─────────────────────────────────────────┘
```

### 1.2 数据流

```
用户请求
  ↓
Stone 创建任务
  ↓
冲突检测
  ↓
创建任务文件
  ↓
执行任务
  ↓
创建 Subagent (sessions_spawn)
  ↓
等待 Subagent 完成
  ↓
更新任务状态
  ↓
记录结果
  ↓
完成任务
```

### 1.3 状态转换

```
pending → running → completed
  ↓        ↓         ↓
paused   failed    archived
  ↑
cancelled
```

## 2. 模块设计

### 2.1 任务管理模块

**职责**:
- 创建、执行、查询任务
- 管理任务状态
- 记录任务历史

**API**:
- `createTask(taskConfig)`
- `executeTask(taskId)`
- `getTask(taskId)`
- `getTasksByAgent(agentId, statusFilter)`

### 2.2 Subagent 管理模块

**职责**:
- 创建 subagent
- 等待 subagent 完成
- 查询 subagent 状态

**API**:
- `spawnSubagent(task, step)`
- `waitForSubagent(sessionId, timeout)`
- `getSubagentStatus(sessionId)`

### 2.3 冲突检测模块

**职责**:
- 检测任务冲突
- 处理冲突
- 生成冲突报告

**API**:
- `detectConflicts(task, existingTasks, mainGoal)`
- `resolveConflicts(task, conflicts)`

### 2.4 监控模块

**职责**:
- 检查任务状态
- 检查 subagent 状态
- 检测超时任务

**API**:
- `checkTask(task)`
- `checkTaskSubagents(task)`
- `checkTaskTimeout(task)`

## 3. 数据存储

### 3.1 任务文件

**路径**: `tasks/{active|completed|failed|archived}/task-*.json`

**格式**: JSON

**示例**:
```json
{
  "taskId": "task-001",
  "title": "诊断 RTSP 连接问题",
  "description": "检查 RTSP 客户端无法连接的问题",
  "agentId": "ffmedia",
  "priority": "high",
  "status": "running",
  "createdAt": "2026-03-03T10:30:00.000Z",
  "updatedAt": "2026-03-03T11:15:00.000Z",
  "steps": [...],
  "context": {...},
  "result": null,
  "summary": null
}
```

### 3.2 任务注册表

**路径**: `tasks/task-registry.json`

**格式**: JSON

**示例**:
```json
{
  "version": 1,
  "totalTasks": 15,
  "activeTasks": 2,
  "completedTasks": 10,
  "failedTasks": 3,
  "tasks": {...},
  "byAgent": {...},
  "lastUpdated": "2026-03-03T11:15:00.000Z"
}
```

### 3.3 任务历史

**路径**: `tasks/task-history.md`

**格式**: Markdown

**示例**:
```markdown
## [2026-03-03T10:30:00.000Z] created: task-001

- 标题: 诊断 RTSP 连接问题
- Agent: ffmedia
- 状态: pending
```

## 4. 集成点

### 4.1 与 Stone 监控集成

**集成方式**:
- 在 `monitor-simple.js` 中添加任务检查
- 更新 AGENT-STATES.md 格式
- 更新 MONITOR-LOG.md 格式

### 4.2 与 OpenClaw 集成

**集成方式**:
- 使用 `sessions_spawn` 创建 subagent
- 使用 `sessions_list` 查询 subagents
- 使用 `sessions_history` 查询 subagent 历史
```

---

## 📊 检查结果总结

### 问题清单

| 编号 | 问题描述 | 严重程度 | 状态 |
|------|---------|---------|------|
| 1 | Subagent Session Key 格式不符合 OpenClaw 规范 | 🔴 高 | 待修复 |
| 2 | Subagent 查询方式假设不存在 | 🔴 高 | 待修复 |
| 3 | Subagent 等待机制不完整 | 🟡 中 | 待优化 |
| 4 | 文档缺少 OpenClaw 集成指南 | 🟡 中 | 待补充 |
| 5 | 文档缺少 API 参考 | 🟡 中 | 待补充 |
| 6 | 文档缺少架构文档 | 🟡 中 | 待补充 |

### 优化建议

1. **修复 Subagent Session Key 格式**
   - 使用 OpenClaw 自动生成的 UUID
   - 使用 label 参数指定可读标签
   - 在任务文件中记录 sessionId 和 label

2. **修复 Subagent 查询方式**
   - 使用 sessions_list 查询 subagents
   - 通过 label 过滤相关 subagents
   - 通过 sessionId 查询特定 subagent

3. **完善 Subagent 等待机制**
   - 使用轮询机制检查 subagent 状态
   - 添加超时处理
   - 添加错误处理

4. **补充文档**
   - 添加 OpenClaw 集成指南
   - 添加 API 参考
   - 添加架构文档

---

## 🚀 下一步行动

### 立即执行（1 天内）

1. ✅ 修复 Subagent Session Key 格式
2. ✅ 修复 Subagent 查询方式
3. ✅ 完善 Subagent 等待机制

### 短期（2-3 天）

4. ✅ 补充 OpenClaw 集成指南
5. ✅ 补充 API 参考
6. ✅ 补充架构文档
7. ✅ 更新设计文档（TASK-MANAGEMENT-DESIGN.md）

### 中期（3-5 天）

8. ✅ 实现 Phase 2（任务执行）
9. ✅ 实现 Phase 3（冲突检测）
10. ✅ 实现 Phase 4（监控集成）

---

**检查人**: Stone Agent 🗿
**检查时间**: 2026-03-03 11:05
**检查结果**: ⚠️ 发现 6 个问题，需要优化
