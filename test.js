#!/usr/bin/env node
/**
 * Stone Agent - 测试脚本
 */

import { getStone } from './core/index.js';

async function test() {
  console.log('\n' + '='.repeat(50));
  console.log('  🗿 Stone Agent - 测试');
  console.log('='.repeat(50));

  try {
    // 1. 获取 Stone 实例
    const stone = getStone();
    console.log('\n✅ 获取 Stone 实例');

    // 2. 检查配置
    const config = stone.getConfig();
    console.log('\n📊 配置:');
    console.log(`  Workspace: ${config.workspace}`);
    console.log(`  Agents: ${Object.keys(config.agents).join(', ')}`);
    console.log(`  Feishu Group: ${config.feishu.groupId}`);

    // 3. 检查存储
    console.log('\n💾 存储初始化...');
    await stone.getStorage().init();
    console.log('✅ 存储初始化成功');

    // 4. 读取 Agent 状态
    console.log('\n📊 读取 Agent 状态:');
    for (const agentId of Object.keys(config.agents)) {
      const state = await stone.getStorage().readAgentState(agentId);
      console.log(`  ${agentId}: ${state.status} (${state.lastActiveTime})`);
    }

    // 5. 测试完成
    console.log('\n' + '='.repeat(50));
    console.log('  ✅ 测试完成');
    console.log('='.repeat(50));

  } catch (error) {
    console.error('\n❌ 测试失败:', error);
    process.exit(1);
  }
}

test();
