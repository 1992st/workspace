/**
 * ContextBuilder - 构建 subagent 上下文
 *
 * 功能：
 * 1. 从 AGENTS.md 读取最新状态
 * 2. 从 MONITOR-LOG.md 读取所有监控记录
 * 3. 从失败 session 文件读取摘要
 * 4. 组装成完整的上下文摘要
 */

import fs from 'fs/promises';
import path from 'path';
import { MemoryStore, MemoryType } from './memory-store.js';

class ContextBuilder {
  constructor() {
    this.workspace = process.cwd();
    this.agentsStatesPath = path.join(this.workspace, 'AGENT-STATES.md');
    this.monitorLogPath = path.join(this.workspace, 'MONITOR-LOG.md');
    this.agentsRoot = path.join(process.env.HOME || process.env.USERPROFILE, '.openclaw', 'agents');
    this.memoryStore = new MemoryStore();

    // 初始化 MemoryStore
    this.memoryStore.init().catch(error => {
      console.error(`⚠️ MemoryStore 初始化失败: ${error.message}`);
    });
  }

  /**
   * 构建 agent 的完整上下文
   * @param {string} agentId - Agent ID
   * @returns {Promise<Object>} 上下文对象
   */
  async buildContext(agentId) {
    const context = {
      agentId,
      currentStatus: null,
      historySummary: '',
      failedAttempts: [],
      recentErrors: [],
      // 新增：记忆
      memories: null,
    };

    // 1. 读取 AGENTS.md 获取当前状态
    context.currentStatus = await this.readAgentStatus(agentId);

    // 2. 读取 MONITOR-LOG.md 获取历史记录
    context.historySummary = await this.readHistorySummary(agentId);

    // 3. 从 MemoryStore 读取记忆
    context.memories = this.memoryStore.generateContextSummary(agentId);

    // 4. 读取失败 session 的摘要
    context.failedAttempts = await this.readFailedSessions(agentId);

    // 5. 提取最近的错误信息
    context.recentErrors = this.extractRecentErrors(context);

    return context;
  }

  /**
   * 读取 AGENT-STATES.md 中的 agent 状态
   */
  async readAgentStatus(agentId) {
    try {
      const content = await fs.readFile(this.agentsStatesPath, 'utf-8');
      const agentSection = this.extractSection(content, `### ${agentId}`);

      if (!agentSection) {
        return null;
      }

      // 提取关键信息（修复正则表达式以匹配实际格式）
      const statusMatch = agentSection.match(/-\s*\*\*状态\*\*:\s*([^\n]+)/);
      const lastActivityMatch = agentSection.match(/-\s*\*\*最后活动\*\*:\s*([^\n]+)/);
      const stopDurationMatch = agentSection.match(/-\s*\*\*停滞时长\*\*:\s*([^\n]+)/);
      const descriptionMatch = agentSection.match(/-\s*\*\*说明\*\*:\s*([^\n]+)/);

      return {
        status: statusMatch ? statusMatch[1].trim() : 'unknown',
        lastActivity: lastActivityMatch ? lastActivityMatch[1].trim() : null,
        stopDuration: stopDurationMatch ? stopDurationMatch[1].trim() : null,
        description: descriptionMatch ? descriptionMatch[1].trim() : null,
      };
    } catch (error) {
      console.error(`Error reading agent status: ${error.message}`);
      return null;
    }
  }

