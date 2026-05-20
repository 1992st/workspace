# Stone 任务管理系统 - OpenClaw 集成指南

## 📋 文档信息

- **版本**: v1.0
- **创建日期**: 2026-03-03 11:15
- **目的**: 指导如何正确使用 OpenClaw 工具实现任务管理系统

---

## 一、OpenClaw 工具概述

### 1.1 可用工具

| 工具 | 用途 | 在任务系统中的应用 |
|------|------|-----------------|
| `sessions_spawn` | 创建子 Agent 执行任务 | 创建 subagent 执行任务步骤 |
| `sessions_list` | 列出所有 sessions | 查询 subagents 状态 |
| `sessions_history` | 查询 session 历史 | 检查 subagent 执行结果 |
| `sessions_send` | 向 session 发送消息 | （可选）向 agent 发送恢复指令 |

### 1.2 工具调用方式

**方式 1: 通过 OpenClaw 工具函数**（推荐）:
```javascript
import { sessions_spawn, sessions_list, sessions_history } from 'openclaw';

// 创建 subagent
const subagent = await sessions_spawn({...});

// 查询 subagents
const sessions = await sessions_list({...});

// 查询历史
const history = await sessions_history({...});
```

**方式 2: 通过 HTTP API**（备选）:
```bash
curl -X POST http://127.0.0.1:18789/v1/responses \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"model": "openclaw", "input": "任务描述"}'
```

---

## 二、sessions_spawn 使用指南

### 2.1 基本用法

**创建 subagent 执行任务**:
```javascript
const subagent = await sessions_spawn({
  agentId: 'ffmedia',
  mode: 'run',
  task: '检查网络配置'
});
```

### 2.2 参数详解

#### agentId

**类型**: `string`

**说明**: Agent ID，指定要创建子 agent 的父 agent

**示例**:
```javascript
agentId: 'ffmedia'        // ffmedia agent
agentId: 'agentmesh'     // agentmesh agent
agentId: 'Ai-StockAssistant'  // Ai-StockAssistant agent
```

#### mode

**类型**: `'run'` | `'session'`

**说明**: 执行模式

| 模式 | 说明 | 生命周期 |
|------|------|---------|
| `run` | 一次性任务，执行完成后自动结束 | 临时 |
| `session` | 持久 session，可以多次交互 | 持久 |

**示例**:
```javascript
mode: 'run'       // 一次性任务（推荐）
mode: 'session'   // 持久 session
```

#### task

**类型**: `string`

**说明**: 任务描述，发送给 subagent 的初始消息

**示例**:
```javascript
task: '检查网络配置'

// 或者更详细的描述
task: `
任务上下文：
- 任务 ID: ${task.taskId}
- 任务标题: ${task.title}

当前步骤：
- 步骤 ID: ${step.stepId}
- 步骤标题: ${step.title}
- 步骤描述: ${step.description}

请执行此步骤，并在完成后报告结果。
`.trim()
```

#### label

**类型**: `string` (可选)

**说明**: 可读标签，用于识别和查询 subagent

