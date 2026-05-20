#!/usr/bin/env node
/**
 * Stone 任务管理器（Task Manager）v2.0
 *
 * 功能：
 * 1. 创建任务
 * 2. 执行任务（通过 subagent）
 * 3. 查询任务
 * 4. 监控任务
 * 5. 冲突检测
 * 6. 高级功能（暂停/恢复/取消/归档）
 *
 * 集成 OpenClaw 工具：
 * - sessions_spawn: 创建 subagent
 * - sessions_list: 查询 subagents
 * - sessions_history: 查询 subagent 历史
 */

import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';

// ============================================================================
// 配置
// ============================================================================

const TASK_DIR = path.join(process.cwd(), 'tasks');
const TASK_REGISTRY = path.join(TASK_DIR, 'task-registry.json');
const TASK_HISTORY = path.join(TASK_DIR, 'task-history.md');

// ============================================================================
// 工具函数
// ============================================================================

const readFile = (filePath) => {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch (e) {
    return null;
  }
};

const writeFile = (filePath, content) => {
  fs.writeFileSync(filePath, content, 'utf8');
};

const readJSON = (filePath) => {
  const content = readFile(filePath);
  return content ? JSON.parse(content) : null;
};

const writeJSON = (filePath, data) => {
  writeFile(filePath, JSON.stringify(data, null, 2));
};

const execAsync = (command) => {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) {
        reject({ error, stdout, stderr });
      } else {
        resolve({ stdout, stderr });
      }
    });
  });
};

// ============================================================================
// OpenClaw 工具集成（通过 HTTP API）
// ============================================================================

const GATEWAY_URL = 'http://127.0.0.1:18789';
const GATEWAY_TOKEN = '6026dcc4ffe9663a47656f60f08c0f77561b31a5ca0133a9';

/**
 * 通过 HTTP API 创建 subagent
 */
async function spawnSubagent(agentId, task, label) {
  try {
    const url = `${GATEWAY_URL}/v1/agents/${agentId}/wake`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GATEWAY_TOKEN}`,
      },
      body: JSON.stringify({
        message: task,
        metadata: {
          label,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // 返回 session 信息
    return {
      sessionId: data.sessionId || data.id || generateSessionId(),
      label,
    };
  } catch (error) {
    console.error(`❌ 创建 subagent 失败: ${error.message}`);
    throw error;
  }
}

/**
 * 通过 HTTP API 查询 sessions
 */
async function listSessions(kind = 'subagent', activeMinutes = 30) {
  try {
    const url = `${GATEWAY_URL}/v1/sessions`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${GATEWAY_TOKEN}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.sessions || [];
  } catch (error) {
    console.error(`❌ 查询 sessions 失败: ${error.message}`);
    return [];
  }
}

/**
 * 通过 HTTP API 查询 session 历史
 */
async function getSessionHistory(sessionId) {
  try {
    const url = `${GATEWAY_URL}/v1/sessions/${sessionId}/history`;
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${GATEWAY_TOKEN}`,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.history || [];
  } catch (error) {
    console.error(`❌ 查询 session 历史失败: ${error.message}`);
    return [];
  }
}

/**
 * 生成临时 session ID（如果 API 未返回）
 */
function generateSessionId() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// ============================================================================
// Subagent 等待机制（轮询）
// ============================================================================

/**
 * 等待 subagent 完成
 */
async function waitForSubagent(sessionId, timeout = 3600000, pollInterval = 5000) {
  const startTime = Date.now();
  let attempts = 0;

  console.log(`  ⏳ 等待 subagent 完成: ${sessionId} (超时: ${timeout/1000}s)`);

  while (Date.now() - startTime < timeout) {
    attempts++;

    try {
      // 查询 subagent 历史
      const history = await getSessionHistory(sessionId);

      if (history.length === 0) {
        console.log(`  ⏳ 轮询 #${attempts}: 无历史记录，等待中...`);
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        continue;
      }

      // 检查最后一条消息
      const lastMessage = history[history.length - 1];
      if (lastMessage && lastMessage.message) {
        const content = lastMessage.message.message?.content || lastMessage.message.content;

        // 检查完成标记
        if (content.includes('completed') ||
            content.includes('finished') ||
            content.includes('done') ||
            content.includes('✅') ||
            content.includes('完成')) {
          console.log(`  ✅ Subagent 完成: ${sessionId} (${attempts} 次轮询)`);
          return { success: true, output: content, attempts };
        }

        // 检查失败标记
        if (content.includes('failed') ||
            content.includes('error') ||
            content.includes('❌') ||
            content.includes('失败') ||
            content.includes('错误')) {
          console.log(`  ❌ Subagent 失败: ${sessionId}`);
          return { success: false, output: content, attempts };
        }
      }

      console.log(`  ⏳ 轮询 #${attempts}: 未完成，等待中...`);
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    } catch (error) {
      console.log(`  ⚠️ 轮询 #${attempts}: 查询失败 (${error.message})，重试...`);
      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }
  }

  // 超时
  console.log(`  ⏱️ Subagent 超时: ${sessionId} (${attempts} 次轮询)`);
  return { success: false, output: 'Timeout', attempts };
}

