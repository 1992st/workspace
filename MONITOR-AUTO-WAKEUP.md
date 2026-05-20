# Stone 监控 - 自动唤醒机制全面检查

## 检查时间
2026-03-03 20:24

---

## 📋 当前机制分析

### 监控流程（10 步）

```
第 1 步：读取 AGENT-SESSIONS.md
  ↓
第 2 步：使用 subagents list 检查 Stone 启动的 subagents
  ↓
第 3 步：读取各个 Agents 的 session 文件并综合状态
  ↓
第 4 步：分析各个 Agents 的最新活动和任务进度
  ↓
第 5 步：记录 subagents 的任务结果到 MONITOR-LOG.md
  ↓
第 6 步：更新 AGENT-STATES.md
  ↓
第 7 步：检测偏离和暂停 ⭐ 关键步骤
  ↓
第 8 步：判断是否需要发送消息（智能静默）
  ↓
第 9 步：如果需要，发送消息（当前未实现）⚠️
  ↓
第 10 步：更新 AGENT-STATES.md 和 MONITOR-LOG.md
```

### 问题识别

**第 7 步：检测偏离和暂停**
- ✅ 正确检测 agent abort 或 stopped
- ✅ 正确计算停滞时长
- ✅ 正确判断是否需要干预

**第 8 步：智能静默**
- ✅ 正确判断是否需要发送消息
- ✅ 避免过度打扰

**第 9 步：发送消息（⚠️ 缺失）**
- ❌ **未集成 `stone-msg.sh` 脚本**
- ❌ **未实现自动唤醒**
- ❌ **依赖手动执行或外部调用**

---

## 🔍 问题详情

### 当前实现

#### detectInterventions() 函数

**功能**: 检测需要干预的情况

**触发条件**:
```javascript
// 条件 1: Agent aborted（main session）
if (status.status === 'aborted' && status.statusSource === 'main-session') {
  // 需要唤醒
}

// 条件 2: Agent stopped 超过阈值 2 倍（main session）
if (status.status === 'stopped' && status.statusSource === 'main-session') {
  // 需要检查
}
```

**输出**: 返回需要干预的 agent 列表

#### executeIntervention() 函数

**当前实现**: 使用 `/v1/sessions/spawn` 创建子 agent

**问题**:
```javascript
// ❌ 当前实现（错误的方式）
const apiUrl = 'http://127.0.0.1:18789/v1/sessions/spawn';
const requestBody = {
  agentId: agent,
  task: task,
  mode: 'session',
  thread: true,
  label: `stone-wakeup-${agent}`,
};

// 使用 curl 调用
const curlCmd = `curl -s -X POST "${apiUrl}" ...`;
```

**问题**:
1. ❌ 使用了错误的端点（`/v1/sessions/spawn` 而不是 `/v1/responses`）
2. ❌ 创建了子 agent 而不是唤醒主 session
3. ❌ 没有使用 `stone-msg.sh` 脚本

---

## ✅ 正确的实现方式

### 应该使用 stone-msg.sh 脚本

#### 方式 1：直接调用脚本（推荐）

```javascript
/**
 * 执行自动干预（使用 stone-msg.sh）
 */
async function executeIntervention(intervention) {
  const { agent, reason, suggestion } = intervention;

  console.log(`\n  🔄 [stone-msg.sh] 唤醒 ${agent}...`);
  console.log(`  📝 原因: ${reason}`);
  console.log(`  💡 建议: ${suggestion}`);

  try {
    // 1. 记录干预到文件
    await recordIntervention(intervention);

    // 2. 生成唤醒消息
    const wakeupMessage = `自动唤醒：${suggestion}\n\n唤醒时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}\n唤醒原因: ${reason}`;

    // 3. 使用 stone-msg.sh 发送消息 ⭐ 关键修改
    const stoneMsgScript = '/Volumes/zhangstExtern/openclaw/workspace/stone/scripts/stone-msg.sh';
    const cmd = `"${stoneMsgScript}" "${agent}" "${wakeupMessage}"`;

    console.log(`  📤 发送唤醒消息...`);

    // 4. 执行脚本
    const { stdout, stderr } = await exec(cmd, {
      timeout: 300000, // 5 分钟超时
      cwd: '/Volumes/zhangstExtern/openclaw/workspace/stone',
    });

    console.log(`  ✅ Agent ${agent} 已唤醒`);
    console.log(`  📝 消息: ${wakeupMessage.substring(0, 100)}...`);

    // 5. 更新 AGENT-STATES.md（记录唤醒时间）
    await recordWakeup(agent, wakeupMessage);

    return { success: true, message: wakeupMessage };

  } catch (error) {
    console.log(`  ❌ 唤醒失败: ${error.message}`);
    console.log(`  ⚠️ stderr: ${error.stderr || 'N/A'}`);

    return { success: false, error: error.message };
  }
}

/**
 * 记录唤醒操作
 */
async function recordWakeup(agentId, message) {
  const timestamp = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' });

  const logEntry = `
