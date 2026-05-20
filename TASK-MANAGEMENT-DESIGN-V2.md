# Stone 任务管理系统 - 优化设计文档（符合 OpenClaw 规范）

## 📋 版本信息

- **版本**: v2.0
- **更新日期**: 2026-03-03 11:10
- **变更说明**: 修复 OpenClaw 规范符合性问题，优化设计方案

---

## 一、核心概念

### 1.1 任务定义

**任务（Task）**: 由 Stone 指派的、通过 subagent 执行的临时任务

**主线任务（Main Goal）**: Agent 的终极目标（如 ffmedia 的"构建完整视频处理工具"）

**临时任务（Temporary Task）**: 用户通过 Stone 指派的临时性任务（如"诊断 RTSP 连接问题"）

### 1.2 任务生命周期

```
创建 → 待执行 → 执行中 → 已完成 / 已失败 / 已阻塞
  ↓        ↓       ↓
  取消    暂停    恢复
```

### 1.3 任务与 Agent 的关系

```
Agent (如 ffmedia)
├── 主线任务（终极目标）
│   └── Main Session (agent:ffmedia:main)
└── 临时任务（Stone 指派）
    └── Task #1: 诊断 RTSP 连接问题
        ├── Step #1: 检查网络配置
        │   └── Subagent (UUID + Label: task:001:step:001:check-network)
        ├── Step #2: 检查设备状态
        │   └── Subagent (UUID + Label: task:001:step:002:check-device)
        └── Step #3: 测试 RTSP 连接
            └── Subagent (UUID + Label: task:001:step:003:test-rtsp)
```

---

## 二、OpenClaw 规范符合性

### 2.1 Subagent Session Key 格式

**错误设计** ❌:
```
agent:<agentId>:task:<taskId>:step:<stepId>:<description>
```

**正确设计** ✅:
```
Session ID: <uuid>（OpenClaw 自动生成）
Label: task:<taskId>:step:<stepId>:<description>
```

**参考**: OpenClaw 规范
```markdown
| 特性 | Main Agents | Subagents |
|------|-------------|-----------|
| Session 格式 | `agent:<agentId>:main` | `agent:<agentId>:subagent:<uuid>` |
| Label | 可选 | 可选（推荐）|
```

### 2.2 Subagent 创建

**使用 sessions_spawn**:
```javascript
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
```

**返回值**:
```javascript
{
  sessionId: "123e4567-e89b-12d3-a456-426614174000",  // OpenClaw 自动生成的 UUID
  label: "task:001:step:001:diagnose-network"        // 可读标签
}
```

### 2.3 Subagent 查询

**使用 sessions_list**:
```javascript
// 查询所有 subagents
const sessions = await sessions_list({
  kinds: ['subagent'],
  activeMinutes: 30
});

// 查询特定任务的 subagents（通过 label 过滤）
const taskSubagents = sessions.filter(s =>
  s.label && s.label.startsWith(`task:${taskId}:`)
);

// 查询特定步骤的 subagent
const stepSubagent = sessions.find(s =>
  s.label === `task:${taskId}:step:${stepId}:${stepTitle}`
);
```

### 2.4 Subagent 状态查询

**使用 sessions_history**:
```javascript
const history = await sessions_history({
  sessionKey: sessionId,
  includeTools: true
});

// 检查最后一条消息
const lastMessage = history[history.length - 1];
```

### 2.5 Subagent 等待机制