// ============================================================================
// 冲突检测
// ============================================================================

/**
 * 检测冲突（基于规则）
 */
function detectConflicts(task, existingTasks, mainGoal) {
  const conflicts = [];

  // 1. 检查任务标题是否重复
  const duplicateTitle = existingTasks.find(t =>
    t.title === task.title && t.status !== 'completed'
  );
  if (duplicateTitle) {
    conflicts.push({
      type: 'duplicate-title',
      taskId: duplicateTitle.taskId,
      severity: 'medium',
      suggestion: '任务标题重复，建议合并或修改',
    });
  }

  // 2. 检查是否有运行中的相同 Agent 任务
  const runningSameAgent = existingTasks.filter(t =>
    t.agentId === task.agentId && t.status === 'running'
  );
  if (runningSameAgent.length > 0) {
    conflicts.push({
      type: 'multiple-running',
      agentId: task.agentId,
      count: runningSameAgent.length,
      severity: 'low',
      suggestion: '同一 Agent 有多个运行中的任务，建议顺序执行',
      tasks: runningSameAgent.map(t => t.taskId),
    });
  }

  // 3. 检查与主线任务是否冲突
  if (task.context && task.context.mainGoal) {
    // 假设任务标题与主线任务不同，则不冲突
    // 实际应用中可以添加更复杂的冲突检测逻辑
  }

  return conflicts;
}

/**
 * 解决冲突
 */
function resolveConflicts(task, conflicts) {
  if (conflicts.length === 0) {
    return { action: 'proceed', reason: '无冲突' };
  }

  const highSeverityConflicts = conflicts.filter(c => c.severity === 'high');
  if (highSeverityConflicts.length > 0) {
    return {
      action: 'reject',
      reason: `存在高严重度冲突: ${highSeverityConflicts.map(c => c.type).join(', ')}`,
      conflicts,
    };
  }

  const mediumSeverityConflicts = conflicts.filter(c => c.severity === 'medium');
  if (mediumSeverityConflicts.length > 0) {
    return {
      action: 'pause-others',
      reason: `存在中严重度冲突，暂停其他任务: ${mediumSeverityConflicts.map(c => c.type).join(', ')}`,
      conflicts,
    };
  }

  return {
    action: 'proceed',
    reason: '冲突不严重，继续执行',
    conflicts,
  };
}

// ============================================================================
// 任务管理
// ============================================================================

/**
 * 生成任务 ID
 */
function generateTaskId() {
  const date = new Date();
  const timestamp = date.toISOString().replace(/[-:.]/g, '').slice(0, 14);
  const random = Math.random().toString(36).substring(2, 5);
  return `task-${timestamp}-${random}`;
}

/**
 * 初始化任务目录
 */
function initTaskDir() {
  const dirs = [
    TASK_DIR,
    path.join(TASK_DIR, 'active'),
    path.join(TASK_DIR, 'completed'),
    path.join(TASK_DIR, 'failed'),
    path.join(TASK_DIR, 'archived'),
    path.join(TASK_DIR, 'paused'),
  ];

  for (const dir of dirs) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  // 初始化任务注册表
  if (!fs.existsSync(TASK_REGISTRY)) {
    const registry = {
      version: 2,
      totalTasks: 0,
      activeTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
      pausedTasks: 0,
      cancelledTasks: 0,
      tasks: {},
      byAgent: {},
      lastUpdated: new Date().toISOString(),
    };
    writeJSON(TASK_REGISTRY, registry);
  }

  // 初始化任务历史
  if (!fs.existsSync(TASK_HISTORY)) {
    writeFile(TASK_HISTORY, '# 任务历史\n\n');
  }

  console.log('✅ 任务目录初始化完成');
}

/**
 * 解析步骤
 */
