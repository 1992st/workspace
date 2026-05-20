# ContextBuilder - 历史上下文继承方案

## 问题

**用户提问**：

> 优化一下 prompt, subagent 起来的时候, 把上一个 session 的路径给他, 让他继承上下文来执行. 但是有个问题, 比如 ffmedia abort 了, 起了一个 subagent1, subagent1 结束后, 又起了一个 subagent2. 有办法让 subagentN 继承前面所有的记忆吗?

**核心问题**：
- ✅ subagent2 能继承主 session 的上下文
- ❌ subagent2 **不能**继承 subagent1 的上下文（失败的尝试）
- ❌ subagent3 **不能**继承 subagent1 和 subagent2 的所有上下文

---

## 解决方案

### ContextBuilder - 历史上下文累积器

**功能**：
1. 从 AGENTS.md 读取最新状态
2. 从 MONITOR-LOG.md 读取所有监控记录
3. 从失败 session 文件读取摘要
4. 组装成完整的上下文摘要
5. 在 prompt 中传递给 subagent

---

## 工作原理

### 传统方式（无 ContextBuilder）

```
ffmedia 主 session
  ↓
subagent1 (失败 - 缺少 libffmedia.so)
  ↓  ❌ 上下文丢失
subagent2 (继续)
  ↓  ❌ 上下文丢失
subagent3 (再继续)
  ↓  ❌ 上下文丢失
```

**问题**：
- subagent2 不知道 subagent1 做了什么
- subagent3 不知道 subagent1 和 subagent2 做了什么
- 可能重复执行相同的操作
- 无法从之前的错误中学习

---

### ContextBuilder 方式

```
Stone 监控
  ↓
检测到需要唤醒 ffmedia
  ↓
ContextBuilder.buildTaskPrompt()
  ├─ 读取 AGENTS.md → 当前状态
  ├─ 读取 MONITOR-LOG.md → 历史记录
  ├─ 读取失败 session → 失败尝试
  └─ 组装上下文摘要
  ↓
subagentN (接收完整上下文)
  ├─ 知道 subagent1 做了什么
  ├─ 知道 subagent2 做了什么
  ├─ 避免重复操作
  └─ 从错误中学习
```

**优势**：
- ✅ subagentN 知道之前所有失败的尝试
- ✅ subagentN 避免重复执行相同的操作
- ✅ subagentN 可以从之前的错误中学习
- ✅ subagentN 基于历史上下文做出智能决策

---

## 实施步骤

### 步骤 1：创建 ContextBuilder 模块

**文件**: `modules/context-builder.js`

**核心方法**：

```javascript
class ContextBuilder {
  /**
   * 构建 agent 的完整上下文
   */
  async buildContext(agentId) {
    const context = {
      agentId,
      currentStatus: null,
      historySummary: '',
      failedAttempts: [],
      recentErrors: [],
    };

    // 1. 读取 AGENTS.md 获取当前状态
    context.currentStatus = await this.readAgentStatus(agentId);

    // 2. 读取 MONITOR-LOG.md 获取历史记录
    context.historySummary = await this.readHistorySummary(agentId);

    // 3. 读取失败 session 的摘要
    context.failedAttempts = await this.readFailedSessions(agentId);

    // 4. 提取最近的错误信息
    context.recentErrors = this.extractRecentErrors(context);

    return context;
  }

  /**
   * 构建任务 prompt
   */
  async buildTaskPrompt(agentId, task) {
    const context = await this.buildContext(agentId);

    let prompt = `## 历史上下文摘要\n\n`;

    // 当前状态
    if (context.currentStatus) {
      prompt += `### 当前状态\n`;
      prompt += `- **状态**: ${context.currentStatus.status}\n`;
      prompt += `- **最后活动**: ${context.currentStatus.lastActivity}\n`;
      prompt += `- **最后任务**: ${context.currentStatus.lastTask}\n\n`;
    }

    // 失败尝试
    if (context.failedAttempts.length > 0) {
      prompt += `### 之前的尝试 (${context.failedAttempts.length} 次)\n\n`;
      for (const attempt of context.failedAttempts) {
        prompt += `#### 尝试: ${attempt.sessionId}\n`;
        prompt += `- **结果**: ${attempt.result}\n`;
        if (attempt.lastTask) {
          prompt += `- **任务**: ${attempt.lastTask}\n`;
        }
        if (attempt.errors) {
          prompt += `- **错误**:\n`;
          for (const error of attempt.errors) {
            prompt += `  - ${error}\n`;
          }
        }
        prompt += `\n`;
      }
    }

    // 最近的错误
    if (context.recentErrors.length > 0) {
      prompt += `### 最近的错误\n\n`;
      for (const error of context.recentErrors) {
        prompt += `- ${error}\n`;
      }
      prompt += `\n`;
    }

    // 新任务
    prompt += `---\n\n## 你的任务\n\n`;
    prompt += task;
    prompt += `\n\n### 重要提示\n`;
    prompt += `- 你已经知道之前的所有失败尝试和错误\n`;
    prompt += `- 避免重复之前的错误操作\n`;
    prompt += `- 基于"历史上下文摘要"中的信息，采用不同的策略\n`;
    prompt += `- 如果遇到相同的问题，尝试不同的解决方法\n`;

    return prompt;
  }
}
```

---

### 步骤 2：在 WakeupManager 中使用

**文件**: `modules/wakeup-manager.js`

```javascript
import ContextBuilder from './context-builder.js';