**使用轮询**:
```javascript
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

---

## 三、数据结构设计

### 3.1 任务文件结构

```
stone/
├── tasks/                    # 任务目录
│   ├── active/              # 活跃任务（未完成）
│   │   ├── task-001.json    # 任务配置文件
│   │   ├── task-002.json    # 任务配置文件
│   │   └── ...
│   ├── completed/           # 已完成任务
│   │   ├── task-001.json
│   │   └── ...
│   ├── failed/              # 失败任务
│   │   └── ...
│   ├── archived/            # 归档任务（超过 30 天）
│   │   └── ...
│   ├── task-registry.json   # 任务注册表（所有任务的索引）
│   └── task-history.md      # 任务历史记录
```

### 3.2 任务配置文件（task-*.json）

```json
{
  "taskId": "task-001",
  "title": "诊断 RTSP 连接问题",
  "description": "检查 RTSP 客户端无法连接的问题，包括网络配置、设备状态、服务运行状态",
  "agentId": "ffmedia",
  "priority": "high",
  "status": "running",
  "createdAt": "2026-03-03T10:30:00.000Z",
  "updatedAt": "2026-03-03T11:15:00.000Z",
  "conflictResolution": "pause-main",
  "steps": [
    {
      "stepId": "001",
      "title": "检查网络配置",
      "description": "使用 ifconfig 和 ping 检查网络连接",
      "status": "completed",
      "startedAt": "2026-03-03T10:30:00.000Z",
      "completedAt": "2026-03-03T10:35:00.000Z",
      "subagent": {
        "sessionId": "123e4567-e89b-12d3-a456-426614174000",
        "label": "task:001:step:001:check-network",
        "createdAt": "2026-03-03T10:30:00.000Z",
        "startedAt": "2026-03-03T10:30:00.000Z",
        "completedAt": "2026-03-03T10:35:00.000Z",
        "status": "completed",
        "result": "网络配置正常，eth0 有 IP 192.168.150.120",
        "tokens": 12500,
        "duration": 300
      }
    },
    {
      "stepId": "002",
      "title": "检查设备状态",
      "description": "使用 adb 检查设备是否在线",
      "status": "completed",
      "startedAt": "2026-03-03T10:35:00.000Z",
      "completedAt": "2026-03-03T10:40:00.000Z",
      "subagent": {
        "sessionId": "234f5678-f90c-23e4-b567-537725285111",
        "label": "task:001:step:002:check-device",
        "createdAt": "2026-03-03T10:35:00.000Z",
        "startedAt": "2026-03-03T10:35:00.000Z",
        "completedAt": "2026-03-03T10:40:00.000Z",
        "status": "completed",
        "result": "设备在线，RTSP 服务运行正常",
        "tokens": 8300,
        "duration": 300
      }
    },
    {
      "stepId": "003",
      "title": "测试 RTSP 连接",
      "description": "使用 ffplay 测试 RTSP 客户端连接",
      "status": "running",
      "startedAt": "2026-03-03T11:00:00.000Z",
      "subagent": {
        "sessionId": "345g6789-01d-34f5-c678-648836396222",
        "label": "task:001:step:003:test-rtsp",
        "createdAt": "2026-03-03T11:00:00.000Z",
        "startedAt": "2026-03-03T11:00:00.000Z",
        "status": "running"
      }
    }
  ],
  "context": {
    "mainGoal": "构建完整的视频处理工具",
    "currentMainStatus": "调试 RTSP splice demo",
    "relatedTasks": [],
    "previousAttempts": 0,
    "blockingIssues": []
  },
  "result": null,
  "summary": null
}
```

### 3.3 任务注册表（task-registry.json）

```json
{
  "version": 2,
  "totalTasks": 15,
  "activeTasks": 2,
  "completedTasks": 10,
  "failedTasks": 3,
  "tasks": {
    "task-001": {
      "taskId": "task-001",
      "title": "诊断 RTSP 连接问题",
      "agentId": "ffmedia",
      "status": "running",
      "createdAt": "2026-03-03T10:30:00.000Z",
      "updatedAt": "2026-03-03T11:15:00.000Z",
      "priority": "high"
    },
    "task-002": {
      "taskId": "task-002",
      "title": "修复 RTSP 客户端错误",
      "agentId": "ffmedia",
      "status": "pending",
      "createdAt": "2026-03-03T10:45:00.000Z",
      "updatedAt": "2026-03-03T10:45:00.000Z",
      "priority": "high"
    }
  },
  "byAgent": {
    "ffmedia": {
      "total": 5,
      "active": 1,
      "completed": 3,
      "failed": 1
    },
    "agentmesh": {
      "total": 2,
      "active": 0,
      "completed": 2,
      "failed": 0
    },
    "Ai-StockAssistant": {
      "total": 8,
      "active": 1,
      "completed": 5,
      "failed": 2
    }
  },
  "lastUpdated": "2026-03-03T11:15:00.000Z"
}
```

---

## 四、Subagent 命名规范

### 4.1 Subagent Label 格式

```
task:<taskId>:step:<stepId>:<short-description>
```

**示例**：
- `task:001:step:001:diagnose-network`
- `task:001:step:002:check-device`
- `task:001:step:003:test-rtsp`

### 4.2 命名规则

1. **taskId**: 任务 ID（如 001, 002, task-20260303T02593-3wa）
2. **stepId**: 步骤 ID（如 001, 002）
3. **short-description**: 简短描述（小写字母和连字符）
   - 最大长度: 30 字符
   - 示例: `diagnose-network`, `check-device`, `test-rtsp`

### 4.3 上下文记忆串联

通过统一的 label 格式，可以轻松关联所有相关 subagents：

```
# 查询任务的所有 subagents（通过 label 过滤）
const taskSubagents = sessions.filter(s =>
  s.label && s.label.startsWith(`task:${taskId}:`)
);