function parseSteps(stepsConfig) {
  return stepsConfig.map((step, index) => ({
    stepId: String(index + 1).padStart(3, '0'),
    title: step.title,
    description: step.description,
    command: step.command || null,
    status: 'pending',
    startedAt: null,
    completedAt: null,
    subagent: null,
    continueOnError: step.continueOnError || false,
  }));
}

/**
 * 创建任务
 */
async function createTask(taskConfig) {
  console.log('\n📝 创建任务...');

  // 1. 生成任务 ID
  const taskId = generateTaskId();

  // 2. 解析步骤
  const steps = parseSteps(taskConfig.steps || []);

  // 3. 构建任务对象
  const task = {
    taskId,
    title: taskConfig.title,
    description: taskConfig.description,
    agentId: taskConfig.agentId,
    priority: taskConfig.priority || 'medium',
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    conflictResolution: taskConfig.conflictResolution || 'pause-others',
    steps,
    context: {
      mainGoal: taskConfig.mainGoal || '未指定',
      currentMainStatus: taskConfig.currentMainStatus || '未知',
    },
    result: null,
    summary: null,
  };

  // 4. 冲突检测
  const existingTasks = getTasksByAgent(task.agentId, ['running', 'pending']);
  const conflicts = detectConflicts(task, existingTasks, task.context.mainGoal);

  if (conflicts.length > 0) {
    console.log('⚠️  检测到冲突:');
    for (const conflict of conflicts) {
      console.log(`  - [${conflict.severity}] ${conflict.type}: ${conflict.suggestion}`);
    }

    const resolution = resolveConflicts(task, conflicts);
    if (resolution.action === 'reject') {
      console.log(`❌ 任务被拒绝: ${resolution.reason}`);
      throw new Error(`任务被拒绝: ${resolution.reason}`);
    }

    console.log(`✅ 冲突处理: ${resolution.action} - ${resolution.reason}`);
  }

  // 5. 保存任务文件
  const taskFilePath = path.join(TASK_DIR, 'active', `${taskId}.json`);
  writeJSON(taskFilePath, task);

  // 6. 更新任务注册表
  updateTaskRegistry(task, 'created');

  // 7. 记录到历史
  logToHistory('created', task);

  console.log(`✅ 任务已创建: ${taskId}`);
  console.log(`  标题: ${task.title}`);
  console.log(`  Agent: ${task.agentId}`);
  console.log(`  状态: ${task.status}`);

  return task;
}

/**
 * 执行任务
 */
async function executeTask(taskId) {
  console.log('\n🚀 执行任务...');

  try {
    // 1. 加载任务
    const task = loadTask(taskId);

    // 2. 更新状态为运行中
    task.status = 'running';
    updateTask(task);

    console.log(`✅ 任务开始执行: ${task.taskId}`);
    console.log(`  标题: ${task.title}`);

    // 3. 执行步骤
    for (let i = 0; i < task.steps.length; i++) {
      const step = task.steps[i];

      if (step.status === 'completed') {
        console.log(`\n⏭️  步骤已完成，跳过: [${step.stepId}] ${step.title}`);
        continue;
      }

      console.log(`\n📌 执行步骤 ${i + 1}/${task.steps.length}: [${step.stepId}] ${step.title}`);

      // 执行步骤
      const stepResult = await executeStep(task, step);

      // 更新步骤状态
      updateStepResult(task, step, stepResult);

      // 保存任务
      updateTask(task);

      // 如果步骤失败且不继续执行，则任务失败
      if (!stepResult.success && !step.continueOnError) {
        task.status = 'failed';
        task.result = `步骤失败: ${step.title}`;
        updateTask(task);
        logToHistory('failed', task);
        throw new Error(`步骤失败: ${step.title}`);
      }
    }

    // 4. 所有步骤完成
    task.status = 'completed';
    task.completedAt = new Date().toISOString();
    task.result = summarizeTaskResult(task);
    updateTask(task);

    // 5. 归档任务
    archiveTask(taskId);

    // 6. 记录到历史
    logToHistory('completed', task);

    console.log(`\n✅ 任务已完成: ${task.taskId}`);
    console.log(`  结果: ${task.result}`);

    return task;
  } catch (error) {
    console.error(`\n❌ 任务执行失败: ${error.message}`);
    throw error;
  }
}

/**
 * 执行步骤
 */