**示例**:
```javascript
label: `task:${task.taskId}:step:${step.stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`

// 示例: task:001:step:001:check-network
```

**注意**:
- ✅ 推荐：使用 label 指定可读标签
- ⚠️ 最大长度：OpenClaw 可能有长度限制（建议 < 100 字符）
- ✅ 格式：`task:<taskId>:step:<stepId>:<description>`

#### runtime

**类型**: `'subagent'` | `'acp'` (可选)

**说明**: 运行时类型

| 运行时 | 说明 |
|--------|------|
| `subagent` | 子 agent（默认） |
| `acp` | ACP 编码会话 |

**示例**:
```javascript
runtime: 'subagent'  // 子 agent（默认）
```

#### model

**类型**: `string` (可选)

**说明**: 使用的模型

**示例**:
```javascript
model: 'zai/glm-4.7'  // GLM 模型
model: 'gpt-4'       // GPT-4 模型
```

### 2.3 返回值

**格式**:
```javascript
{
  sessionId: "123e4567-e89b-12d3-a456-426614174000",  // OpenClaw 自动生成的 UUID
  label: "task:001:step:001:check-network"        // 可读标签（如果指定）
}
```

**字段说明**:
- `sessionId`: Subagent 的唯一 ID（UUID 格式）
- `label`: Subagent 的标签（如果指定）

### 2.4 使用示例

**示例 1: 简单任务**
```javascript
const subagent = await sessions_spawn({
  agentId: 'ffmedia',
  mode: 'run',
  task: '检查网络配置',
  label: 'task:001:step:001:check-network'
});

console.log(`Subagent ID: ${subagent.sessionId}`);
console.log(`Subagent Label: ${subagent.label}`);
```

**示例 2: 详细任务描述**
```javascript
const task = {
  taskId: 'task-001',
  title: '诊断 RTSP 连接问题',
  description: '检查 RTSP 客户端无法连接的问题'
};

const step = {
  stepId: '001',
  title: '检查网络配置',
  description: '使用 ifconfig 和 ping 检查网络连接'
};

const subagent = await sessions_spawn({
  agentId: 'ffmedia',
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

---

## 三、sessions_list 使用指南

### 3.1 基本用法

**列出所有 sessions**:
```javascript
const sessions = await sessions_list({
  kinds: ['subagent'],
  activeMinutes: 30
});
```

### 3.2 参数详解

#### kinds

**类型**: `string[]`

**说明**: Session 类型过滤

**值**:
- `subagent`: 仅列出 subagents
- `agent`: 仅列出 agents
- `all`: 列出所有（默认）

**示例**:
```javascript
kinds: ['subagent']  // 仅列出 subagents
kinds: ['agent']     // 仅列出 agents
kinds: ['subagent', 'agent']  // 列出 subagents 和 agents
kinds: []            // 列出所有
```

#### activeMinutes

**类型**: `number` (可选)

**说明**: 仅返回指定分钟内活跃的 sessions

**示例**:
```javascript
activeMinutes: 30   // 最近 30 分钟内活跃的 sessions
activeMinutes: 60   // 最近 1 小时内活跃的 sessions
```

#### limit

**类型**: `number` (可选)

**说明**: 返回的最大 session 数量

**示例**:
```javascript
limit: 10  // 最多返回 10 个 sessions
```

### 3.3 返回值

**格式**:
```javascript
[
  {
    sessionId: "123e4567-e89b-12d3-a456-426614174000",
    label: "task:001:step:001:check-network",
    agentId: "ffmedia",
    createdAt: "2026-03-03T10:30:00.000Z",
    lastActivity: "2026-03-03T10:35:00.000Z",
    status: "completed",
    kind: "subagent"
  },
  {
    sessionId: "234f5678-f90c-23e4-b567-537725285111",
    label: "task:001:step:002:check-device",
    agentId: "ffmedia",
    createdAt: "2026-03-03T10:35:00.000Z",
    lastActivity: "2026-03-03T10:40:00.000Z",
    status: "completed",
    kind: "subagent"
  }
]
```

**字段说明**:
- `sessionId`: Session ID
- `label`: Session 标签（如果指定）
- `agentId`: Agent ID
- `createdAt`: 创建时间
- `lastActivity`: 最后活动时间
- `status`: 状态
- `kind`: Session 类型

### 3.4 使用示例

**示例 1: 查询所有 subagents**
```javascript
const sessions = await sessions_list({
  kinds: ['subagent']
});

console.log(`Total subagents: ${sessions.length}`);
```

**示例 2: 查询最近 30 分钟内活跃的 subagents**
```javascript
const sessions = await sessions_list({
  kinds: ['subagent'],
  activeMinutes: 30
});

console.log(`Active subagents (last 30 min): ${sessions.length}`);
```

**示例 3: 查询特定任务的 subagents（通过 label 过滤）**
```javascript
const sessions = await sessions_list({
  kinds: ['subagent']
});

const taskId = 'task-001';
const taskSubagents = sessions.filter(s =>
  s.label && s.label.startsWith(`task:${taskId}:`)
);

console.log(`Task subagents: ${taskSubagents.length}`);
```

**示例 4: 查询特定步骤的 subagent**
```javascript
const sessions = await sessions_list({
  kinds: ['subagent']
});

const taskId = 'task-001';
const stepId = '001';
const stepTitle = 'check-network';

const stepSubagent = sessions.find(s =>
  s.label === `task:${taskId}:step:${stepId}:${stepTitle}`
);

if (stepSubagent) {
  console.log(`Found subagent: ${stepSubagent.sessionId}`);
}
```

---

## 四、sessions_history 使用指南

### 4.1 基本用法

**查询 session 历史**:
```javascript
const history = await sessions_history({
  sessionKey: '123e4567-e89b-12d3-a456-426614174000',
  includeTools: true
});
```

### 4.2 参数详解

#### sessionKey

**类型**: `string`

**说明**: Session ID

**示例**:
```javascript
sessionKey: '123e4567-e89b-12d3-a456-426614174000'
```

#### includeTools

**类型**: `boolean` (可选)

**说明**: 是否包含工具调用记录

**示例**:
```javascript
includeTools: true   // 包含工具调用
includeTools: false  // 不包含工具调用
```

#### limit

**类型**: `number` (可选)

**说明**: 返回的最大消息数量

**示例**:
```javascript
limit: 50  // 最多返回 50 条消息
```

### 4.3 返回值

**格式**:
```javascript
[
  {
    type: 'session',
    timestamp: '2026-03-03T10:30:00.000Z',
    message: {
      role: 'user',
      content: '检查网络配置'
    }
  },
  {
    type: 'message',
    timestamp: '2026-03-03T10:30:05.000Z',
    message: {
      role: 'assistant',
      content: '正在检查网络配置...'
    }
  },
  {
    type: 'toolResult',
    timestamp: '2026-03-03T10:31:00.000Z',
    tool: 'exec',
    result: 'eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST> ...'
  },
  {
    type: 'message',
    timestamp: '2026-03-03T10:35:00.000Z',
    message: {
      role: 'assistant',
      content: '✅ 网络配置正常，eth0 有 IP 192.168.150.120'
    }
  }
]
```

**字段说明**:
- `type`: 消息类型（session, message, toolResult）
- `timestamp`: 时间戳
- `message`: 消息内容
- `tool`: 工具名称（toolResult 类型）
- `result`: 工具结果（toolResult 类型）

### 4.4 使用示例

**示例 1: 查询 session 历史**
```javascript
const history = await sessions_history({
  sessionKey: '123e4567-e89b-12d3-a456-426614174000',
  includeTools: true
});

console.log(`Total messages: ${history.length}`);
```

**示例 2: 检查 subagent 是否完成**
```javascript
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
    console.log('Subagent completed successfully');
  } else if (content.includes('failed') ||
             content.includes('error') ||
             content.includes('❌')) {
    console.log('Subagent failed');
  }
}
```

**示例 3: 提取 subagent 执行结果**
```javascript
const history = await sessions_history({
  sessionKey: sessionId,
  includeTools: false  // 不需要工具调用
});

