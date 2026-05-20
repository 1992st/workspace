/**
 * Stone - 结果处理器
 *
 * 分析 subagent 结果，判断任务是否完成，生成下一步任务
 */

import { sessions_history } from 'sessions';
import { formatDate } from '../core/utils.js';

/**
 * 结果处理器
 */
export class ResultHandler {
  constructor(stone) {
    this.stone = stone;
    this.config = stone.getConfig();
    this.running = false;
  }

  /**
   * 启动结果处理器
   */
  async start() {
    console.log('\n🔍 启动结果处理器...');

    this.running = false; // 结果处理器不需要持续运行

    console.log('✅ 结果处理器已启动');
  }

  /**
   * 停止结果处理器
   */
  async stop() {
    console.log('\n🔍 停止结果处理器...');

    this.running = false;

    console.log('✅ 结果处理器已停止');
  }

  /**
   * 处理结果
   */
  async handleResult(agentId, lastMessage) {
    console.log(`\n🔍 处理结果: ${agentId}`);
    console.log(`  最后消息: ${lastMessage.message?.substring(0, 100)}...`);

    // 1. 分析结果
    const analysis = await this.analyzeResult(agentId, lastMessage);

    console.log(`  分析结果: ${analysis.status}`);
    console.log(`  任务完成: ${analysis.completed}`);
    console.log(`  需要继续: ${analysis.needsContinue}`);

    // 2. 判断是否完成
    if (analysis.completed) {
      console.log(`✅ 任务完成`);
      await this.handleCompletion(agentId, analysis);
    } else if (analysis.needsContinue) {
      console.log(`🔄 需要继续执行`);
      await this.handleContinue(agentId, analysis);
    } else {
      console.log(`⏸️ 任务进行中，无需操作`);
    }

    // 3. 记录到存储
    await this.stone.getStorage().recordResult(agentId, analysis);

    return analysis;
  }

  /**
   * 分析结果
   */
  async analyzeResult(agentId, message) {
    const content = message.message || '';

    // 1. 读取需求文件
    const requirements = await this.readRequirements(agentId);

    // 2. 检查是否完成
    const completed = this.isTaskComplete(content, requirements);

    // 3. 检查是否需要继续
    const needsContinue = this.needsContinue(content, requirements);

    // 4. 检查是否有阻塞
    const blocked = this.isBlocked(content);

    // 5. 检查是否有错误
    const hasError = this.hasError(content);

    return {
      status: completed ? 'completed' : blocked ? 'blocked' : hasError ? 'error' : 'in_progress',
      completed,
      needsContinue,
      blocked,
      hasError,
      content,
      requirements,
      timestamp: Date.now(),
    };
  }

  /**
   * 读取需求文件
   */
  async readRequirements(agentId) {
    const agentConfig = this.config.agents[agentId];
    if (!agentConfig || !agentConfig.requirementsFile) {
      return null;
    }

    try {
      const { read } = await import('fs');
      const content = await read(`${this.config.workspace}${agentConfig.requirementsFile}`);
      return content;
    } catch (error) {
      console.error(`读取需求文件失败: ${agentConfig.requirementsFile}`, error);
      return null;
    }
  }

  /**
   * 判断任务是否完成
   */
  isTaskComplete(content, requirements) {
    // 简单判断：检查消息中是否包含"完成"关键字
    const completeKeywords = ['任务完成', '已完成', 'finished', 'done', '✅'];

    if (completeKeywords.some(keyword => content.includes(keyword))) {
      return true;
    }

    // 检查需求文件中的任务是否全部完成
    if (requirements) {
      const tasks = this.extractTasks(requirements);
      const completedTasks = tasks.filter(t => t.completed);

      if (tasks.length > 0 && completedTasks.length === tasks.length) {
        return true;
      }
    }

    return false;
  }