async function executeStep(task, step) {
  // 1. 更新步骤状态
  step.status = 'running';
  step.startedAt = new Date().toISOString();

  // 2. 生成 subagent 任务描述
  const subagentTask = `
任务上下文：
- 任务 ID: ${task.taskId}
- 任务标题: ${task.title}
- 任务描述: ${task.description}

当前步骤：
- 步骤 ID: ${step.stepId}
- 步骤标题: ${step.title}
- 步骤描述: ${step.description}

请执行此步骤，并在完成后报告结果。
重要：使用以下标记表示状态：
- ✅ completed / 完成：步骤成功完成
- ❌ failed / 失败：步骤执行失败
  `.trim();

  // 3. 生成 subagent label
  const label = `task:${task.taskId}:step:${step.stepId}:${step.title.toLowerCase().replace(/ /g, '-')}`;

  console.log(`  📤 创建 subagent: ${label}`);

  try {
    // 4. 创建 subagent
    const subagent = await spawnSubagent(task.agentId, subagentTask, label);

    // 5. 记录 subagent 信息
    step.subagent = {
      sessionId: subagent.sessionId,
      label: subagent.label,
      createdAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
      status: 'running',
    };

    // 6. 等待 subagent 完成
    const result = await waitForSubagent(
      subagent.sessionId,
      getTaskTimeout(task.priority),
      5000
    );

    // 7. 记录结果
    step.subagent.completedAt = new Date().toISOString();
    step.subagent.status = result.success ? 'completed' : 'failed';
    step.subagent.result = result.output;
    step.subagent.duration = Math.floor((new Date(step.subagent.completedAt) - new Date(step.subagent.startedAt)) / 1000);
    step.subagent.attempts = result.attempts;

    console.log(`  📊 Subagent 结果: ${result.success ? '成功' : '失败'}`);
    console.log(`     时长: ${step.subagent.duration}s`);
    console.log(`     轮询次数: ${result.attempts}`);

    return result;
  } catch (error) {
    console.error(`  ❌ 步骤执行失败: ${error.message}`);
    return { success: false, output: error.message };
  }
}

/**
 * 更新步骤结果
 */
function updateStepResult(task, step, stepResult) {
  step.status = stepResult.success ? 'completed' : 'failed';
  step.completedAt = new Date().toISOString();
}

/**
 * 获取任务超时时间
 */
function getTaskTimeout(priority) {
  const timeouts = {
    high: 7200000,    // 2 小时
    medium: 3600000, // 1 小时
    low: 1800000,    // 30 分钟
  };
  return timeouts[priority] || timeouts.medium;
}

/**
 * 汇总任务结果
 */
function summarizeTaskResult(task) {
  const totalSteps = task.steps.length;
  const completedSteps = task.steps.filter(s => s.status === 'completed').length;
  const failedSteps = task.steps.filter(s => s.status === 'failed').length;

  return `任务完成: ${completedSteps}/${totalSteps} 步骤成功，${failedSteps} 步骤失败`;
}

/**
 * 加载任务
 */
function loadTask(taskId) {
  // 在 active 目录中查找
  let taskFilePath = path.join(TASK_DIR, 'active', `${taskId}.json`);
  if (fs.existsSync(taskFilePath)) {
    return readJSON(taskFilePath);
  }

  // 在 paused 目录中查找
  taskFilePath = path.join(TASK_DIR, 'paused', `${taskId}.json`);
  if (fs.existsSync(taskFilePath)) {
    return readJSON(taskFilePath);
  }

  // 在 completed 目录中查找
  taskFilePath = path.join(TASK_DIR, 'completed', `${taskId}.json`);
  if (fs.existsSync(taskFilePath)) {
    return readJSON(taskFilePath);
  }

  // 在 failed 目录中查找
  taskFilePath = path.join(TASK_DIR, 'failed', `${taskId}.json`);
  if (fs.existsSync(taskFilePath)) {
    return readJSON(taskFilePath);
  }

  throw new Error(`任务不存在: ${taskId}`);
}

/**
 * 查询 Agent 的所有任务
 */
function getTasksByAgent(agentId, statusFilter = null) {
  const registry = readJSON(TASK_REGISTRY);
  const taskIds = Object.keys(registry.tasks)
    .filter((id) => registry.tasks[id].agentId === agentId)
    .filter((id) => !statusFilter || registry.tasks[id].status === statusFilter);

  const tasks = [];
  for (const taskId of taskIds) {
    try {
      const task = loadTask(taskId);
      tasks.push(task);
    } catch (e) {
      // 忽略加载失败的任务
    }
  }

  return tasks;
}

/**
 * 更新任务
 */
