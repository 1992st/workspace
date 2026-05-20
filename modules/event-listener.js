/**
 * Stone - 事件监听器
 *
 * 实时监听 subagent 生命周期事件
 * 使用 sessions_list 作为补充机制
 */

import { sessions_list } from 'sessions';
import { formatDate, extractAgentId, extractRunId, delay } from '../core/utils.js';

/**
 * 事件监听器
 */
export class EventListener {
  constructor(stone) {
    this.stone = stone;
    this.config = stone.getConfig();
    this.running = false;
    this.queryInterval = null;
    this.eventHandlers = {
      onSubagentStart: [],
      onSubagentEnd: [],
      onSubagentError: [],
      onSubagentAbort: [],
    };
  }

  /**
   * 启动事件监听
   */
  async start() {
    console.log('\n👀 启动事件监听器...');

    this.running = true;

    // TODO: 注册真正的 lifecycle 事件监听
    // 目前使用 sessions_list 作为替代
    this.queryInterval = setInterval(() => {
      this.querySubagentStatus();
    }, this.config.subagents.queryIntervalSeconds * 1000);

    // 立即执行一次查询
    await this.querySubagentStatus();

    console.log('✅ 事件监听器已启动');
  }

  /**
   * 停止事件监听
   */
  async stop() {
    console.log('\n👀 停止事件监听器...');

    this.running = false;

    if (this.queryInterval) {
      clearInterval(this.queryInterval);
      this.queryInterval = null;
    }

    console.log('✅ 事件监听器已停止');
  }

  /**
   * 注册事件处理器
   */
  on(event, handler) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].push(handler);
    }
  }

  /**
   * 触发事件
   */
  async emit(event, data) {
    const handlers = this.eventHandlers[event] || [];
    for (const handler of handlers) {
      try {
        await handler(data);
      } catch (error) {
        console.error(`事件处理器错误 (${event}):`, error);
      }
    }
  }

  /**
   * 查询 subagent 状态
   */
  async querySubagentStatus() {
    if (!this.running) return;

    console.log(`\n[${formatDate()}] 📊 查询 subagent 状态...`);

    try {
      // 查询 Stone 创建的所有 subagents
      const result = await sessions_list({
        spawnedBy: this.config.stoneSessionKey,
        activeMinutes: 30,
        limit: 20,
        messageLimit: 5,
      });

      const sessions = result.sessions || [];

      console.log(`  找到 ${sessions.length} 个 subagents`);

      // 检查每个 subagent
      for (const session of sessions) {
        await this.checkSubagent(session);
      }

    } catch (error) {
      console.error('查询 subagent 状态失败:', error);
    }
  }

  /**
   * 检查单个 subagent
   */
  async checkSubagent(session) {
    const agentId = extractAgentId(session.key);
    const runId = session.sessionId;

    console.log(`\n  检查 subagent: ${agentId} (${runId})`);
    console.log(`    状态: ${session.abortedLastRun ? '❌ Abort' : '✅ 正常'}`);
    console.log(`    更新时间: ${new Date(session.updatedAt * 1000).toLocaleString('zh-CN')}`);

    // 检查是否 abort
    if (session.abortedLastRun) {
      console.log(`    ⚠️ 检测到 abort: ${runId}`);

      // 触发 abort 事件
      await this.emit('onSubagentAbort', {
        agentId,
        runId,
        session,
      });

      // 记录到存储
      await this.stone.getStorage().recordAbort(agentId, runId, {
        timestamp: Date.now(),
        reason: 'abortedLastRun',
      });
    }

    // 分析最后一条消息
    if (session.messages && session.messages.length > 0) {
      const lastMessage = session.messages[session.messages.length - 1];
      console.log(`    最后消息: ${lastMessage.message?.substring(0, 100)}...`);

      // 触发 subagent end 事件
      await this.emit('onSubagentEnd', {
        agentId,
        runId,
        session,
        lastMessage,
      });
    }
  }

  /**
   * 监听 subagent 启动（TODO: 真正的事件监听）
   */
  onSubagentStart(handler) {
    this.on('onSubagentStart', handler);
  }

  /**
   * 监听 subagent 结束
   */
  onSubagentEnd(handler) {
    this.on('onSubagentEnd', handler);
  }

  /**
   * 监听 subagent 错误
   */
  onSubagentError(handler) {
    this.on('onSubagentError', handler);
  }

  /**
   * 监听 subagent abort
   */
  onSubagentAbort(handler) {
    this.on('onSubagentAbort', handler);
  }
}

export default EventListener;