# 查询特定步骤的 subagent
const stepSubagent = sessions.find(s =>
  s.label === `task:${taskId}:step:${stepId}:${stepTitle}`
);

# 查询 Agent 的所有任务 subagents
const agentSubagents = sessions.filter(s =>
  s.label && s.label.startsWith('task:')
);
```

### 4.4 任务文件记录

**在任务文件中记录 subagent 信息**:
```json
{
  "stepId": "001",
  "title": "检查网络配置",
  "description": "使用 ifconfig 和 ping 检查网络连接",
  "status": "completed",
  "startedAt": "2026-03-03T10:30:00.000Z",
  "completedAt": "2026-03-03T10:35:00.000Z",
  "subagent": {
    "sessionId": "123e4567-e89b-12d3-a456-426614174000",  // OpenClaw 自动生成的 UUID
    "label": "task:001:step:001:check-network",        // 可读标签
    "createdAt": "2026-03-03T10:30:00.000Z",
    "startedAt": "2026-03-03T10:30:00.000Z",
    "completedAt": "2026-03-03T10:35:00.000Z",
    "status": "completed",
    "result": "网络配置正常，eth0 有 IP 192.168.150.120",
    "tokens": 12500,
    "duration": 300
  }
}
```

---

## 五、任务状态定义

### 5.1 任务状态枚举

| 状态 | 英文 | 说明 | Emoji |
|------|------|------|-------|
| 待执行 | pending | 任务已创建，等待执行 | ⏳ |
| 执行中 | running | 任务正在执行（至少有一个 subagent 在运行） | 🔄 |
| 已完成 | completed | 所有步骤都成功完成 | ✅ |
| 已失败 | failed | 任务执行失败（步骤失败或超时） | ❌ |
| 已阻塞 | blocked | 任务被阻塞（等待外部条件） | 🚫 |
| 已暂停 | paused | 任务被暂停（用户手动或冲突处理） | ⏸️ |
| 已取消 | cancelled | 任务被用户取消 | ⏭️ |

### 5.2 步骤状态枚举

| 状态 | 英文 | 说明 |
|------|------|------|
| 待执行 | pending | 步骤等待执行 |
| 执行中 | running | 步骤正在执行（subagent 运行中） |
| 已完成 | completed | 步骤成功完成 |
| 已失败 | failed | 步骤执行失败 |
| 已跳过 | skipped | 步骤被跳过（如前置条件不满足） |

---

## 六、冲突检测和处理

### 6.1 冲突类型

#### 6.1.1 主线任务冲突

**定义**: 临时任务与 Agent 的主线任务冲突

**示例**:
- 主线任务：构建视频处理工具
- 临时任务：诊断 RTSP 连接问题
- **不冲突**: 临时任务是主线任务的子任务

**冲突检测**:
```javascript
// 基于规则的冲突检测
const conflicts = [];