function updateTask(task) {
  task.updatedAt = new Date().toISOString();

  // 根据状态选择目录
  let taskDir;
  if (task.status === 'completed') {
    taskDir = 'completed';
  } else if (task.status === 'failed') {
    taskDir = 'failed';
  } else if (task.status === 'paused') {
    taskDir = 'paused';
  } else {
    taskDir = 'active';
  }

  // 保存任务文件
  const taskFilePath = path.join(TASK_DIR, taskDir, `${task.taskId}.json`);
  writeJSON(taskFilePath, task);

  // 更新任务注册表
  const registry = readJSON(TASK_REGISTRY);
  registry.tasks[task.taskId] = {
    taskId: task.taskId,
    title: task.title,
    agentId: task.agentId,
    status: task.status,
    createdAt: task.createdAt,
    updatedAt: task.updatedAt,
    priority: task.priority,
  };
  registry.lastUpdated = new Date().toISOString();
  writeJSON(TASK_REGISTRY, registry);
}

/**
 * 更新任务注册表
 */
function updateTaskRegistry(task, action) {
  const registry = readJSON(TASK_REGISTRY);

  if (action === 'created') {
    // 创建任务
    registry.tasks[task.taskId] = {
      taskId: task.taskId,
      title: task.title,
      agentId: task.agentId,
      status: task.status,
      createdAt: task.createdAt,
      updatedAt: task.updatedAt,
      priority: task.priority,
    };

    registry.totalTasks++;
    registry.activeTasks++;

    // 更新 Agent 统计
    if (!registry.byAgent[task.agentId]) {
      registry.byAgent[task.agentId] = {
        total: 0,
        active: 0,
        completed: 0,
        failed: 0,
        paused: 0,
      };
    }
    registry.byAgent[task.agentId].total++;
    registry.byAgent[task.agentId].active++;
  } else if (action === 'completed') {
    // 任务完成
    registry.activeTasks--;
    registry.completedTasks++;

    if (registry.byAgent[task.agentId]) {
      registry.byAgent[task.agentId].active--;
      registry.byAgent[task.agentId].completed++;
    }
  } else if (action === 'failed') {
    // 任务失败
    registry.activeTasks--;
    registry.failedTasks++;

    if (registry.byAgent[task.agentId]) {
      registry.byAgent[task.agentId].active--;
      registry.byAgent[task.agentId].failed++;
    }
  } else if (action === 'paused') {
    // 任务暂停
    registry.activeTasks--;
    registry.pausedTasks++;

    if (registry.byAgent[task.agentId]) {
      registry.byAgent[task.agentId].active--;
      registry.byAgent[task.agentId].paused++;
    }
  } else if (action === 'cancelled') {
    // 任务取消
    registry.activeTasks--;
    registry.cancelledTasks++;

    if (registry.byAgent[task.agentId]) {
      registry.byAgent[task.agentId].active--;
    }
  }

  registry.lastUpdated = new Date().toISOString();
  writeJSON(TASK_REGISTRY, registry);
}

/**
 * 归档任务
 */
function archiveTask(taskId) {
  console.log(`\n📦 归档任务: ${taskId}`);

  // 加载任务
  const task = loadTask(taskId);

  // 如果任务已完成超过 30 天，则归档
  const completedAt = new Date(task.completedAt || task.updatedAt);
  const daysSinceCompletion = (Date.now() - completedAt) / (1000 * 60 * 60 * 24);

  if (daysSinceCompletion >= 30) {
    // 从当前目录移动到 archived 目录
    let sourceDir;
    if (task.status === 'completed') {
      sourceDir = 'completed';
    } else if (task.status === 'failed') {
      sourceDir = 'failed';
    } else {
      return;
    }

    const sourcePath = path.join(TASK_DIR, sourceDir, `${taskId}.json`);
    const destPath = path.join(TASK_DIR, 'archived', `${taskId}.json`);

    if (fs.existsSync(sourcePath)) {
      fs.copyFileSync(sourcePath, destPath);
      fs.unlinkSync(sourcePath);

      console.log(`  ✅ 任务已归档到 archived 目录`);
    }
  }
}

/**
 * 暂停任务
 */
function pauseTask(taskId) {
  console.log(`\n⏸️  暂停任务: ${taskId}`);

  const task = loadTask(taskId);

  if (task.status !== 'running') {
    throw new Error(`只能暂停运行中的任务，当前状态: ${task.status}`);
  }

  task.status = 'paused';
  task.pausedAt = new Date().toISOString();
  updateTask(task);
  updateTaskRegistry(task, 'paused');

  logToHistory('paused', task);

  console.log(`✅ 任务已暂停: ${task.taskId}`);
}

/**
 * 恢复任务
 */
