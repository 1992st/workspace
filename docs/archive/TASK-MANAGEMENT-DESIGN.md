# Stone 任务管理系统设计文档

## 设计目标

为 Stone 添加任务管理能力，支持：
1. Stone 给 agent 指派临时任务
2. 任务可能与主线任务有冲突，需要冲突检测和处理
3. 使用 subagent 实现任务执行
4. Subagent 命名与任务关联，方便串联上下文记忆
5. Subagent 继承自特定 agent（如 b100）
6. 支持查询特定任务的历史进程和当前状态
7. 未完成任务纳入监控范围
8. 结合当前实现，综合设计，避免冲突

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
    ├── Task #1: 诊断 RTSP 连接问题
    │   ├── Subagent #1-1: 检查网络配置
    │   ├── Subagent #1-2: 检查设备状态
    │   └── Subagent #1-3: 测试 RTSP 连接
    └── Task #2: 修复 RTSP 客户端错误
        ├── Subagent #2-1: 分析错误日志
        ├── Subagent #2-2: 修复代码
        └── Subagent #2-3: 重新测试
```

---

## 二、数据结构设计

### 2.1 任务文件结构

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
│   └── archived/            # 归档任务（超过 30 天）
│       └── ...
├── task-registry.json       # 任务注册表（所有任务的索引）
└── task-history.md         # 任务历史记录
```

