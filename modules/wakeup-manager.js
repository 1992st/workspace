/**
 * Stone - 唤醒管理器
 *
 * 负责唤醒 agent、等待完成、处理结果
 */

import { sessions_spawn, sessions_history } from 'sessions';
import { formatDate, extractAgentId, extractRunId, delay } from '../core/utils.js';
import ContextBuilder from './context-builder.js';

/**
 * 唤醒管理器
 */
export class WakeupManager {
  constructor(stone) {
    this.stone = stone;
    this.config = stone.getConfig();
    this.running = false;
    this.activeRuns = new Map();
    this.retryCount = new Map();
    this.contextBuilder = new ContextBuilder();
  }

  /**
   * 启动唤醒管理器
   */
  async start() {
    console.log('\n🔄 启动唤醒管理器...');

    this.running = true;

    // 注册事件监听器
    this.stone.eventListener.onSubagentAbort(async (data) => {
      await this.handleSubagentAbort(data);
    });

    console.log('✅ 唤醒管理器已启动');
  }

  /**
   * 停止唤醒管理器
   */
  async stop() {
    console.log('\n🔄 停止唤醒管理器...');

    this.running = false;

    // 等待所有活跃运行完成
    const runIds = Array.from(this.activeRuns.keys());
    console.log(`  等待 ${runIds.length} 个活跃运行完成...`);

    // TODO: 可以在这里实现优雅关闭

    console.log('✅ 唤醒管理器已停止');
  }

  /**
   * 唤醒 agent 并监控
   */
  async wakeupAndMonitor(agentId, task) {
    console.log(`\n🔄 唤醒 ${agentId}...`);
    console.log(`  任务: ${task.substring(0, 100)}...`);

    // 1. 唤醒 subagent
    const spawnResult = await this.spawnAgent(agentId, task);
    if (!spawnResult.success) {
      console.error(`❌ 唤醒失败: ${spawnResult.error}`);
      return { success: false, error: spawnResult.error };
    }

    const runId = spawnResult.runId;
    console.log(`✅ Subagent 已唤醒: runId=${runId}`);

    // 2. 注册运行
    this.stone.registerSubagentRun(agentId, runId);
    this.activeRuns.set(runId, {
      agentId,
      runId,
      task,
      startTime: Date.now(),
      status: 'waiting',
    });

    // 3. 等待完成（使用 sessions_history 轮询，替代 agent.wait）
    const waitResult = await this.waitForCompletion(runId);

    // 4. 处理结果
    const result = await this.processResult(runId, agentId, waitResult);

    // 5. 取消注册
    this.stone.unregisterSubagentRun(agentId, runId);
    this.activeRuns.delete(runId);

    return result;
  }

  /**
   * 唤醒 subagent
   */
  async spawnAgent(agentId, task) {
    try {
      // 🔧 使用 ContextBuilder 构建增强的任务 prompt
      const enhancedTask = await this.contextBuilder.buildTaskPrompt(agentId, task);

      console.log(`\n📝 构建增强的任务 prompt (包含历史上下文)...`);
      console.log(`  原始任务: ${task.substring(0, 100)}...`);
      console.log(`  增强后长度: ${enhancedTask.length} 字符`);

      const result = await sessions_spawn({
        agentId: agentId,
        task: enhancedTask,  // ✅ 使用增强的任务
        mode: 'session',  // ✅ 持久化 session 模式
        thread: true,     // ✅ 绑定到当前 thread
        label: `stone-wakeup-${agentId}`,  // 固定 label，便于后续查找
        runTimeoutSeconds: this.config.subagents.waitTimeoutSeconds,
      });

      return {
        success: true,
        runId: result.childSessionKey,
        sessionKey: result.childSessionKey,
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
      };
    }
  }

  /**
   * 等待 subagent 完成
   */
  async waitForCompletion(runId) {
    const timeout = this.config.subagents.waitTimeoutSeconds * 1000;
    const startTime = Date.now();
    const pollInterval = 10000; // 10 秒轮询一次

    console.log(`👀 等待 subagent 完成 (超时: ${timeout / 1000}秒)...`);

    while (Date.now() - startTime < timeout) {
      try {
        // 使用 sessions_history 查询最后一条消息
        const history = await sessions_history({
          sessionKey: runId,
          limit: 5,
        });

        if (!history || !history.messages || history.messages.length === 0) {
          await delay(pollInterval);
          continue;
        }

        const lastMessage = history.messages[history.messages.length - 1];

        // 检查是否完成
        const isCompleted = this.isSubagentCompleted(lastMessage);

        if (isCompleted) {
          const duration = Date.now() - startTime;
          console.log(`✅ Subagent 完成 (耗时: ${duration / 1000}秒)`);
          return { success: true, status: 'ok', lastMessage };
        }

        // 检查是否出错
        if (lastMessage.error) {
          console.log(`❌ Subagent 出错: ${lastMessage.error}`);
          return { success: false, status: 'error', error: lastMessage.error };
        }

        // 继续等待
        await delay(pollInterval);

      } catch (error) {
        console.warn('查询 subagent 状态失败:', error);
        await delay(pollInterval);
      }
    }

    // 超时
    console.log(`⏱️ Subagent 超时`);
    return { success: false, status: 'timeout' };
  }