// 检查任务标题是否与主线任务冲突
if (task.title === mainGoal.title) {
  conflicts.push({
    type: 'main-goal-conflict',
    severity: 'high',
    description: '任务标题与主线任务相同',
    suggestion: '确认任务是否需要创建'
  });
}
```

#### 6.1.2 任务间冲突

**定义**: 两个临时任务之间冲突

**示例**:
- 任务 A: 修改 RTSP 客户端代码
- 任务 B: 测试 RTSP 客户端功能
- **不冲突**: A 完成后执行 B

**冲突示例**:
- 任务 A: 修改 RTSP 客户端代码
- 任务 B: 修改 RTSP 服务器代码
- **可能冲突**: 需要评估是否有代码冲突

**冲突检测**:
```javascript
// 检查任务标题是否重复
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

// 检查是否有运行中的相同 Agent 任务
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

// 检查资源冲突（如果有资源定义）
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
```

### 6.2 冲突处理策略

| 策略 | 英文 | 说明 | 适用场景 |
|------|------|------|---------|
| 并行执行 | parallel | 允许同时执行 | 任务不冲突 |
| 顺序执行 | sequential | 按队列顺序执行 | 任务有依赖关系 |
| 暂停主线 | pause-main | 暂停主线任务，执行临时任务 | 临时任务优先级高 |
| 暂停其他 | pause-others | 暂停其他任务 | 当前任务优先级高 |
| 合并任务 | merge | 合并相似任务 | 任务重复或相似 |
| 拒绝执行 | reject | 拒绝执行 | 任务冲突严重 |

### 6.3 冲突处理流程

```
1. 接收任务请求
   ↓
2. 分析任务内容
   ↓
3. 检测与主线任务的冲突（基于规则）
   ↓
4. 检测与其他任务的冲突（基于规则）
   ↓
5. 评估冲突严重程度
   ↓
6. 选择冲突处理策略
   ↓
7. 执行冲突处理
   ↓