class WakeupManager {
  constructor(stone) {
    this.contextBuilder = new ContextBuilder();
  }

  async spawnAgent(agentId, task) {
    // 🔧 使用 ContextBuilder 构建增强的任务 prompt
    const enhancedTask = await this.contextBuilder.buildTaskPrompt(agentId, task);

    console.log(`\n📝 构建增强的任务 prompt (包含历史上下文)...`);

    const result = await sessions_spawn({
      agentId: agentId,
      task: enhancedTask,  // ✅ 使用增强的任务
      mode: 'session',
      thread: true,
      label: `stone-wakeup-${agentId}`,
      runTimeoutSeconds: 1800,
    });

    return result;
  }
}
```

---

### 步骤 3：在 monitor-simple.js 中使用

**文件**: `monitor-simple.js`

```javascript
import('./modules/context-builder.js').then(({ default: ContextBuilder }) => {
  global.ContextBuilder = ContextBuilder;
  runStoneMonitoring();
}).catch(error => {
  console.error('Failed to import ContextBuilder:', error);
  process.exit(1);
});

async function executeIntervention(intervention) {
  const { agent, reason, suggestion } = intervention;

  // 初始化 ContextBuilder
  const contextBuilder = new ContextBuilder();

  // 构建基础任务
  const baseTask = `${suggestion}\n\n任务时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`;

  // 🔧 构建增强的任务 prompt
  const enhancedTask = await contextBuilder.buildTaskPrompt(agent, baseTask);

  const requestBody = {
    agentId: agent,
    task: enhancedTask,  // ✅ 使用增强的任务（包含历史上下文）
    mode: 'session',
    thread: true,
    label: `stone-wakeup-${agent}`,
    runTimeoutSeconds: 1800,
  };

  // 调用 Gateway HTTP API
  const response = await callGatewayAPI(requestBody);

  return response;
}
```

---

## 示例输出

### 增强后的 prompt 示例

```
## 历史上下文摘要

### 当前状态
- **状态**: 🔴 阻塞
- **最后活动**: 2026-03-02 10:18
- **最后任务**: 继续测试 demo_rtsp_multi_splice

### 之前的尝试 (3 次)

#### 尝试: bd6654e5-985d-4fc4-97d4-f448ccef63ed
- **结果**: aborted
- **任务**: 从编译服务器下载代码...
- **错误**:
  - libffmedia.so: cannot open shared object file

#### 尝试: ceb28b68-6af2-496c-a62d-433cd6313830
- **结果**: aborted
- **任务**: 尝试推送 libffmedia.so...
- **错误**:
  - adb: error: failed to copy

#### 尝试: 62f86e1a-8e74-43c8-aadd-491ff26b4f98
- **结果**: aborted
- **任务**: 检查设备状态...
- **错误**:
  - devices: offline

### 最近的错误
- libffmedia.so: cannot open shared object file
- adb: error: failed to copy
- devices: offline

---

## 你的任务

设备已恢复（adb devices 显示 device），继续之前的任务：

1. 重新部署代码到 RK3588（如果需要）
2. 启动 4 个 RTSP 服务器
3. 运行 demo_rtsp_multi_splice 测试
4. 使用 VLC 播放 rtsp://192.168.150.120:9997/live/test 验证输出
5. 如果进程停止，分析原因