### 2.2 任务配置文件（task-*.json）

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
  "conflictResolution": "pause-main",  // 冲突处理策略
  "steps": [
    {
      "stepId": "step-001",
      "title": "检查网络配置",
      "description": "使用 ifconfig 和 ping 检查网络连接",
      "status": "completed",
      "startedAt": "2026-03-03T10:30:00.000Z",
      "completedAt": "2026-03-03T10:35:00.000Z",
      "subagent": {
        "sessionId": "agent:ffmedia:task-001:step-001:diagnose-network",
        "sessionKey": "stone-wakeup-ffmedia-20260303-1030",
        "result": "网络配置正常，eth0 有 IP 192.168.150.120",
        "tokens": 12500
      }
    },
    {
      "stepId": "step-002",
      "title": "检查设备状态",
      "description": "使用 adb 检查设备是否在线",
      "status": "completed",
      "startedAt": "2026-03-03T10:35:00.000Z",
      "completedAt": "2026-03-03T10:40:00.000Z",
      "subagent": {
        "sessionId": "agent:ffmedia:task-001:step-002:check-device",
        "sessionKey": "stone-wakeup-ffmedia-20260303-1035",
        "result": "设备在线，RTSP 服务运行正常",
        "tokens": 8300
      }
    },
    {
      "stepId": "step-003",
      "title": "测试 RTSP 连接",
      "description": "使用 ffplay 测试 RTSP 客户端连接",
      "status": "running",
      "startedAt": "2026-03-03T11:00:00.000Z",
      "subagent": {
        "sessionId": "agent:ffmedia:task-001:step-003:test-rtsp",
        "sessionKey": "stone-wakeup-ffmedia-20260303-1100"
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

### 2.3 任务注册表（task-registry.json）

```json
{
  "version": 1,
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

## 三、任务状态定义

### 3.1 任务状态枚举

| 状态 | 英文 | 说明 | Emoji |
|------|------|------|-------|
| 待执行 | pending | 任务已创建，等待执行 | ⏳ |
| 执行中 | running | 任务正在执行（至少有一个 subagent 在运行） | 🔄 |
| 已完成 | completed | 所有步骤都成功完成 | ✅ |
| 已失败 | failed | 任务执行失败（步骤失败或超时） | ❌ |
| 已阻塞 | blocked | 任务被阻塞（等待外部条件） | 🚫 |
| 已暂停 | paused | 任务被暂停（用户手动或冲突处理） | ⏸️ |
| 已取消 | cancelled | 任务被用户取消 | ⏭️ |

### 3.2 步骤状态枚举

| 状态 | 英文 | 说明 |
|------|------|------|
| 待执行 | pending | 步骤等待执行 |
| 执行中 | running | 步骤正在执行（subagent 运行中） |
| 已完成 | completed | 步骤成功完成 |
| 已失败 | failed | 步骤执行失败 |
| 已跳过 | skipped | 步骤被跳过（如前置条件不满足） |

---

## 四、Subagent 命名规范

### 4.1 Subagent Session Key 格式

```
agent:<agentId>:task:<taskId>:step:<stepId>:<short-description>
```

**示例**：
- `agent:ffmedia:task:001:step:001:diagnose-network`
- `agent:ffmedia:task:001:step:002:check-device`
- `agent:ffmedia:task:001:step:003:test-rtsp`

### 4.2 命名规则

1. **agentId**: 继承的 Agent ID（如 ffmedia, b100）
2. **taskId**: 任务 ID（如 001, 002）
3. **stepId**: 步骤 ID（如 001, 002）
4. **short-description**: 简短描述（小写字母和连字符）
   - 最大长度: 30 字符
   - 示例: `diagnose-network`, `check-device`, `test-rtsp`

### 4.3 上下文记忆串联

通过统一的命名规范，可以轻松关联所有相关 subagents：

```
# 查询任务的所有 subagents
agent:ffmedia:task:001:*

# 查询特定步骤的 subagent
agent:ffmedia:task:001:step:003:*

# 查询 Agent 的所有任务 subagents
agent:ffmedia:task:*
```

---

## 五、冲突检测和处理

### 5.1 冲突类型

#### 5.1.1 主线任务冲突

**定义**: 临时任务与 Agent 的主线任务冲突

**示例**:
- 主线任务：构建视频处理工具
- 临时任务：诊断 RTSP 连接问题
- **不冲突**: 临时任务是主线任务的子任务

**冲突检测**:
```
临时任务标题 + 描述 vs 主线任务标题 + 描述
→ 使用 LLM 分析是否冲突
```

#### 5.1.2 任务间冲突

**定义**: 两个临时任务之间冲突

**示例**:
- 任务 A: 修改 RTSP 客户端代码
- 任务 B: 测试 RTSP 客户端功能
- **不冲突**: A 完成后执行 B

**冲突示例**:
- 任务 A: 修改 RTSP 客户端代码
- 任务 B: 修改 RTSP 服务器代码
- **可能冲突**: 需要评估是否有代码冲突

### 5.2 冲突处理策略

#### 5.2.1 策略枚举

| 策略 | 英文 | 说明 | 适用场景 |
|------|------|------|---------|
| 并行执行 | parallel | 允许同时执行 | 任务不冲突 |
| 顺序执行 | sequential | 按队列顺序执行 | 任务有依赖关系 |
| 暂停主线 | pause-main | 暂停主线任务，执行临时任务 | 临时任务优先级高 |
| 暂停其他 | pause-others | 暂停其他任务 | 当前任务优先级高 |
| 合并任务 | merge | 合并相似任务 | 任务重复或相似 |
| 拒绝执行 | reject | 拒绝执行 | 任务冲突严重 |

#### 5.2.2 冲突处理流程

```
1. 接收任务请求
   ↓
2. 分析任务内容
   ↓
3. 检测与主线任务的冲突
   ↓
4. 检测与其他任务的冲突
   ↓
5. 评估冲突严重程度
   ↓
6. 选择冲突处理策略
   ↓
7. 执行冲突处理
   ↓
8. 记录冲突处理结果
```

### 5.3 冲突检测实现

```javascript
async function detectConflicts(task, existingTasks, mainGoal) {
  const conflicts = [];

  // 检测与主线任务的冲突
  const mainConflict = await detectMainConflict(task, mainGoal);
  if (mainConflict.hasConflict) {
    conflicts.push({
      type: 'main-goal',
      severity: mainConflict.severity,
      description: mainConflict.description,
      suggestion: mainConflict.suggestion
    });
  }

  // 检测与其他任务的冲突
  for (const existingTask of existingTasks) {
    if (existingTask.status === 'running' || existingTask.status === 'pending') {
      const taskConflict = await detectTaskConflict(task, existingTask);
      if (taskConflict.hasConflict) {
        conflicts.push({
          type: 'task',
          taskId: existingTask.taskId,
          severity: taskConflict.severity,
          description: taskConflict.description,
          suggestion: taskConflict.suggestion
        });
      }
    }
  }

  return conflicts;
}
```

---

## 六、任务管理功能

### 6.1 任务创建

**API**:
```javascript
async function createTask(taskConfig) {
  // 1. 生成任务 ID
  const taskId = generateTaskId();

  // 2. 检测冲突
  const conflicts = await detectConflicts(taskConfig, getActiveTasks(), getMainGoal(agentId));

  // 3. 处理冲突
  if (conflicts.length > 0) {
    const resolution = await resolveConflicts(taskConfig, conflicts);
    if (resolution.action === 'reject') {
      throw new Error(`任务被拒绝: ${resolution.reason}`);
    }
  }

  // 4. 创建任务文件
  const task = {
    taskId,
    ...taskConfig,
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    steps: parseSteps(taskConfig.steps),
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

**示例调用**:
```javascript
const task = await createTask({
  title: '诊断 RTSP 连接问题',
  description: '检查 RTSP 客户端无法连接的问题',
  agentId: 'ffmedia',
  priority: 'high',
  steps: [
    {
      title: '检查网络配置',
      description: '使用 ifconfig 和 ping 检查网络连接',
      command: 'ifconfig eth0 && ping -c 3 192.168.150.120'
    },
    {
      title: '检查设备状态',
      description: '使用 adb 检查设备是否在线',
      command: 'adb devices'
    },
    {
      title: '测试 RTSP 连接',
      description: '使用 ffplay 测试 RTSP 客户端连接',
      command: 'ffplay rtsp://127.0.0.1:8554/cam1'
    }
  ]
});
```

### 6.2 任务执行

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

      // 创建 subagent
      const subagent = await spawnSubagent(task, step);
      step.subagent = subagent;

      await saveTaskFile(task);

      // 等待 subagent 完成
      const result = await waitForSubagent(subagent.sessionKey);

      // 更新步骤状态
      step.status = result.success ? 'completed' : 'failed';
      step.completedAt = new Date().toISOString();
      step.subagent.result = result.output;
      step.subagent.tokens = result.tokens;

      await saveTaskFile(task);

      // 如果步骤失败，决定是否继续
      if (!result.success && !result.continueOnError) {
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

**Subagent 创建**:
```javascript
async function spawnSubagent(task, step) {
  const sessionKey = `agent:${task.agentId}:task:${task.taskId}:step:${step.stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`;

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
    label: sessionKey
  });

  return {
    sessionId: subagent.sessionId,
    sessionKey,
    label: sessionKey
  };
}
```

### 6.3 任务查询

#### 6.3.1 查询单个任务

**API**:
```javascript
async function getTask(taskId) {
  const task = await loadTask(taskId);
  return task;
}
```

#### 6.3.2 查询 Agent 的所有任务

**API**:
```javascript
async function getTasksByAgent(agentId, status = null) {
  const registry = await loadTaskRegistry();
  const taskIds = Object.keys(registry.tasks)
    .filter(id => registry.tasks[id].agentId === agentId)
    .filter(id => !status || registry.tasks[id].status === status);

  const tasks = await Promise.all(taskIds.map(id => loadTask(id)));
  return tasks;
}
```

#### 6.3.3 查询任务历史

**API**:
```javascript
async function getTaskHistory(taskId) {
  const task = await loadTask(taskId);
  const history = await loadTaskHistory();

  // 从历史记录中提取相关条目
  const taskHistory = history.filter(entry => entry.taskId === taskId);
  return taskHistory;
}
```

### 6.4 任务暂停和恢复

**API**:
```javascript
async function pauseTask(taskId, reason) {
  const task = await loadTask(taskId);

  // 如果任务正在执行，需要停止当前 subagent
  if (task.status === 'running') {
    const currentStep = task.steps.find(s => s.status === 'running');
    if (currentStep && currentStep.subagent) {
      await killSubagent(currentStep.subagent.sessionKey);
    }
  }

  task.status = 'paused';
  task.pausedAt = new Date().toISOString();
  task.pauseReason = reason;

  await saveTaskFile(task);

  return task;
}

async function resumeTask(taskId) {
  const task = await loadTask(taskId);

  if (task.status !== 'paused') {
    throw new Error(`任务状态不是 paused，无法恢复`);
  }

  // 继续执行
  await executeTask(taskId);

  return task;
}
```

### 6.5 任务取消

**API**:
```javascript
async function cancelTask(taskId, reason) {
  const task = await loadTask(taskId);

  // 如果任务正在执行，需要停止当前 subagent
  if (task.status === 'running') {
    const currentStep = task.steps.find(s => s.status === 'running');
    if (currentStep && currentStep.subagent) {
      await killSubagent(currentStep.subagent.sessionKey);
    }
  }

  task.status = 'cancelled';
  task.cancelledAt = new Date().toISOString();
  task.cancelReason = reason;

  await saveTaskFile(task);

  // 归档到 failed 目录
  await moveTask(taskId, 'active', 'failed');

  return task;
}
```

---

## 七、监控集成

### 7.1 任务监控流程

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

async function checkTaskSubagents(task) {
  for (const step of task.steps) {
    if (step.status === 'running' && step.subagent) {
      const subagentStatus = await getSubagentStatus(step.subagent.sessionKey);

      if (subagentStatus === 'completed') {
        step.status = 'completed';
        step.completedAt = new Date().toISOString();
      } else if (subagentStatus === 'failed') {
        step.status = 'failed';
        step.completedAt = new Date().toISOString();
      }
    }
  }
}
```

### 7.2 任务状态报告

在监控报告中添加任务信息：

```markdown
## 任务状态

### ffmedia

**活跃任务**: 2

| 任务 ID | 标题 | 状态 | 进度 | 创建时间 |
|---------|------|------|------|---------|
| task-001 | 诊断 RTSP 连接问题 | 🔄 执行中 | 2/3 | 2026-03-03 10:30 |
| task-002 | 修复 RTSP 客户端错误 | ⏳ 待执行 | 0/3 | 2026-03-03 10:45 |

### agentmesh

**活跃任务**: 0

### Ai-StockAssistant

**活跃任务**: 1

| 任务 ID | 标题 | 状态 | 进度 | 创建时间 |
|---------|------|------|------|---------|
| task-003 | 检查上周预测结果 | 🔄 执行中 | 1/2 | 2026-03-03 09:00 |
```

---

## 八、与当前实现的集成

### 8.1 修改 AGENT-STATES.md

添加任务信息列：

```markdown
## 状态总览

| Agent | 状态 | 最后活动 | 停滞时长 | 活跃任务 | 阻塞原因 |
|-------|------|---------|---------|---------|---------|
| ffmedia | 🟢 normal | 10 分钟前 | - | 2 个任务 | - |
| agentmesh | 🟢 normal | 21 小时前 | 1260 分钟 | 0 个任务 | - |
| Ai-StockAssistant | 🟢 normal | 5 分钟前 | - | 1 个任务 | - |
```

### 8.2 修改 MONITOR-LOG.md

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

### 8.3 修改 monitor-simple.js

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

  return mainStatus;
}
```

---

## 九、实现路线图

### 9.1 Phase 1: 基础框架（1-2 天）

- [ ] 创建任务目录结构
- [ ] 实现任务配置文件格式
- [ ] 实现任务注册表
- [ ] 实现任务创建 API
- [ ] 实现任务查询 API

### 9.2 Phase 2: 任务执行（2-3 天）

- [ ] 实现任务执行 API
- [ ] 实现 subagent 创建和命名
- [ ] 实现步骤执行流程
- [ ] 实现任务结果汇总

### 9.3 Phase 3: 冲突检测（2-3 天）

- [ ] 实现冲突检测逻辑
- [ ] 实现冲突处理策略
- [ ] 实现冲突解决流程
- [ ] 添加冲突报告

### 9.4 Phase 4: 监控集成（1-2 天）

- [ ] 在监控脚本中添加任务检查
- [ ] 更新 AGENT-STATES.md 格式
- [ ] 更新 MONITOR-LOG.md 格式
- [ ] 实现任务超时检测

### 9.5 Phase 5: 高级功能（3-5 天）

- [ ] 实现任务暂停和恢复
- [ ] 实现任务取消
- [ ] 实现任务归档
- [ ] 实现任务历史查询
- [ ] 实现任务统计和报告

---

## 十、使用示例

### 10.1 创建任务

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

### 10.2 查询任务

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

### 10.3 查询任务历史

```javascript
// 用户查询任务历史
"Stone，查询 task-001 的历史"

// Stone 处理
const history = await getTaskHistory('task-001');

for (const entry of history) {
  console.log(`[${entry.timestamp}] ${entry.action}`);
  console.log(`  ${entry.description}`);
}
```

---

## 十一、注意事项

### 11.1 避免冲突

1. **任务优先级**: 高优先级任务优先执行
2. **冲突检测**: 创建任务前检测冲突
3. **资源隔离**: 每个任务使用独立的 subagent
4. **状态同步**: 实时更新任务状态

### 11.2 性能优化

1. **任务队列**: 使用队列管理任务执行顺序
2. **并发控制**: 限制同时执行的任务数量
3. **缓存**: 缓存任务注册表，减少 I/O
4. **异步处理**: 使用异步执行提高性能

### 11.3 错误处理

1. **重试机制**: 失败的步骤自动重试
2. **超时处理**: 超时的任务自动取消
3. **错误日志**: 记录所有错误信息
4. **用户通知**: 及时通知用户任务状态

---

## 十二、总结

本设计提供了一个完整的任务管理系统，支持：

✅ 任务创建、执行、查询
✅ 冲突检测和处理
✅ Subagent 命名和上下文记忆
✅ 监控集成
✅ 与当前 Stone 实现的无缝集成

**下一步**: 开始 Phase 1 实现（基础框架）

---

**设计人**: Stone Agent 🗿
**设计时间**: 2026-03-03 10:56
**版本**: v1.0
