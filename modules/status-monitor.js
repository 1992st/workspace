/**
 * Stone - 状态监控器
 *
 * 周期性监控（兼容旧的监控逻辑）
 */

import { sessions_list, sessions_history } from 'sessions';
import { message } from 'message';
import { formatDate, minutesAgo } from '../core/utils.js';

/**
 * 状态监控器
 */
export class StatusMonitor {
  constructor(stone) {
    this.stone = stone;
    this.config = stone.getConfig();
    this.running = false;
    this.monitorInterval = null;
  }

  /**
   * 启动状态监控器
   */
  async start() {
    console.log('\n📊 启动状态监控器...');

    this.running = false; // 周期监控不自动启动，由 cron 触发

    console.log('✅ 状态监控器已启动');
  }

  /**
   * 停止状态监控器
   */
  async stop() {
    console.log('\n📊 停止状态监控器...');

    this.running = false;

    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = null;
    }

    console.log('✅ 状态监控器已停止');
  }

  /**
   * 运行一次监控
   */
  async runMonitoring() {
    console.log('\n' + '='.repeat(50));
    console.log('  📊 Stone 状态监控');
    console.log('='.repeat(50));
    console.log(`  时间: ${formatDate()}`);
    console.log('='.repeat(50));

    try {
      const results = {
        timestamp: formatDate(),
        startTime: Date.now(),
        agents: {},
        alerts: [],
        summary: {
          total: 0,
          normal: 0,
          warning: 0,
          critical: 0,
        },
      };

      // 1. 遍历所有 agents
      for (const agentId of Object.keys(this.config.agents)) {
        console.log(`\n📊 监控 Agent: ${agentId}`);

        const agentResult = await this.monitorAgent(agentId);
        results.agents[agentId] = agentResult;
        results.summary.total++;
        results.summary[agentResult.level]++;
      }

      // 2. 生成报告
      results.endTime = Date.now();
      results.duration = Math.round((results.endTime - results.startTime) / 1000);

      // 3. 汇总告警
      for (const [agentId, agentResult] of Object.entries(results.agents)) {
        if (agentResult.alert) {
          results.alerts.push({
            agentId,
            level: agentResult.level,
            message: agentResult.message,
          });
        }
      }

      // 4. 输出报告
      this.printReport(results);

      // 5. 发送报告到飞书群
      if (results.alerts.length > 0) {
        await this.sendReport(results);
      }

      // 6. 记录到存储
      await this.stone.getStorage().recordMonitoring(results);

      return results;

    } catch (error) {
      console.error('\n❌ 监控失败:', error);
      throw error;
    }
  }

  /**
   * 监控单个 Agent
   */
  async monitorAgent(agentId) {
    const agentConfig = this.config.agents[agentId];

    // 1. 读取 Agent 状态
    const agentState = await this.stone.getStorage().readAgentState(agentId);

    // 2. 检查最后活跃时间
    const lastActive = agentState.lastActiveTime || 'unknown';
    const minutesSinceActive = minutesAgo(lastActive);

    console.log(`  最后活跃: ${lastActive} (${minutesSinceActive}分钟前)`);

    // 3. 检查 subagent 状态
    const subagentInfo = await this.checkSubagentStatus(agentId);

    // 4. 判断状态
    const status = this.determineStatus(minutesSinceActive, subagentInfo);

    console.log(`  状态: ${status.emoji} ${status.message}`);

    // 5. 检查是否需要唤醒
    let wakeupResult = null;
    if (status.needsWakeup) {
      console.log(`  ⚠️ 需要唤醒`);
      wakeupResult = await this.wakeupAgent(agentId, "自动唤醒: 继续之前的任务");
    }

    // 6. 检查 subagent abort
    if (subagentInfo.aborted > 0) {
      console.log(`  ⚠️ 检测到 ${subagentInfo.aborted} 个 abort 的 subagent`);
      await this.handleSubagentAbort(agentId, subagentInfo.aborted);
    }

    return {
      agentId,
      lastActive,
      minutesSinceActive,
      subagentInfo,
      status,
      wakeupResult,
      level: status.level,
      alert: status.level !== 'normal',
      message: status.message,
    };
  }

  /**
   * 检查 subagent 状态
   */
  async checkSubagentStatus(agentId) {
    try {
      const result = await sessions_list({
        spawnedBy: `agent:${agentId}:main`,
        activeMinutes: 30,
        limit: 10,
      });

      const sessions = result.sessions || [];
      const aborted = sessions.filter(s => s.abortedLastRun).length;

      return {
        total: sessions.length,
        aborted,
        lastSubagent: sessions[0] || null,
      };
    } catch (error) {
      console.error(`查询 subagent 状态失败: ${agentId}`, error);
      return { total: 0, aborted: 0, lastSubagent: null };
    }
  }

  /**
   * 判断状态
   */
  determineStatus(minutesSinceActive, subagentInfo) {
    // 阈值（分钟）
    const WARNING_THRESHOLD = 60; // 1 小时
    const CRITICAL_THRESHOLD = 180; // 3 小时

    // 判断
    if (subagentInfo.aborted > 0) {
      return {
        emoji: '🔴',
        level: 'critical',
        message: `${subagentInfo.aborted} 个 subagent 已 abort`,
        needsWakeup: true,
      };
    } else if (minutesSinceActive > CRITICAL_THRESHOLD) {
      return {
        emoji: '🔴',
        level: 'critical',
        message: `停滞超过 ${CRITICAL_THRESHOLD} 分钟`,
        needsWakeup: true,
      };
    } else if (minutesSinceActive > WARNING_THRESHOLD) {
      return {
        emoji: '🟡',
        level: 'warning',
        message: `停滞超过 ${WARNING_THRESHOLD} 分钟`,
        needsWakeup: false,
      };
    } else {
      return {
        emoji: '🟢',
        level: 'normal',
        message: '运行正常',
        needsWakeup: false,
      };
    }
  }

  /**
   * 唤醒 Agent
   */
  async wakeupAgent(agentId, task) {
    console.log(`  🔄 唤醒 ${agentId}...`);

    try {
      const result = await this.stone.wakeupManager.wakeupAndMonitor(agentId, task);

      if (result.success) {
        console.log(`  ✅ 唤醒成功`);
        return { success: true, runId: result.runId };
      } else {
        console.log(`  ❌ 唤醒失败: ${result.error}`);
        return { success: false, error: result.error };
      }
    } catch (error) {
      console.error(`  ❌ 唤醒出错: ${error}`);
      return { success: false, error: error.message };
    }
  }

  /**
   * 处理 subagent abort
   */
  async handleSubagentAbort(agentId, count) {
    console.log(`  ⚠️ 处理 ${count} 个 abort 的 subagent`);

    // 事件监听器会自动处理 abort，这里只需记录
    await this.stone.getStorage().recordAbort(agentId, 'multiple', {
      count,
      timestamp: Date.now(),
    });
  }

  /**
   * 打印报告
   */
  printReport(results) {
    console.log('\n' + '='.repeat(50));
    console.log('  📊 监控报告');
    console.log('='.repeat(50));
    console.log(`  耗时: ${results.duration} 秒`);
    console.log(`  总 Agent 数: ${results.summary.total}`);
    console.log(`  正常: ${results.summary.normal}`);
    console.log(`  警告: ${results.summary.warning}`);
    console.log(`  严重: ${results.summary.critical}`);
    console.log('='.repeat(50));

    if (results.alerts.length > 0) {
      console.log('\n  告警列表:');
      for (const alert of results.alerts) {
        console.log(`    - ${alert.agentId}: ${alert.message}`);
      }
    }
  }

  /**
   * 发送报告到飞书群
   */
  async sendReport(results) {
    console.log('\n📱 发送报告到飞书群...');

    try {
      const message = this.formatReportMessage(results);

      await message({
        channel: 'feishu',
        target: this.config.feishu.groupId,
        message: message,
      });

      console.log('✅ 报告已发送');
    } catch (error) {
      console.error('发送报告失败:', error);
    }
  }

  /**
   * 格式化报告消息
   */
  formatReportMessage(results) {
    const lines = [
      `📊 Stone 监控报告`,
      `时间: ${results.timestamp}`,
      `耗时: ${results.duration} 秒`,
      ``,
      `📊 汇总`,
      `- 总 Agent 数: ${results.summary.total}`,
      `- 正常: ${results.summary.normal}`,
      `- 警告: ${results.summary.warning}`,
      `- 严重: ${results.summary.critical}`,
    ];

    if (results.alerts.length > 0) {
      lines.push(``, `⚠️ 告警:`);
      for (const alert of results.alerts) {
        const emoji = alert.level === 'critical' ? '🔴' : '🟡';
        lines.push(`- ${emoji} ${alert.agentId}: ${alert.message}`);
      }
    }

    lines.push(``, `=`.repeat(40));

    return lines.join('\n');
  }
}

export default StatusMonitor;