// 提取 assistant 的最后一条消息
const assistantMessages = history.filter(h => h.message?.role === 'assistant');
const lastAssistantMessage = assistantMessages[assistantMessages.length - 1];

if (lastAssistantMessage) {
  const result = lastAssistantMessage.message.content;
  console.log(`Subagent result: ${result}`);
}
```

---

## 五、Subagent 等待机制

### 5.1 轮询机制

**原因**: OpenClaw 不提供异步通知机制，需要通过轮询检查 subagent 状态

**实现**:
```javascript
async function waitForSubagent(sessionId, timeout = 3600000, pollInterval = 5000) {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    // 查询 subagent 历史
    const history = await sessions_history({
      sessionKey: sessionId,
      includeTools: true
    });

    // 检查最后一条消息
    const lastMessage = history[history.length - 1];
    if (lastMessage && lastMessage.message) {
      const content = lastMessage.message.message?.content || lastMessage.message.content;

      // 检查完成标记
      if (content.includes('completed') ||
          content.includes('finished') ||
          content.includes('done') ||
          content.includes('✅')) {
        return { success: true, output: content };
      }

      // 检查失败标记
      if (content.includes('failed') ||
          content.includes('error') ||
          content.includes('❌')) {
        return { success: false, output: content };
      }
    }

    // 等待一段时间后重试
    await new Promise(resolve => setTimeout(resolve, pollInterval));
  }

  // 超时
  return { success: false, output: 'Timeout' };
}
```

### 5.2 使用示例

**示例 1: 等待 subagent 完成**
```javascript
const subagent = await sessions_spawn({
  agentId: 'ffmedia',
  mode: 'run',
  task: '检查网络配置',
  label: 'task:001:step:001:check-network'
});