  /**
   * 读取 MONITOR-LOG.md 中的历史摘要
   */
  async readHistorySummary(agentId) {
    try {
      const content = await fs.readFile(this.monitorLogPath, 'utf-8');
      const sections = content.split(/## \d{4}-\d{2}-\d{2}/);

      // 提取所有关于该 agent 的记录
      const relevantSections = sections.filter(section =>
        section.includes(agentId)
      );

      // 取最近 5 条记录
      const recentSections = relevantSections.slice(-5);
      return recentSections.join('\n---\n');
    } catch (error) {
      console.error(`Error reading history summary: ${error.message}`);
      return '';
    }
  }

  /**
   * 读取失败 session 的摘要
   */
  async readFailedSessions(agentId) {
    const attempts = [];
    const agentSessionsPath = path.join(this.agentsRoot, agentId, 'sessions');

    try {
      const files = await fs.readdir(agentSessionsPath);
      const jsonlFiles = files.filter(f => f.endsWith('.jsonl'));

      // 按修改时间排序，取最近 10 个
      const fileStats = await Promise.all(
        jsonlFiles.map(async (file) => {
          const filePath = path.join(agentSessionsPath, file);
          const stats = await fs.stat(filePath);
          return { file, stats, path: filePath };
        })
      );

      fileStats.sort((a, b) => b.stats.mtime - a.stats.mtime);
      const recentFiles = fileStats.slice(0, 10);

      for (const { file, path: filePath } of recentFiles) {
        const attempt = await this.readSessionSummary(filePath);
        if (attempt) {
          attempts.push({
            sessionId: file.replace('.jsonl', ''),
            ...attempt,
          });
        }
      }
    } catch (error) {
      console.error(`Error reading failed sessions: ${error.message}`);
    }

    return attempts;
  }

  /**
   * 读取单个 session 的摘要
   */
  async readSessionSummary(sessionPath) {
    try {
      const content = await fs.readFile(sessionPath, 'utf-8');
      const lines = content.trim().split('\n');

      // 取最后 50 行
      const recentLines = lines.slice(-50);

      // 提取关键信息
      let status = 'unknown';
      let lastTask = '';
      let errors = [];
      let result = '';

      for (const line of recentLines) {
        try {
          const entry = JSON.parse(line);
          if (entry.type === 'lifecycle') {
            status = entry.phase;
          } else if (entry.type === 'message' && entry.message?.role === 'assistant') {
            const content = entry.message.content || [];
            for (const item of content) {
              if (item.type === 'text') {
                if (!lastTask) {
                  lastTask = item.text.substring(0, 200);
                }
              } else if (item.type === 'toolResult' && item.isError) {
                errors.push(item.text);
              }
            }
          }
        } catch (e) {
          // 忽略解析错误
        }
      }

      return {
        status,
        lastTask,
        errors: errors.slice(-3), // 最近 3 个错误
        result: status === 'end' ? 'completed' : 'aborted',
      };
    } catch (error) {
      return null;
    }
  }

  /**
   * 提取最近的错误信息
   */
  extractRecentErrors(context) {
    const errors = [];

    for (const attempt of context.failedAttempts) {
      if (attempt.errors) {
        errors.push(...attempt.errors);
      }
    }

    return errors.slice(-5); // 最近 5 个错误
  }

  /**
   * 提取文件中的指定 section
   */
  extractSection(content, sectionName) {
    const lines = content.split('\n');
    const startLine = lines.findIndex(line => line.startsWith(sectionName));

    if (startLine === -1) {
      return null;
    }

    let endLine = lines.findIndex((line, index) =>
      index > startLine && line.startsWith('## ')
    );

    if (endLine === -1) {
      endLine = lines.length;
    }

    return lines.slice(startLine, endLine).join('\n');
  }

  /**
   * 构建任务 prompt
   * @param {string} agentId - Agent ID
   * @param {string} task - 原始任务
   * @returns {Promise<string>} 增强后的任务
   */
  async buildTaskPrompt(agentId, task) {
    const context = await this.buildContext(agentId);

    let prompt = `## 历史上下文摘要\n\n`;

    // 当前状态
    if (context.currentStatus) {
      prompt += `### 当前状态\n`;
      prompt += `- **状态**: ${context.currentStatus.status}\n`;
      prompt += `- **最后活动**: ${context.currentStatus.lastActivity || '未知'}\n`;
      prompt += `- **停滞时长**: ${context.currentStatus.stopDuration || '未知'}\n`;
      prompt += `- **说明**: ${context.currentStatus.description || '未知'}\n\n`;
    }

    // 记忆（新增）
    if (context.memories) {
      prompt += `### 记忆摘要\n\n`;

      // 关键决策记忆
      if (context.memories.criticalDecisions && context.memories.criticalDecisions.length > 0) {
        prompt += `#### 关键决策 (${context.memories.criticalDecisions.length} 条)\n\n`;
        for (const decision of context.memories.criticalDecisions.slice(0, 5)) {
          prompt += `- **${decision.created}**: ${decision.decision}\n`;
        }
        prompt += `\n`;
      }

      // 最近操作
      if (context.memories.recentOperations && context.memories.recentOperations.length > 0) {
        prompt += `#### 最近操作 (${context.memories.recentOperations.length} 条)\n\n`;
        for (const operation of context.memories.recentOperations.slice(0, 10)) {
          prompt += `- **${operation.created}**: ${operation.operation}\n`;
        }
        prompt += `\n`;
      }

      // 最近失败
      if (context.memories.recentFailures && context.memories.recentFailures.length > 0) {
        prompt += `#### 最近失败 (${context.memories.recentFailures.length} 条)\n\n`;
        for (const failure of context.memories.recentFailures.slice(0, 5)) {
          prompt += `- **${failure.created}**: ${failure.failure}\n`;
        }
        prompt += `\n`;
      }
    }

    // 失败尝试
    if (context.failedAttempts.length > 0) {
      prompt += `### 之前的尝试 (${context.failedAttempts.length} 次)\n\n`;
      for (let i = 0; i < Math.min(context.failedAttempts.length, 3); i++) {
        const attempt = context.failedAttempts[i];
        prompt += `#### 尝试 #${i + 1}: ${attempt.sessionId.substring(0, 8)}\n`;
        prompt += `- **结果**: ${attempt.result}\n`;
        if (attempt.lastTask) {
          prompt += `- **任务**: ${attempt.lastTask.substring(0, 100)}...\n`;
        }
        if (attempt.errors && attempt.errors.length > 0) {
          prompt += `- **错误**:\n`;
          for (const error of attempt.errors) {
            prompt += `  - ${error.substring(0, 100)}...\n`;
          }
        }
        prompt += `\n`;
      }
    }

    // 最近的错误
    if (context.recentErrors.length > 0) {
      prompt += `### 最近的错误\n\n`;
      for (const error of context.recentErrors) {
        prompt += `- ${error.substring(0, 150)}...\n`;
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

export default ContextBuilder;