function resumeTask(taskId) {
  console.log(`\n▶️  恢复任务: ${taskId}`);

  const task = loadTask(taskId);

  if (task.status !== 'paused') {
    throw new Error(`只能恢复已暂停的任务，当前状态: ${task.status}`);
  }

  task.status = 'pending';
  task.resumedAt = new Date().toISOString();

  // 从 paused 目录移动到 active 目录
  const sourcePath = path.join(TASK_DIR, 'paused', `${taskId}.json`);
  const destPath = path.join(TASK_DIR, 'active', `${taskId}.json`);

  if (fs.existsSync(sourcePath)) {
    fs.copyFileSync(sourcePath, destPath);
    fs.unlinkSync(sourcePath);
  }

  updateTask(task);
  updateTaskRegistry(task, 'resumed');

  logToHistory('resumed', task);

  console.log(`✅ 任务已恢复: ${task.taskId}`);
}

/**
 * 取消任务
 */
function cancelTask(taskId) {
  console.log(`\n⏭️  取消任务: ${taskId}`);

  const task = loadTask(taskId);

  task.status = 'cancelled';
  task.cancelledAt = new Date().toISOString();
  task.result = '任务被用户取消';

  // 从当前目录移动到 failed 目录
  let sourceDir;
  if (task.status === 'pending' || task.status === 'running') {
    sourceDir = 'active';
  } else if (task.status === 'paused') {
    sourceDir = 'paused';
  } else {
    throw new Error(`无法取消状态为 ${task.status} 的任务`);
  }

  const sourcePath = path.join(TASK_DIR, sourceDir, `${taskId}.json`);
  const destPath = path.join(TASK_DIR, 'failed', `${taskId}.json`);

  if (fs.existsSync(sourcePath)) {
    fs.copyFileSync(sourcePath, destPath);
    fs.unlinkSync(sourcePath);
  }

  updateTaskRegistry(task, 'cancelled');

  logToHistory('cancelled', task);

  console.log(`✅ 任务已取消: ${task.taskId}`);
}

/**
 * 查询任务历史
 */
function getTaskHistory(taskId) {
  const history = readFile(TASK_HISTORY);
  const lines = history.split('\n');

  const entries = [];
  for (const line of lines) {
    if (line.includes(taskId)) {
      entries.push(line);
    }
  }

  return entries;
}

/**
 * 记录到历史
 */
function logToHistory(action, task) {
  const timestamp = new Date().toISOString();
  const entry = `## [${timestamp}] ${action}: ${task.taskId}

- 标题: ${task.title}
- Agent: ${task.agentId}
- 状态: ${task.status}

`;

  const history = readFile(TASK_HISTORY);
  writeFile(TASK_HISTORY, entry + '\n' + history);
}

/**
 * 显示任务列表
 */
function showTasks(agentId = null, statusFilter = null) {
  console.log('\n📋 任务列表\n');

  const registry = readJSON(TASK_REGISTRY);
  const taskIds = Object.keys(registry.tasks)
    .filter((id) => !agentId || registry.tasks[id].agentId === agentId)
    .filter((id) => !statusFilter || registry.tasks[id].status === statusFilter);

  if (taskIds.length === 0) {
    console.log('没有找到任务');
    return;
  }

  console.log(`| 任务 ID | 标题 | Agent | 状态 | 创建时间 |`);
  console.log('|---------|------|-------|------|---------|');

  for (const taskId of taskIds) {
    const taskInfo = registry.tasks[taskId];
    const statusEmoji = getStatusEmoji(taskInfo.status);
    console.log(`| ${taskId} | ${taskInfo.title} | ${taskInfo.agentId} | ${statusEmoji} ${taskInfo.status} | ${taskInfo.createdAt.slice(0, 19)} |`);
  }

  console.log(`\n总计: ${taskIds.length} 个任务`);
}

/**
 * 显示任务详情
 */
