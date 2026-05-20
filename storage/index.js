/**
 * Stone - 存储管理
 *
 * 负责数据持久化和读取
 */

import { read, write } from 'fs';
import { formatDate } from '../core/utils.js';

/**
 * 存储管理
 */
export class Storage {
  constructor(config) {
    this.config = config;
    this.workspace = config.workspace;
  }

  /**
   * 初始化存储
   */
  async init() {
    console.log('\n💾 初始化存储...');

    // 确保目录存在
    const directories = [
      this.workspace,
      `${this.workspace}requirements/`,
      `${this.workspace}memory/`,
      `${this.workspace}alerts/`,
      `${this.workspace}retrospectives/`,
    ];

    for (const dir of directories) {
      // TODO: 创建目录（OpenClaw 可能需要扩展）
      // await mkdir(dir, { recursive: true });
    }

    console.log('✅ 存储初始化完成');
  }

  /**
   * 读取 Agent 状态
   */
  async readAgentState(agentId) {
    try {
      const content = await read(`${this.workspace}${this.config.storage.agentStates}`);
      return this.parseAgentState(content, agentId);
    } catch (error) {
      console.error(`读取 Agent 状态失败: ${agentId}`, error);
      return this.createDefaultAgentState(agentId);
    }
  }

  /**
   * 解析 Agent 状态
   */
  parseAgentState(content, agentId) {
    // 从 AGENT-STATES.md 中提取 Agent 状态
    const sectionRegex = new RegExp(`^## ${agentId}\\n([\\s\\S]*?)(?=^## |$)`, 'm');
    const match = content.match(sectionRegex);

    if (!match) {
      return this.createDefaultAgentState(agentId);
    }

    const section = match[1];
    const state = {
      agentId,
      lastActiveTime: this.extractField(section, '最后活动时间'),
      status: this.extractField(section, '状态'),
      currentTask: this.extractField(section, '当前任务'),
      progress: this.extractField(section, '进度'),
    };

    return state;
  }

  /**
   * 提取字段
   */
  extractField(content, fieldName) {
    const regex = new RegExp(`\\*\\*${fieldName}\\*\\*:\\s*(.+)`);
    const match = content.match(regex);
    return match ? match[1].trim() : null;
  }

  /**
   * 创建默认 Agent 状态
   */
  createDefaultAgentState(agentId) {
    return {
      agentId,
      lastActiveTime: 'unknown',
      status: 'unknown',
      currentTask: 'unknown',
      progress: '0%',
    };
  }

  /**
   * 更新 Agent 状态
   */
  async updateAgentState(agentId, updates) {
    try {
      const filePath = `${this.workspace}${this.config.storage.agentStates}`;
      let content = await read(filePath);

      // 更新字段
      for (const [key, value] of Object.entries(updates)) {
        const fieldName = this.keyToFieldName(key);
        content = this.updateField(content, fieldName, value);
      }

      await write(filePath, content);
      console.log(`✅ 更新 Agent 状态: ${agentId}`);
    } catch (error) {
      console.error(`更新 Agent 状态失败: ${agentId}`, error);
    }
  }

  /**
   * 键名转换为字段名
   */
  keyToFieldName(key) {
    const mapping = {
      lastActiveTime: '最后活动时间',
      status: '状态',
      currentTask: '当前任务',
      progress: '进度',
    };
    return mapping[key] || key;
  }

  /**
   * 更新字段
   */
  updateField(content, fieldName, value) {
    const regex = new RegExp(`(\\*\\*${fieldName}\\*\\*:\\s*)(.+)`);
    return content.replace(regex, `$1${value}`);
  }

  /**
   * 记录监控结果
   */
  async recordMonitoring(results) {
    try {
      const filePath = `${this.workspace}${this.config.storage.monitorLog}`;
      let content = '';

      try {
        content = await read(filePath);
      } catch {
        content = '# Stone 监控日志\n\n';
      }

      const report = this.formatMonitoringReport(results);
      content += '\n' + report;

      await write(filePath, content);
      console.log(`✅ 记录监控结果`);
    } catch (error) {
      console.error('记录监控结果失败:', error);
    }
  }

  /**
   * 格式化监控报告
   */
  formatMonitoringReport(results) {
    const lines = [
      `## 监控报告 - ${results.timestamp}`,
      ``,
      `**耗时**: ${results.duration} 秒`,
      ``,
      `### 汇总`,
      ``,
      `- 总 Agent 数: ${results.summary.total}`,
      `- 正常: ${results.summary.normal}`,
      `- 警告: ${results.summary.warning}`,
      `- 严重: ${results.summary.critical}`,
      ``,
    ];

    if (results.alerts.length > 0) {
      lines.push(`### 告警`, ``);
      for (const alert of results.alerts) {
        const emoji = alert.level === 'critical' ? '🔴' : '🟡';
        lines.push(`- ${emoji} **${alert.agentId}**: ${alert.message}`);
      }
      lines.push(``);
    }

    lines.push(`---`);

    return lines.join('\n');
  }