### 重要提示
- 你已经知道之前的所有失败尝试和错误
- 避免重复之前的错误操作
- 基于"历史上下文摘要"中的信息，采用不同的策略
- 如果遇到相同的问题，尝试不同的解决方法
```

---

## 效果对比

### 无 ContextBuilder

```
subagent1: 尝试启动 demo_rtsp_multi_splice
  → 错误：缺少 libffmedia.so
  → abort

subagent2: 继续任务
  → ❓ 不知道 subagent1 做了什么
  → 重复执行相同的操作
  → 错误：缺少 libffmedia.so
  → abort

subagent3: 继续任务
  → ❓ 不知道 subagent1 和 subagent2 做了什么
  → 重复执行相同的操作
  → 错误：缺少 libffmedia.so
  → abort
```

**结果**：
- ❌ 重复执行相同的操作
- ❌ 无法从错误中学习
- ❌ 持续失败

---

### 有 ContextBuilder

```
subagent1: 尝试启动 demo_rtsp_multi_splice
  → 错误：缺少 libffmedia.so
  → abort

subagent2: 继续任务
  → ✅ 知道 subagent1 尝试过启动
  → ✅ 知道缺少 libffmedia.so
  → 跳过启动，直接获取 libffmedia.so
  → 错误：adb push 失败
  → abort

subagent3: 继续任务
  → ✅ 知道 subagent1 尝试过启动
  → ✅ 知道 subagent2 尝试过推送
  → ✅ 跳过启动和推送
  → 检查设备状态
  → 设备 offline
  → 等待用户修复

subagent4: 继续任务（用户修复后）
  → ✅ 知道 subagent1-3 的所有尝试
  → ✅ 设备已恢复
  → 重新开始完整的测试流程
  → ✅ 成功
```

**结果**：
- ✅ 不重复执行相同的操作
- ✅ 从错误中学习
- ✅ 基于历史上下文做出智能决策
- ✅ 最终成功

---

## 配置选项

### 读取失败 session 的数量

```javascript
// 取最近 N 个
const recentFiles = fileStats.slice(0, N);
```

默认：10 个

---

### 读取 session 摘要的行数

```javascript
// 取最后 N 行
const recentLines = lines.slice(-N);
```

默认：50 行

---

### 读取 MONITOR-LOG.md 的记录数

```javascript
// 取最近 N 条记录
const recentSections = relevantSections.slice(-N);
```

默认：5 条

---

## 最佳实践

### 1. 定期更新 AGENTS.md

在 AGENTS.md 中手动更新关键信息：

```markdown
## ffmedia

### 当前状态：🔄 运行中

**最后任务**: 继续测试 demo_rtsp_multi_splice

**最新进展**:
- ✅ 设备已恢复
- ✅ 代码已部署
- 🔄 正在启动 RTSP 服务器
```

---

### 2. 限制历史上下文的长度

通过修改配置来限制历史上下文的长度：

```javascript
// 只读取最近 3 个失败的 session
const recentFiles = fileStats.slice(0, 3);

// 只读取最近 20 行
const recentLines = lines.slice(-20);

// 只读取最近 3 条监控记录
const recentSections = relevantSections.slice(-3);
```

---

### 3. 监控 Token 使用

监控 prompt 的长度，避免超过模型的 token 限制：

```javascript
const task = await contextBuilder.buildTaskPrompt(agentId, baseTask);
console.log(`📝 任务长度: ${task.length} 字符`);

// 如果太长，可以截断
const maxLength = 10000;
const trimmedTask = task.length > maxLength ? task.substring(0, maxLength) + '...' : task;
```

---

## 总结

**ContextBuilder** 是 Stone 的核心功能，确保：

1. ✅ subagentN 继承之前所有失败尝试的记忆
2. ✅ subagentN 避免重复操作
3. ✅ subagentN 从错误中学习
4. ✅ subagentN 基于历史上下文做出智能决策

**最终效果**：

```
subagent1 (失败) → subagent2 (知道 subagent1) → subagent3 (知道 subagent1 和 subagent2) → ... → subagentN (知道所有之前的尝试)
```

每个 subagent 都有完整的上下文，可以智能地继续执行任务。

---

**相关文档**:
- `docs/CONTEXT-BUILDER.md` - 详细使用指南
- `modules/context-builder.js` - 核心实现
- `modules/wakeup-manager.js` - WakeupManager 集成
- `monitor-simple.js` - 监控脚本集成