function showTask(taskId) {
  console.log('\n📄 任务详情\n');

  try {
    const task = loadTask(taskId);

    console.log(`任务 ID: ${task.taskId}`);
    console.log(`标题: ${task.title}`);
    console.log(`描述: ${task.description}`);
    console.log(`Agent: ${task.agentId}`);
    console.log(`优先级: ${task.priority}`);
    console.log(`状态: ${getStatusEmoji(task.status)} ${task.status}`);
    console.log(`创建时间: ${task.createdAt.slice(0, 19)}`);
    console.log(`更新时间: ${task.updatedAt.slice(0, 19)}`);

    if (task.completedAt) {
      console.log(`完成时间: ${task.completedAt.slice(0, 19)}`);
    }

    if (task.result) {
      console.log(`结果: ${task.result}`);
    }

    console.log(`\n步骤:`);
    for (const step of task.steps) {
      const stepEmoji = getStepEmoji(step.status);
      console.log(`  ${stepEmoji} [${step.stepId}] ${step.title}`);
      console.log(`      描述: ${step.description}`);

      if (step.startedAt) {
        console.log(`      开始时间: ${step.startedAt.slice(0, 19)}`);
      }
      if (step.completedAt) {
        console.log(`      完成时间: ${step.completedAt.slice(0, 19)}`);
      }
      if (step.subagent) {
        console.log(`      Subagent ID: ${step.subagent.sessionId}`);
        console.log(`      Subagent Label: ${step.subagent.label}`);
        if (step.subagent.duration) {
          console.log(`      执行时长: ${step.subagent.duration}s`);
        }
        if (step.subagent.attempts) {
          console.log(`      轮询次数: ${step.subagent.attempts}`);
        }
      }
    }
  } catch (e) {
    console.error(`❌ ${e.message}`);
  }
}

/**
 * 获取状态 emoji
 */
function getStatusEmoji(status) {
  const emojis = {
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌',
    blocked: '🚫',
    paused: '⏸️',
    cancelled: '⏭️',
  };
  return emojis[status] || '⚪';
}

/**
 * 获取步骤 emoji
 */
function getStepEmoji(status) {
  const emojis = {
    pending: '⏳',
    running: '🔄',
    completed: '✅',
    failed: '❌',
    skipped: '⏭️',
  };
  return emojis[status] || '⚪';
}

/**
 * 显示统计信息
 */
function showStats() {
  console.log('\n📊 任务统计\n');

  const registry = readJSON(TASK_REGISTRY);

  console.log(`总任务数: ${registry.totalTasks}`);
  console.log(`活跃任务: ${registry.activeTasks}`);
  console.log(`已完成: ${registry.completedTasks}`);
  console.log(`已失败: ${registry.failedTasks}`);
  console.log(`已暂停: ${registry.pausedTasks}`);
  console.log(`已取消: ${registry.cancelledTasks}`);

  console.log('\n按 Agent 统计:');
  for (const [agentId, stats] of Object.entries(registry.byAgent)) {
    console.log(`  ${agentId}:`);
    console.log(`    总计: ${stats.total}`);
    console.log(`    活跃: ${stats.active}`);
    console.log(`    已完成: ${stats.completed}`);
    console.log(`    已失败: ${stats.failed}`);
    console.log(`    已暂停: ${stats.paused}`);
  }
}

/**
 * 监控任务
 */
async function monitorTasks(agentId = null) {
  console.log('\n🔍 监控任务...\n');

  const registry = readJSON(TASK_REGISTRY);
  const taskIds = Object.keys(registry.tasks)
    .filter((id) => !agentId || registry.tasks[id].agentId === agentId)
    .filter((id) => ['running', 'pending'].includes(registry.tasks[id].status));

  if (taskIds.length === 0) {
    console.log('没有需要监控的任务');
    return;
  }

  for (const taskId of taskIds) {
    try {
      const task = loadTask(taskId);

      console.log(`\n任务: ${task.taskId}`);
      console.log(`标题: ${task.title}`);
      console.log(`状态: ${getStatusEmoji(task.status)} ${task.status}`);

      // 检查超时
      if (task.status === 'running') {
        const currentStep = task.steps.find(s => s.status === 'running');
        if (currentStep && currentStep.startedAt) {
          const elapsed = Date.now() - new Date(currentStep.startedAt);
          const timeout = getTaskTimeout(task.priority);

          if (elapsed > timeout) {
            console.log(`⚠️  任务超时: ${elapsed/1000}s (超时: ${timeout/1000}s)`);

            // 处理超时任务
            task.status = 'failed';
            task.result = '任务超时';
            updateTask(task);
            updateTaskRegistry(task, 'failed');
            logToHistory('failed', task);
          } else {
            console.log(`⏱️  运行中: ${Math.floor(elapsed/1000)}s / ${timeout/1000}s`);
          }
        }
      }

      // 显示步骤状态
      console.log(`步骤进度: ${task.steps.filter(s => s.status === 'completed').length}/${task.steps.length}`);

    } catch (e) {
      console.error(`❌ 监控任务失败: ${e.message}`);
    }
  }

  console.log('\n✅ 监控完成');
}

/**
 * 归档旧任务
 */