  /**
   * 判断是否需要继续
   */
  needsContinue(content, requirements) {
    // 检查消息中是否包含"继续"、"下一步"等关键字
    const continueKeywords = ['继续', '下一步', 'next', '待执行'];

    if (continueKeywords.some(keyword => content.includes(keyword))) {
      return true;
    }

    // 检查是否有未完成的任务
    if (requirements) {
      const tasks = this.extractTasks(requirements);
      const completedTasks = tasks.filter(t => t.completed);

      if (completedTasks.length < tasks.length) {
        return true;
      }
    }

    return false;
  }

  /**
   * 判断是否阻塞
   */
  isBlocked(content) {
    const blockKeywords = ['阻塞', '等待', 'blocked', 'waiting', '暂停'];

    return blockKeywords.some(keyword => content.includes(keyword));
  }

  /**
   * 判断是否有错误
   */
  hasError(content) {
    const errorKeywords = ['错误', '失败', 'error', 'failed', '❌'];

    return errorKeywords.some(keyword => content.includes(keyword));
  }

  /**
   * 从需求文件提取任务列表
   */
  extractTasks(requirements) {
    const tasks = [];
    const taskRegex = /-\s*\[([ x])\]\s*(.+)/g;
    let match;

    while ((match = taskRegex.exec(requirements)) !== null) {
      tasks.push({
        name: match[2].trim(),
        completed: match[1] === 'x',
      });
    }

    return tasks;
  }

  /**
   * 处理完成
   */
  async handleCompletion(agentId, analysis) {
    console.log(`\n✅ 处理任务完成: ${agentId}`);

    // 1. 更新 Agent 状态
    await this.updateAgentStatus(agentId, 'completed');

    // 2. 发送完成通知
    await this.sendCompletionNotification(agentId, analysis);

    // 3. 记录到存储
    await this.stone.getStorage().recordCompletion(agentId, null, {
      timestamp: Date.now(),
      analysis,
    });
  }

  /**
   * 处理继续
   */
  async handleContinue(agentId, analysis) {
    console.log(`\n🔄 处理继续执行: ${agentId}`);

    // 1. 生成下一步任务
    const nextTask = this.generateNextTask(agentId, analysis);

    // 2. 唤醒 agent 继续执行
    const result = await this.stone.wakeupManager.wakeupAndMonitor(agentId, nextTask);

    if (result.success) {
      console.log(`✅ 继续执行成功`);
    } else {
      console.log(`❌ 继续执行失败: ${result.error}`);
    }

    // 3. 记录到存储
    await this.stone.getStorage().recordContinue(agentId, nextTask, {
      timestamp: Date.now(),
      result,
    });
  }

  /**
   * 生成下一步任务
   */
  generateNextTask(agentId, analysis) {
    const content = analysis.content;
    const requirements = analysis.requirements;

    // 1. 检查是否有明确的下一步任务
    const nextStepMatch = content.match(/(?:下一步|next|待执行)[：:]\s*(.+)/i);
    if (nextStepMatch) {
      return nextStepMatch[1].trim();
    }

    // 2. 如果没有，从需求文件中找到第一个未完成的任务
    if (requirements) {
      const tasks = this.extractTasks(requirements);
      const nextTask = tasks.find(t => !t.completed);

      if (nextTask) {
        return `继续执行任务: ${nextTask.name}`;
      }
    }

    // 3. 默认任务
    return '继续之前的任务';
  }

  /**
   * 更新 Agent 状态
   */
  async updateAgentStatus(agentId, status) {
    // 更新 AGENT-STATES.md
    await this.stone.getStorage().updateAgentState(agentId, { status });
  }

  /**
   * 发送完成通知
   */
  async sendCompletionNotification(agentId, analysis) {
    console.log(`📱 发送完成通知: ${agentId}`);

    // TODO: 发送到飞书群
    // await this.stone.getStorage().sendCompletionNotification(agentId, analysis);
  }
}

export default ResultHandler;