  /**
   * 记录 abort
   */
  async recordAbort(agentId, runId, data) {
    try {
      const filePath = `${this.workspace}alerts/${agentId}-abort-${Date.now()}.md`;
      const content = this.formatAbortAlert(agentId, runId, data);
      await write(filePath, content);
      console.log(`✅ 记录 abort: ${agentId}`);
    } catch (error) {
      console.error('记录 abort 失败:', error);
    }
  }

  /**
   * 格式化 abort 告警
   */
  formatAbortAlert(agentId, runId, data) {
    const lines = [
      `# Subagent Abort 告警`,
      ``,
      `**Agent**: ${agentId}`,
      `**Run ID**: ${runId}`,
      `**时间**: ${formatDate(data.timestamp)}`,
      `**原因**: ${data.reason}`,
      ``,
      `---`,
    ];

    return lines.join('\n');
  }

  /**
   * 记录错误
   */
  async recordError(agentId, runId, data) {
    try {
      const filePath = `${this.workspace}alerts/${agentId}-error-${Date.now()}.md`;
      const content = this.formatErrorAlert(agentId, runId, data);
      await write(filePath, content);
      console.log(`✅ 记录错误: ${agentId}`);
    } catch (error) {
      console.error('记录错误失败:', error);
    }
  }

  /**
   * 格式化错误告警
   */
  formatErrorAlert(agentId, runId, data) {
    const lines = [
      `# Agent 错误告警`,
      ``,
      `**Agent**: ${agentId}`,
      `**Run ID**: ${runId}`,
      `**时间**: ${formatDate(data.timestamp)}`,
      `**类型**: ${data.type}`,
      `**消息**: ${data.message}`,
      ``,
      `---`,
    ];

    return lines.join('\n');
  }

  /**
   * 记录完成
   */
  async recordCompletion(agentId, runId, data) {
    try {
      const filePath = `${this.workspace}alerts/${agentId}-completion-${Date.now()}.md`;
      const content = this.formatCompletionRecord(agentId, runId, data);
      await write(filePath, content);
      console.log(`✅ 记录完成: ${agentId}`);
    } catch (error) {
      console.error('记录完成失败:', error);
    }
  }

  /**
   * 格式化完成记录
   */
  formatCompletionRecord(agentId, runId, data) {
    const lines = [
      `# Agent 任务完成`,
      ``,
      `**Agent**: ${agentId}`,
      `**Run ID**: ${runId}`,
      `**时间**: ${formatDate(data.timestamp)}`,
      ``,
      `---`,
    ];

    return lines.join('\n');
  }

  /**
   * 记录结果
   */
  async recordResult(agentId, analysis) {
    try {
      const filePath = `${this.workspace}alerts/${agentId}-result-${Date.now()}.md`;
      const content = this.formatResultRecord(agentId, analysis);
      await write(filePath, content);
      console.log(`✅ 记录结果: ${agentId}`);
    } catch (error) {
      console.error('记录结果失败:', error);
    }
  }

  /**
   * 格式化结果记录
   */
  formatResultRecord(agentId, analysis) {
    const lines = [
      `# Subagent 结果分析`,
      ``,
      `**Agent**: ${agentId}`,
      `**时间**: ${formatDate(analysis.timestamp)}`,
      ``,
      `## 分析结果`,
      ``,
      `- **状态**: ${analysis.status}`,
      `- **完成**: ${analysis.completed ? '是' : '否'}`,
      `- **继续**: ${analysis.needsContinue ? '是' : '否'}`,
      `- **阻塞**: ${analysis.blocked ? '是' : '否'}`,
      `- **错误**: ${analysis.hasError ? '是' : '否'}`,
      ``,
      `## 最后消息`,
      ``,
      analysis.content.substring(0, 500),
      ``,
      `---`,
    ];

    return lines.join('\n');
  }

  /**
   * 记录继续
   */
  async recordContinue(agentId, task, data) {
    try {
      const filePath = `${this.workspace}alerts/${agentId}-continue-${Date.now()}.md`;
      const content = this.formatContinueRecord(agentId, task, data);
      await write(filePath, content);
      console.log(`✅ 记录继续: ${agentId}`);
    } catch (error) {
      console.error('记录继续失败:', error);
    }
  }

  /**
   * 格式化继续记录
   */
  formatContinueRecord(agentId, task, data) {
    const lines = [
      `# Subagent 继续执行`,
      ``,
      `**Agent**: ${agentId}`,
      `**时间**: ${formatDate(data.timestamp)}`,
      ``,
      `## 下一步任务`,
      ``,
      task,
      ``,
      `## 结果`,
      ``,
      JSON.stringify(data.result, null, 2),
      ``,
      `---`,
    ];

    return lines.join('\n');
  }
}

export default Storage;
