#!/usr/bin/env node
/**
 * Stone Agent - 更新 AGENT-STATES.md
 *
 * 确保 AGENT-STATES.md 包含所有监控的 agents
 */

import fs from 'fs';
import path from 'path';
import { formatDate } from './core/utils.js';

const AGENTS = ['ffmedia', 'agentmesh', 'Ai-StockAssistant'];
const AGENT_STATES_FILE = '/Volumes/zhangstExtern/openclaw/workspace/stone/AGENT-STATES.md';

async function updateAgentStates() {
  console.log('\n📊 更新 AGENT-STATES.md...');

  try {
    // 读取现有内容
    let content = '';
    try {
      content = fs.readFileSync(AGENT_STATES_FILE, 'utf-8');
    } catch (error) {
      content = '# Agent 状态跟踪\n\n';
    }

    // 检查每个 agent 是否存在
    for (const agentId of AGENTS) {
      const sectionRegex = new RegExp(`^## ${agentId}\\n`, 'm');

      if (!sectionRegex.test(content)) {
        // 添加新的 agent section
        content += `## ${agentId}\n\n`;
        content += `**状态**: 未知\n`;
        content += `**最后活动时间**: 未知\n`;
        content += `**当前任务**: 未知\n`;
        content += `**进度**: 0%\n`;
        content += `**更新时间**: ${formatDate()}\n`;
        content += `\n`;
        console.log(`✅ 添加 agent: ${agentId}`);
      } else {
        console.log(`ℹ️  agent 已存在: ${agentId}`);
      }
    }

    // 写回文件
    fs.writeFileSync(AGENT_STATES_FILE, content, 'utf-8');
    console.log('✅ AGENT-STATES.md 更新完成');

  } catch (error) {
    console.error('❌ 更新失败:', error);
    process.exit(1);
  }
}

updateAgentStates();