function archiveOldTasks() {
  console.log('\n📦 归档旧任务...\n');

  const registry = readJSON(TASK_REGISTRY);
  const taskIds = Object.keys(registry.tasks)
    .filter((id) => ['completed', 'failed'].includes(registry.tasks[id].status));

  let archivedCount = 0;

  for (const taskId of taskIds) {
    try {
      archiveTask(taskId);
      archivedCount++;
    } catch (e) {
      // 忽略归档失败的任务
    }
  }

  console.log(`✅ 归档完成: ${archivedCount} 个任务`);
}

// ============================================================================
// 主函数
// ============================================================================

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  // 初始化任务目录
  initTaskDir();

  switch (command) {
    case 'create': {
      // 示例: node task-manager.js create "诊断 RTSP 连接问题" ffmedia
      const title = args[1];
      const agentId = args[2];
      const priority = args[3] || 'medium';

      if (!title || !agentId) {
        console.error('用法: node task-manager.js create <title> <agentId> [priority]');
        process.exit(1);
      }

      await createTask({
        title,
        description: title,
        agentId,
        priority,
        steps: [
          {
            title: '步骤 1',
            description: '第一步',
          },
          {
            title: '步骤 2',
            description: '第二步',
          },
        ],
      });

      break;
    }

    case 'execute': {
      // 示例: node task-manager.js execute task-xxx
      const taskId = args[1];

      if (!taskId) {
        console.error('用法: node task-manager.js execute <taskId>');
        process.exit(1);
      }

      await executeTask(taskId);

      break;
    }

    case 'list': {
      // 示例: node task-manager.js list ffmedia running
      const agentId = args[1] || null;
      const statusFilter = args[2] || null;

      showTasks(agentId, statusFilter);
      break;
    }

    case 'show': {
      // 示例: node task-manager.js show task-xxx
      const taskId = args[1];

      if (!taskId) {
        console.error('用法: node task-manager.js show <taskId>');
        process.exit(1);
      }

      showTask(taskId);
      break;
    }

    case 'pause': {
      // 示例: node task-manager.js pause task-xxx
      const taskId = args[1];

      if (!taskId) {
        console.error('用法: node task-manager.js pause <taskId>');
        process.exit(1);
      }

      pauseTask(taskId);
      break;
    }

    case 'resume': {
      // 示例: node task-manager.js resume task-xxx
      const taskId = args[1];

      if (!taskId) {
        console.error('用法: node task-manager.js resume <taskId>');
        process.exit(1);
      }

      resumeTask(taskId);
      break;
    }

    case 'cancel': {
      // 示例: node task-manager.js cancel task-xxx
      const taskId = args[1];

      if (!taskId) {
        console.error('用法: node task-manager.js cancel <taskId>');
        process.exit(1);
      }

      cancelTask(taskId);
      break;
    }

    case 'stats': {
      showStats();
      break;
    }

    case 'monitor': {
      // 示例: node task-manager.js monitor ffmedia
      const agentId = args[1] || null;

      await monitorTasks(agentId);
      break;
    }

    case 'archive': {
      archiveOldTasks();
      break;
    }

    case 'init': {
      // 已在主函数开始时初始化
      console.log('✅ 任务目录已初始化');
      break;
    }

    default: {
      console.log(`
Stone 任务管理器 v2.0

用法:
  node task-manager.js init                          # 初始化任务目录
  node task-manager.js create <title> <agentId> [priority]  # 创建任务
  node task-manager.js execute <taskId>              # 执行任务
  node task-manager.js list [agentId] [status]        # 列出任务
  node task-manager.js show <taskId>                 # 显示任务详情
  node task-manager.js pause <taskId>                # 暂停任务
  node task-manager.js resume <taskId>               # 恢复任务
  node task-manager.js cancel <taskId>               # 取消任务
  node task-manager.js stats                         # 显示统计信息
  node task-manager.js monitor [agentId]              # 监控任务
  node task-manager.js archive                       # 归档旧任务

示例:
  node task-manager.js create "诊断 RTSP 连接问题" ffmedia high
  node task-manager.js execute task-20260303-1056-ab1
  node task-manager.js list ffmedia running
  node task-manager.js show task-20260303-1056-ab1
  node task-manager.js pause task-20260303-1056-ab1
  node task-manager.js resume task-20260303-1056-ab1
  node task-manager.js cancel task-20260303-1056-ab1
  node task-manager.js stats
  node task-manager.js monitor ffmedia
  node task-manager.js archive
      `);
    }
  }
}

// 运行主函数
main().catch(console.error);