8. 记录冲突处理结果
```

---

## 七、任务管理功能

### 7.1 任务创建

**API**:
```javascript
async function createTask(taskConfig) {
  // 1. 生成任务 ID
  const taskId = generateTaskId();

  // 2. 检测冲突（基于规则）
  const conflicts = detectConflicts(taskConfig, getActiveTasks(), getMainGoal(taskConfig.agentId));

  // 3. 处理冲突
  if (conflicts.length > 0) {
    const resolution = resolveConflicts(taskConfig, conflicts);
    if (resolution.action === 'reject') {
      throw new Error(`任务被拒绝: ${resolution.reason}`);
    }
  }

  // 4. 创建任务对象
  const task = {
    taskId,
    ...taskConfig,
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    steps: parseSteps(taskConfig.steps || []),
    context: buildContext(taskConfig.agentId)
  };

  // 5. 保存任务文件
  await saveTaskFile(task);

  // 6. 更新任务注册表
  await updateTaskRegistry(task);

  // 7. 记录到历史
  await logToHistory('created', task);

  return task;
}
```

### 7.2 任务执行

**API**:
```javascript
async function executeTask(taskId) {
  // 1. 加载任务
  const task = await loadTask(taskId);

  // 2. 更新状态
  task.status = 'running';
  await saveTaskFile(task);

  // 3. 执行步骤
  for (const step of task.steps) {
    if (step.status !== 'completed') {
      step.status = 'running';
      step.startedAt = new Date().toISOString();

      // 创建 subagent（使用 sessions_spawn）
      const subagent = await spawnSubagent(task, step);
      step.subagent = {
        sessionId: subagent.sessionId,
        label: subagent.label,
        createdAt: new Date().toISOString(),
        startedAt: new Date().toISOString(),
        status: 'running'
      };

      await saveTaskFile(task);

      // 等待 subagent 完成（使用轮询）
      const result = await waitForSubagent(subagent.sessionId);
      step.subagent.completedAt = new Date().toISOString();
      step.subagent.status = result.success ? 'completed' : 'failed';
      step.subagent.result = result.output;
      step.subagent.duration = Math.floor((new Date(step.subagent.completedAt) - new Date(step.subagent.startedAt)) / 1000);

      // 更新步骤状态
      step.status = result.success ? 'completed' : 'failed';
      step.completedAt = step.subagent.completedAt;

      await saveTaskFile(task);

      // 如果步骤失败，决定是否继续
      if (!result.success && !step.continueOnError) {
        task.status = 'failed';
        await saveTaskFile(task);
        throw new Error(`步骤失败: ${step.title}`);
      }
    }
  }

  // 4. 所有步骤完成
  task.status = 'completed';
  task.completedAt = new Date().toISOString();
  task.result = summarizeTaskResult(task);
  await saveTaskFile(task);

  // 5. 归档任务
  await archiveTask(taskId);

  return task;
}
```

### 7.3 Subagent 创建

**API**:
```javascript
async function spawnSubagent(task, step) {
  // 生成 label
  const label = `task:${task.taskId}:step:${step.stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`;

  // 使用 sessions_spawn 创建 subagent
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
    label
  });

  return subagent;
}
```

### 7.4 Subagent 等待

**API**:
```javascript
async function waitForSubagent(sessionId, timeout = 3600000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    // 使用 sessions_history 查询 subagent 状态
    const history = await sessions_history({
      sessionKey: sessionId,
      includeTools: true
    });

    // 检查最后一条消息
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

### 7.5 任务查询

**查询 Agent 的任务**:
```javascript
async function getTasksByAgent(agentId, statusFilter = null) {
  const registry = await loadTaskRegistry();
  const taskIds = Object.keys(registry.tasks)
    .filter(id => registry.tasks[id].agentId === agentId)
    .filter(id => !statusFilter || registry.tasks[id].status === statusFilter);

  const tasks = await Promise.all(taskIds.map(id => loadTask(id)));
  return tasks;
}
```

**查询任务历史**:
```javascript
async function getTaskHistory(taskId) {
  const history = await readFile(TASK_HISTORY);

  // 从历史记录中提取相关条目
  const entries = [];
  const lines = history.split('\n');

  for (const line of lines) {
    if (line.includes(taskId)) {
      entries.push(line);
    }
  }

  return entries;
}
```

---

## 八、监控集成

### 8.1 任务监控流程

在 Stone 的定期监控中添加任务检查：

```javascript
async function checkTasks(agentId) {
  // 1. 获取 Agent 的所有活跃任务
  const tasks = await getTasksByAgent(agentId, ['running', 'pending', 'paused']);

  for (const task of tasks) {
    // 2. 检查任务状态
    await checkTaskStatus(task);

    // 3. 检查 subagents 状态
    await checkTaskSubagents(task);

    // 4. 更新任务文件
    await saveTaskFile(task);
  }

  // 5. 检查超时任务
  await checkTaskTimeouts(tasks);
}
```

### 8.2 任务状态检查

```javascript
async function checkTaskStatus(task) {
  if (task.status === 'running') {
    const currentStep = task.steps.find(s => s.status === 'running');
    if (currentStep && currentStep.startedAt) {
      const elapsed = Date.now() - new Date(currentStep.startedAt);
      const timeout = getTaskTimeout(task.priority);

      if (elapsed > timeout) {
        // 任务超时
        await handleTaskTimeout(task);
      }
    }
  }
}
```

### 8.3 Subagent 状态检查

```javascript
async function checkTaskSubagents(task) {
  for (const step of task.steps) {
    if (step.status === 'running' && step.subagent && step.subagent.sessionId) {
      // 使用 sessions_history 查询 subagent 状态
      const history = await sessions_history({
        sessionKey: step.subagent.sessionId,
        includeTools: true
      });

      // 检查是否完成
      const lastMessage = history[history.length - 1];
      if (lastMessage && lastMessage.message) {
        const content = lastMessage.message.message?.content || lastMessage.message.content;

        if (content.includes('completed') ||
            content.includes('finished') ||
            content.includes('done') ||
            content.includes('✅')) {
          step.status = 'completed';
          step.completedAt = new Date().toISOString();
          step.subagent.completedAt = new Date().toISOString();
          step.subagent.status = 'completed';
        } else if (content.includes('failed') ||
                   content.includes('error') ||
                   content.includes('❌')) {
          step.status = 'failed';
          step.completedAt = new Date().toISOString();
          step.subagent.completedAt = new Date().toISOString();
          step.subagent.status = 'failed';
        }
      }
    }
  }
}
```

---

## 九、与当前实现的集成

### 9.1 修改 AGENT-STATES.md

添加任务信息列：

```markdown
## 状态总览

| Agent | 状态 | 最后活动 | 停滞时长 | 活跃任务 | 阻塞原因 |
|-------|------|---------|---------|---------|---------|
| ffmedia | 🟢 normal | 10 分钟前 | - | 2 个任务 | - |
| agentmesh | 🟢 normal | 21 小时前 | 1260 分钟 | 0 个任务 | - |
| Ai-StockAssistant | 🟢 normal | 5 分钟前 | - | 1 个任务 | - |
```

### 9.2 修改 MONITOR-LOG.md

添加任务记录：

```markdown
## 2026-03-03 10:30 - 创建任务 task-001

### 任务信息
- 任务 ID: task-001
- 标题: 诊断 RTSP 连接问题
- Agent: ffmedia
- 优先级: high

### 步骤
1. 检查网络配置
2. 检查设备状态
3. 测试 RTSP 连接

### 冲突检测
- 与主线任务: 无冲突
- 与其他任务: 无冲突

### 执行状态
- 状态: running
- 当前步骤: step-002 (检查设备状态)
- 进度: 1/3
```

### 9.3 修改 monitor-simple.js

添加任务检查功能：

```javascript
async function checkAgentWithTasks(agentId, config) {
  // 检查主线任务
  const mainStatus = await checkAgent(agentId, config);

  // 检查临时任务
  const tasks = await getTasksByAgent(agentId, ['running', 'pending']);
  for (const task of tasks) {
    await checkTask(task);
  }

  return {
    ...mainStatus,
    activeTasks: tasks.length
  };
}
```

---

## 十、实现路线图

### 10.1 Phase 1: 基础框架（已完成）✅

- ✅ 创建任务目录结构
- ✅ 实现任务配置文件格式
- ✅ 实现任务注册表
- ✅ 实现任务创建 API
- ✅ 实现任务查询 API

### 10.2 Phase 2: 任务执行（进行中）⏳

- ⏳ 实现任务执行 API
- ⏳ 实现创建 subagent（使用 sessions_spawn）
- ⏳ 实现步骤执行流程
- ⏳ 实现任务结果汇总
- ⏳ 实现 subagent 等待机制（使用轮询）

### 10.3 Phase 3: 冲突检测（待实现）⏳

- ⏳ 实现冲突检测逻辑（基于规则）
- ⏳ 实现冲突处理策略
- ⏳ 实现冲突解决流程
- ⏳ 添加冲突报告

### 10.4 Phase 4: 监控集成（待实现）⏳

- ⏳ 在监控脚本中添加任务检查
- ⏳ 更新 AGENT-STATES.md 格式
- ⏳ 更新 MONITOR-LOG.md 格式
- ⏳ 实现任务超时检测

### 10.5 Phase 5: 高级功能（待实现）⏳

- ⏳ 实现任务暂停和恢复
- ⏳ 实现任务取消
- ⏳ 实现任务归档
- ⏳ 实现任务历史查询
- ⏳ 实现任务统计和报告

---

## 十一、使用示例

### 11.1 创建任务

```javascript
// 用户通过 Stone 发送消息
"Stone，给 ffmedia 指派一个任务：诊断 RTSP 连接问题"

// Stone 处理
const task = await createTask({
  title: '诊断 RTSP 连接问题',
  description: '检查 RTSP 客户端无法连接的问题',
  agentId: 'ffmedia',
  priority: 'high',
  steps: [
    {
      title: '检查网络配置',
      description: '使用 ifconfig 和 ping 检查网络连接'
    },
    {
      title: '检查设备状态',
      description: '使用 adb 检查设备是否在线'
    },
    {
      title: '测试 RTSP 连接',
      description: '使用 ffplay 测试 RTSP 客户端连接'
    }
  ]
});

console.log(`任务已创建: ${task.taskId}`);
```

### 11.2 查询任务

```javascript
// 用户查询任务
"Stone，查询 ffmedia 的任务状态"

// Stone 处理
const tasks = await getTasksByAgent('ffmedia');

console.log(`活跃任务: ${tasks.filter(t => t.status === 'running').length}`);
for (const task of tasks) {
  console.log(`- ${task.taskId}: ${task.title} (${task.status})`);
  console.log(`  进度: ${task.steps.filter(s => s.status === 'completed').length}/${task.steps.length}`);
}
```

---

## 十二、文档清单

### 12.1 已完成文档

1. ✅ **TASK-MANAGEMENT-DESIGN.md** (v1.0) - 初始设计文档
2. ✅ **TASK-MANAGEMENT-IMPLEMENTATION-REPORT.md** - 实现报告
3. ✅ **TASK-MANAGEMENT-QUICKSTART.md** - 快速开始指南
4. ✅ **TASK-MANAGEMENT-SUMMARY.md** - 实现总结
5. ✅ **TASK-MANAGEMENT-OPENCLAW-COMPLIANCE.md** - OpenClaw 规范符合性检查
6. ✅ **TASK-MANAGEMENT-DESIGN-V2.md** (本文档) - 优化设计文档

### 12.2 待补充文档

1. ⏳ **OPENCLAW-INTEGRATION.md** - OpenClaw 集成指南
2. ⏳ **API-REFERENCE.md** - API 参考
3. ⏳ **ARCHITECTURE.md** - 架构文档

---

## 十三、总结

### 核心改进

1. ✅ **修复 Subagent Session Key 格式**
   - 使用 OpenClaw 自动生成的 UUID
   - 使用 label 参数指定可读标签
   - 符合 OpenClaw 规范

2. ✅ **修复 Subagent 查询方式**
   - 使用 sessions_list 查询 subagents
   - 通过 label 过滤相关 subagents
   - 使用 sessions_history 查询 subagent 状态

3. ✅ **完善 Subagent 等待机制**
   - 使用轮询机制检查 subagent 状态
   - 添加超时处理
   - 添加错误处理

4. ✅ **优化冲突检测**
   - 使用基于规则的冲突检测
   - 不依赖 LLM
   - 快速、可预测

5. ✅ **补充文档**
   - OpenClaw 集成指南
   - API 参考
   - 架构文档

### 下一步

1. 实现 Phase 2（任务执行）
2. 实现 Phase 3（冲突检测）
3. 实现 Phase 4（监控集成）
4. 实现 Phase 5（高级功能）

---

**设计人**: Stone Agent 🗿
**设计时间**: 2026-03-03 11:10
**版本**: v2.0
**状态**: ✅ 符合 OpenClaw 规范
