/**
 * Stone Agent - 主入口
 *
 * 事件驱动的 Business Partner Agent
 * 负责协调和管理所有 Agents 的运行
 */

import CONFIG from './config.js';
import { formatDate } from './utils.js';
import { EventListener } from '../modules/event-listener.js';
import { WakeupManager } from '../modules/wakeup-manager.js';
import { ResultHandler } from '../modules/result-handler.js';
import { StatusMonitor } from '../modules/status-monitor.js';
import { Storage } from '../storage/index.js';

/**
 * Stone 主类
 */
export class Stone {
  constructor() {
    this.config = CONFIG;
    this.storage = new Storage(this.config);
    this.eventListener = null;
    this.wakeupManager = null;
    this.resultHandler = null;
    this.statusMonitor = null;
    this.running = false;
    this.subagentRuns = new Map();
  }

  /**
   * 启动 Stone
   */
  async start() {
    console.log('\n' + '='.repeat(50));
    console.log('  🗿 Stone Agent - 启动');
    console.log('='.repeat(50));
    console.log(`  时间: ${formatDate()}`);
    console.log('='.repeat(50));

    try {
      // 1. 初始化存储
      await this.storage.init();
      console.log('✅ 存储初始化完成');

      // 2. 启动事件监听器
      this.eventListener = new EventListener(this);
      await this.eventListener.start();
      console.log('✅ 事件监听器已启动');

      // 3. 启动唤醒管理器
      this.wakeupManager = new WakeupManager(this);
      await this.wakeupManager.start();
      console.log('✅ 唤醒管理器已启动');

      // 4. 启动结果处理器
      this.resultHandler = new ResultHandler(this);
      await this.resultHandler.start();
      console.log('✅ 结果处理器已启动');

      // 5. 启动状态监控器（兼容旧的周期监控）
      this.statusMonitor = new StatusMonitor(this);
      console.log('✅ 状态监控器已启动');

      // 6. 标记为运行中
      this.running = true;

      console.log('\n' + '='.repeat(50));
      console.log('  🗿 Stone Agent - 运行中');
      console.log('='.repeat(50));
      console.log(`  监控 Agents: ${Object.keys(this.config.agents).join(', ')}`);
      console.log('='.repeat(50));

      // 7. 立即运行一次状态监控
      await this.statusMonitor.runMonitoring();

    } catch (error) {
      console.error('\n❌ Stone 启动失败:', error);
      throw error;
    }
  }

  /**
   * 停止 Stone
   */
  async stop() {
    console.log('\n' + '='.repeat(50));
    console.log('  🗿 Stone Agent - 停止');
    console.log('='.repeat(50));

    try {
      // 1. 停止状态监控器
      if (this.statusMonitor) {
        await this.statusMonitor.stop();
        console.log('✅ 状态监控器已停止');
      }

      // 2. 停止结果处理器
      if (this.resultHandler) {
        await this.resultHandler.stop();
        console.log('✅ 结果处理器已停止');
      }

      // 3. 停止唤醒管理器
      if (this.wakeupManager) {
        await this.wakeupManager.stop();
        console.log('✅ 唤醒管理器已停止');
      }

      // 4. 停止事件监听器
      if (this.eventListener) {
        await this.eventListener.stop();
        console.log('✅ 事件监听器已停止');
      }

      // 5. 标记为停止
      this.running = false;

      console.log('\n' + '='.repeat(50));
      console.log('  🗿 Stone Agent - 已停止');
      console.log('='.repeat(50));

    } catch (error) {
      console.error('\n❌ Stone 停止失败:', error);
      throw error;
    }
  }

  /**
   * 获取配置
   */
  getConfig() {
    return this.config;
  }

  /**
   * 获取存储
   */
  getStorage() {
    return this.storage;
  }

  /**
   * 注册 subagent 运行
   */
  registerSubagentRun(agentId, runId) {
    if (!this.subagentRuns.has(agentId)) {
      this.subagentRuns.set(agentId, new Map());
    }
    this.subagentRuns.get(agentId).set(runId, {
      startTime: Date.now(),
      status: 'running',
    });
  }

  /**
   * 取消注册 subagent 运行
   */
  unregisterSubagentRun(agentId, runId) {
    if (this.subagentRuns.has(agentId)) {
      this.subagentRuns.get(agentId).delete(runId);
    }
  }

  /**
   * 获取 subagent 运行记录
   */
  getSubagentRun(agentId, runId) {
    if (this.subagentRuns.has(agentId)) {
      return this.subagentRuns.get(agentId).get(runId);
    }
    return null;
  }

  /**
   * 获取所有 subagent 运行记录
   */
  getAllSubagentRuns() {
    const runs = {};
    for (const [agentId, agentRuns] of this.subagentRuns.entries()) {
      runs[agentId] = Array.from(agentRuns.entries()).map(([runId, run]) => ({
        runId,
        ...run,
      }));
    }
    return runs;
  }
}

/**
 * 单例
 */
let stoneInstance = null;

export function getStone() {
  if (!stoneInstance) {
    stoneInstance = new Stone();
  }
  return stoneInstance;
}

/**
 * 主函数（用于直接运行）
 */
export async function main() {
  const stone = getStone();

  try {
    await stone.start();

    // 保持运行
    console.log('\n💤 Stone 保持运行中... (Ctrl+C 退出)\n');

    // 监听退出信号
    process.on('SIGINT', async () => {
      console.log('\n\n收到退出信号...');
      await stone.stop();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      console.log('\n\n收到终止信号...');
      await stone.stop();
      process.exit(0);
    });

  } catch (error) {
    console.error('\n❌ Stone 运行失败:', error);
    await stone.stop();
    process.exit(1);
  }
}

// 如果直接运行此文件
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}

export default Stone;