console.log(`Waiting for subagent: ${subagent.sessionId}`);

const result = await waitForSubagent(subagent.sessionId, 3600000, 5000);

if (result.success) {
  console.log(`✅ Subagent completed: ${result.output}`);
} else {
  console.log(`❌ Subagent failed: ${result.output}`);
}
```

**示例 2: 带超时处理的等待**
```javascript
const subagent = await sessions_spawn({
  agentId: 'ffmedia',
  mode: 'run',
  task: '检查网络配置',
  label: 'task:001:step:001:check-network'
});

try {
  const result = await waitForSubagent(subagent.sessionId, 3600000, 5000);

  if (result.success) {
    console.log(`✅ Subagent completed`);
  } else {
    throw new Error(`Subagent failed: ${result.output}`);
  }
} catch (error) {
  console.error(`❌ Error waiting for subagent: ${error.message}`);
}
```

---

## 六、最佳实践

### 6.1 Subagent 命名

**使用 label 参数指定可读标签**:
```javascript
const label = `task:${taskId}:step:${stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`;
```

**优势**:
- ✅ 易于识别和查询
- ✅ 支持批量过滤
- ✅ 便于调试

### 6.2 任务描述

**提供详细的任务描述**:
```javascript
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
`.trim()
```

**优势**:
- ✅ Subagent 有足够的上下文
- ✅ 执行结果更准确
- ✅ 便于调试

### 6.3 轮询间隔

**选择合适的轮询间隔**:
```javascript
const pollInterval = 5000;  // 5 秒（推荐）
```

**说明**:
- ✅ 5 秒间隔：平衡响应速度和资源消耗
- ⚠️ 1 秒间隔：响应快，但消耗更多资源
- ⚠️ 10 秒间隔：节省资源，但响应慢

### 6.4 超时设置

**根据任务复杂度设置超时**:
```javascript
const timeout = 3600000;  // 1 小时（默认）

// 简单任务
const timeout = 300000;  // 5 分钟

// 复杂任务
const timeout = 7200000;  // 2 小时
```

### 6.5 错误处理

**妥善处理超时和错误**:
```javascript
try {
  const result = await waitForSubagent(sessionId, timeout, pollInterval);

  if (result.success) {
    // 处理成功
  } else {
    // 处理失败
  }
} catch (error) {
  // 处理异常
  console.error(`Error: ${error.message}`);
}
```

---

## 七、常见问题

### 7.1 如何查询特定任务的 subagents？

**使用 label 过滤**:
```javascript
const sessions = await sessions_list({ kinds: ['subagent'] });
const taskId = 'task-001';
const taskSubagents = sessions.filter(s =>
  s.label && s.label.startsWith(`task:${taskId}:`)
);
```

### 7.2 如何检查 subagent 是否完成？

**检查历史消息**:
```javascript
const history = await sessions_history({ sessionKey: sessionId });
const lastMessage = history[history.length - 1];
const content = lastMessage.message?.content || '';

if (content.includes('completed') || content.includes('✅')) {
  console.log('Completed');
}
```

### 7.3 如何处理 subagent 超时？

**设置合理的超时时间**:
```javascript
const result = await waitForSubagent(sessionId, 3600000, 5000);

if (!result.success) {
  // 超时处理
  console.error('Subagent timeout');
}
```

### 7.4 如何获取 subagent 的执行结果？

**提取最后一条 assistant 消息**:
```javascript
const history = await sessions_history({
  sessionKey: sessionId,
  includeTools: false
});

const assistantMessages = history.filter(h => h.message?.role === 'assistant');
const lastAssistantMessage = assistantMessages[assistantMessages.length - 1];

const result = lastAssistantMessage.message.content;
```

---

## 八、注意事项

1. **Session Key 格式**: OpenClaw 自动生成 UUID，不支持自定义格式
2. **Label 参数**: 使用 label 指定可读标签，方便查询
3. **轮询机制**: 使用轮询检查 subagent 状态，避免阻塞
4. **超时处理**: 设置合理的超时时间，妥善处理超时情况
5. **错误处理**: 妥善处理网络错误和工具调用错误
6. **资源消耗**: 轮询间隔不宜过短，避免消耗过多资源

---

**文档版本**: v1.0
**最后更新**: 2026-03-03 11:15
**维护人**: Stone Agent 🗿