  /**
   * 判断 subagent 是否完成
   */
  isSubagentCompleted(message) {
    if (!message) return false;

    const content = message.message || '';

    // 检查完成关键字
    const completeKeywords = ['完成', 'finished', 'done', '✅', '完成情况', '报告'];
    return completeKeywords.some(keyword => content.includes(keyword));
  }

  /**
   * 处理结果
   */
  async processResult(runId, agentId, waitResult) {
    console.log(`\n📊 处理结果: ${agentId} (${runId})`);
    console.log(`  状态: ${waitResult.status}`);

    if (waitResult.status === 'ok') {
      // 触发结果处理
      await this.stone.resultHandler.handleResult(agentId, waitResult.lastMessage);

      // 记录到存储
      await this.stone.getStorage().recordCompletion(agentId, runId, {
        timestamp: Date.now(),
        lastMessage: waitResult.lastMessage,
      });

      return { success: true, status: 'ok', lastMessage: waitResult.lastMessage };
    } else if (waitResult.status === 'timeout') {
      // 超时处理
      await this.handleTimeout(agentId, runId);
      return { success: false, status: 'timeout' };
    } else if (waitResult.status === 'error') {
      // 错误处理
      await this.handleError(agentId, runId, waitResult.error);
      return { success: false, status: 'error', error: waitResult.error };
    }

    return { success: false, status: 'unknown' };
  }

  /**
   * 处理 subagent abort
   */
  async handleSubagentAbort(data) {
    const { agentId, runId } = data;

    console.log(`\n⚠️ 处理 subagent abort: ${agentId} (${runId})`);

    // 获取重试次数
    const currentRetries = this.retryCount.get(runId) || 0;
    const maxRetries = this.config.subagents.maxRetries;

    if (currentRetries >= maxRetries) {
      console.log(`❌ 超过最大重试次数 (${maxRetries})`);

      // 发送告警
      await this.sendAlert(agentId, '多次 abort，需要手动检查', 'critical');

      return;
    }

    // 增加重试次数
    this.retryCount.set(runId, currentRetries + 1);

    console.log(`🔄 [${currentRetries + 1}/${maxRetries}] 重新唤醒...`);

    // 获取原始任务
    const runRecord = this.activeRuns.get(runId);
    const task = runRecord ? runRecord.task : '继续之前的任务';

    // 重新唤醒
    const result = await this.wakeupAndMonitor(agentId, task);

    if (result.success) {
      console.log(`✅ 重试成功`);
    } else {
      console.log(`❌ 重试失败: ${result.error}`);
    }
  }

  /**
   * 处理超时
   */
  async handleTimeout(agentId, runId) {
    console.log(`\n⏱️ 处理超时: ${agentId} (${runId})`);

    // 记录到存储
    await this.stone.getStorage().recordError(agentId, runId, {
      type: 'timeout',
      message: 'Subagent 执行超时',
      timestamp: Date.now(),
    });

    // 发送告警
    await this.sendAlert(agentId, '执行超时', 'warning');
  }

  /**
   * 处理错误
   */
  async handleError(agentId, runId, error) {
    console.log(`\n❌ 处理错误: ${agentId} (${runId})`);
    console.log(`  错误: ${error}`);

    // 记录到存储
    await this.stone.getStorage().recordError(agentId, runId, {
      type: 'error',
      message: error,
      timestamp: Date.now(),
    });

    // 发送告警
    await this.sendAlert(agentId, `执行错误: ${error}`, 'error');
  }

  /**
   * 发送告警
   */
  async sendAlert(agentId, message, severity = 'info') {
    console.log(`🚨 告警: ${agentId} - ${message}`);

    // TODO: 发送到飞书群
    // await this.stone.getStorage().sendAlert(agentId, message, severity);
  }

  /**
   * 获取活跃运行
   */
  getActiveRuns() {
    return Array.from(this.activeRuns.values());
  }

  /**
   * 获取运行记录
   */
  getRun(runId) {
    return this.activeRuns.get(runId);
  }
}

export default WakeupManager;