## ${timestamp} - 唤醒 ${agentId}

### 唤醒信息
- Agent: ${agentId}
- 消息: ${message}
- 方法: stone-msg.sh
- 状态: ✅ 成功
`;

  // 添加到 MONITOR-LOG.md
  let existingLog = '';
  try {
    existingLog = await read(MONITOR_LOG, 'utf8');
  } catch (e) {
    // 文件不存在
  }

  const newLog = logEntry + '\n' + existingLog;
  await write(MONITOR_LOG, newLog);
  console.log(`  ✅ 唤醒已记录到 MONITOR-LOG.md`);
}
```

#### 方式 2：使用 sendToAgent 函数（备用）

```javascript
import { sendToAgent } from './scripts/send-to-agent.js';

/**
 * 执行自动干预（使用 sendToAgent）
 */
async function executeIntervention(intervention) {
  const { agent, reason, suggestion } = intervention;

  console.log(`\n  🔄 [sendToAgent] 唤醒 ${agent}...`);

  try {
    // 1. 记录干预到文件
    await recordIntervention(intervention);

    // 2. 生成唤醒消息
    const wakeupMessage = `自动唤醒：${suggestion}\n\n唤醒时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}\n唤醒原因: ${reason}`;

    // 3. 使用 sendToAgent 发送消息 ⭐ 备用方案
    await sendToAgent(agent, wakeupMessage);

    console.log(`  ✅ Agent ${agent} 已唤醒`);
    console.log(`  📝 消息: ${wakeupMessage.substring(0, 100)}...`);

    // 4. 更新 AGENT-STATES.md（记录唤醒时间）
    await recordWakeup(agent, wakeupMessage);

    return { success: true, message: wakeupMessage };

  } catch (error) {
    console.log(`  ❌ 唤醒失败: ${error.message}`);

    return { success: false, error: error.message };
  }
}
```

---

## 🔄 监控流程更新（完整版）

### 旧流程（第 9 步缺失）

```
第 1-8 步：...（正常流程）
  ↓
第 9 步：[❌ 缺失] 没有实现自动唤醒
  ↓
第 10 步：更新 AGENT-STATES.md 和 MONITOR-LOG.md
```

### 新流程（第 9 步已实现）

```
第 1-8 步：...（正常流程）
  ↓
第 9 步：执行自动干预（使用 stone-msg.sh）
   ├─ 9.1: 检测需要干预的 agents
   │   ├─ Agent aborted（main session）→ 需要唤醒
   │   └─ Agent stopped 超过阈值 2 倍 → 需要唤醒
   │
   ├─ 9.2: 生成唤醒消息
   │   └─ 消息格式: "自动唤醒：<任务描述>"
   │
   ├─ 9.3: 使用 stone-msg.sh 发送消息
   │   └─ 命令: ./scripts/stone-msg.sh <agentId> "<message>"
   │
   ├─ 9.4: 等待 Gateway 响应（2-4 分钟）
   │
   ├─ 9.5: 记录唤醒操作
   │   ├─ 更新 AGENT-STATES.md（记录唤醒时间）
   │   └─ 更新 MONITOR-LOG.md（记录消息内容）
   │
   └─ 9.6: 返回唤醒结果
       └─ 成功/失败状态
  ↓
第 10 步：更新 AGENT-STATES.md 和 MONITOR-LOG.md
```

---

## 📋 修改建议

### 方案 1：修改 monitor-simple.js（推荐）

**步骤**:
1. 备份现有文件
2. 替换 `executeIntervention()` 函数
3. 添加 `recordWakeup()` 函数
4. 测试验证

**修改位置**: `monitor-simple.js` 第 650 行左右

**修改内容**:
- 删除旧的 `executeIntervention()` 函数（使用 `/v1/sessions/spawn`）
- 添加新的 `executeIntervention()` 函数（使用 `stone-msg.sh`）
- 添加 `recordWakeup()` 函数

### 方案 2：创建新的监控脚本（备用）

**步骤**:
1. 创建 `monitor-auto-wakeup.js`
2. 实现自动唤醒逻辑
3. 替换 `monitor-simple.js`

**优势**:
- 不影响现有监控脚本
- 可以并行测试
- 失败时可以快速回滚

---

## 🎯 修改后的完整流程

### 主监控函数

```javascript
async function runMonitoring() {
  console.log('\n' + '='.repeat(50));
  console.log('  🗿 Stone 监控');
  console.log('='.repeat(50));

  const report = {
    timestamp: new Date().toISOString(),
    agents: {},
  };

  // 第 1 步：读取各个 Agents 的 session 文件
  for (const [agentId, config] of Object.entries(AGENTS)) {
    const status = await checkAgent(agentId, config);
    report.agents[agentId] = status;
  }

  // 第 2 步：更新 AGENT-STATES.md
  await updateAgentStates(report);

  // 第 3 步：记录到 MONITOR-LOG.md
  await logToMonitorLog(report);

  // 第 4 步：生成报告
  generateReport(report);

  // 第 5 步：检测需要干预的情况 ⭐ 关键步骤
  const interventions = detectInterventions(report);

  if (interventions.length > 0) {
    console.log('\n  ⚠️ 检测到需要干预的情况:');
    interventions.forEach(intervention => {
      console.log(`    - ${intervention.agent}: ${intervention.reason}`);
    });

    // 第 6 步：执行自动干预（使用 stone-msg.sh）⭐ 新增
    for (const intervention of interventions) {
      const result = await executeIntervention(intervention);
      if (result.success) {
        console.log(`  ✅ ${intervention.agent} 已自动唤醒`);
      } else {
        console.log(`  ❌ ${intervention.agent} 唤醒失败: ${result.error}`);
      }
    }
  } else {
    console.log('\n  ✅ 所有 Agents 运行正常，无需干预');
  }
}
```

---

## 📊 修改对比

### 旧实现

```javascript
// ❌ 错误：使用 sessions_spawn
const apiUrl = 'http://127.0.0.1:18789/v1/sessions/spawn';
const curlCmd = `curl -s -X POST "${apiUrl}" ...`;

// 问题：
// 1. 创建子 agent（不是唤醒主 session）
// 2. 没有使用 stone-msg.sh 脚本
// 3. 没有持久化到主 session 历史
```

### 新实现

```javascript
// ✅ 正确：使用 stone-msg.sh
const stoneMsgScript = '/Volumes/zhangstExtern/openclaw/workspace/stone/scripts/stone-msg.sh';
const cmd = `"${stoneMsgScript}" "${agent}" "${wakeupMessage}"`;

// 优势：
// 1. 唤醒主 session（不是创建子 agent）
// 2. 使用 stone-msg.sh 脚本
// 3. 消息持久化到 session 历史
```

---

## ✅ 预期效果

### 修改前

```
监控检测到 ffmedia abort
  ↓
生成干预报告
  ↓
❌ 没有自动唤醒
  ↓
等待手动执行 stone-msg.sh
```

### 修改后

```
监控检测到 ffmedia abort
  ↓
生成干预报告
  ↓
✅ 自动执行 stone-msg.sh 唤醒
  ↓
ffmedia 接收到消息并继续执行
  ↓
记录唤醒操作到 AGENT-STATES.md 和 MONITOR-LOG.md
```

---

## 📝 测试计划

### 测试 1：Agent Abort 场景

**步骤**:
1. 手动停止 ffmedia agent
2. 运行监控脚本
3. 观察是否自动唤醒

**预期结果**:
- ✅ 检测到 ffmedia abort
- ✅ 自动执行 stone-msg.sh
- ✅ ffmedia 接收到消息
- ✅ 记录到 MONITOR-LOG.md

### 测试 2：Agent Stopped 场景

**步骤**:
1. 让 ffmedia 停止（不 abort）
2. 等待超过阈值 2 倍
3. 运行监控脚本
4. 观察是否自动唤醒

**预期结果**:
- ✅ 检测到 ffmedia stopped 超过阈值
- ✅ 自动执行 stone-msg.sh
- ✅ ffmedia 接收到消息
- ✅ 记录到 MONITOR-LOG.md

---

## 🚀 下一步行动

### 立即行动

1. **修改 monitor-simple.js**
   - 替换 `executeIntervention()` 函数
   - 添加 `recordWakeup()` 函数
   - 测试验证

2. **更新文档**
   - 更新 AGENTS.md（记录新的监控流程）
   - 更新 MONITORING-UPDATED.md

### 后续优化

1. **添加重试机制**
   - 如果 stone-msg.sh 失败，重试 3 次
   - 每次重试间隔 1 分钟

2. **添加飞书通知**
   - 唤醒成功后发送飞书通知
   - 便于用户跟踪

3. **添加降级方案**
   - 如果 stone-msg.sh 失败，尝试 sessions_spawn

---

## 总结

### 核心问题

❌ **当前问题**: 监控脚本未集成 `stone-msg.sh`，无法自动唤醒 agent

### 解决方案

✅ **修改方案**: 替换 `executeIntervention()` 函数，使用 `stone-msg.sh` 脚本

### 关键改进

1. ✅ **自动唤醒**: 检测到 abort 或暂停时自动执行 stone-msg.sh
2. ✅ **正确方式**: 唤醒主 session，不是创建子 agent
3. ✅ **持久化**: 消息记录到 session 历史
4. ✅ **日志记录**: 记录唤醒操作到 AGENT-STATES.md 和 MONITOR-LOG.md

---

**Stone Agent** 🗿
**检查时间**: 2026-03-03 20:24
**文档版本**: v1.0
