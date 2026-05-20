#!/usr/bin/env node
/**
 * 记忆继承系统测试脚本
 *
 * 功能：
 * 1. 初始化 MemoryStore
 * 2. 添加测试记忆
 * 3. 测试 ContextBuilder
 * 4. 验证记忆继承
 */

import('../modules/memory-store.js').then(({ MemoryStore, MemoryType, MemoryPriority }) => {
  runTests(MemoryStore, MemoryType, MemoryPriority);
}).catch(error => {
  console.error('Failed to import MemoryStore:', error);
  process.exit(1);
});

async function runTests(MemoryStore, MemoryType, MemoryPriority) {
  console.log('\n' + '='.repeat(60));
  console.log('  记忆继承系统测试');
  console.log('='.repeat(60));

  // 1. 初始化 MemoryStore
  console.log('\n📦 测试 1: 初始化 MemoryStore');
  const memoryStore = new MemoryStore();
  const initSuccess = await memoryStore.init();

  if (!initSuccess) {
    console.error('❌ MemoryStore 初始化失败');
    return;
  }

  // 2. 添加测试记忆
  console.log('\n📝 测试 2: 添加测试记忆');

  // 关键决策记忆
  await memoryStore.addCriticalMemory('ffmedia', '使用端口 9997 作为 RTSP 输出端口', MemoryPriority.HIGH);
  await memoryStore.addCriticalMemory('ffmedia', '使用 /live/test 作为 RTSP 输出路径', MemoryPriority.HIGH);

  // 操作记忆
  await memoryStore.addOperationMemory('ffmedia', '启动 4 个 RTSP 输入服务器（端口 8554-8557）', MemoryPriority.MEDIUM);
  await memoryStore.addOperationMemory('ffmedia', '修改源代码（端口 9999→9997）', MemoryPriority.MEDIUM);
  await memoryStore.addOperationMemory('ffmedia', '推送 libffmedia.so 到 /oem/', MemoryPriority.MEDIUM);

  // 失败记忆
  await memoryStore.addFailureMemory('ffmedia', 'eth0 无 IP 地址，udhcpc 无法获取 DHCP', MemoryPriority.MEDIUM);

  console.log('✅ 测试记忆已添加');

  // 3. 查询记忆
  console.log('\n🔍 测试 3: 查询记忆');
  const memories = memoryStore.queryMemories('ffmedia');
  console.log(`📊 查询到 ${memories.length} 条记忆`);

  // 显示前 5 条
  console.log('\n最近 5 条记忆:');
  for (let i = 0; i < Math.min(5, memories.length); i++) {
    const m = memories[i];
    console.log(`  ${i + 1}. [${m.type}] ${m.type === 'critical_decision' ? m.decision : (m.type === 'operation' ? m.operation : m.failure)}`);
  }

  // 4. 生成上下文摘要
  console.log('\n📄 测试 4: 生成上下文摘要');
  const summary = memoryStore.generateContextSummary('ffmedia');

  console.log(`\n关键决策: ${summary.criticalDecisions.length} 条`);
  for (const d of summary.criticalDecisions) {
    console.log(`  - ${d.decision}`);
  }

  console.log(`\n最近操作: ${summary.recentOperations.length} 条`);
  for (const o of summary.recentOperations) {
    console.log(`  - ${o.operation}`);
  }

  console.log(`\n最近失败: ${summary.recentFailures.length} 条`);
  for (const f of summary.recentFailures) {
    console.log(`  - ${f.failure}`);
  }

  // 5. 测试 ContextBuilder
  console.log('\n🔨 测试 5: 测试 ContextBuilder');

  try {
    const ContextBuilder = (await import('../modules/context-builder.js')).default;
    const contextBuilder = new ContextBuilder();

    // 等待 MemoryStore 初始化
    await new Promise(resolve => setTimeout(resolve, 1000));

    // 构建上下文
    const context = await contextBuilder.buildContext('ffmedia');

    console.log(`\n✅ ContextBuilder 构建成功`);
    console.log(`  - 当前状态: ${context.currentStatus ? JSON.stringify(context.currentStatus) : 'null'}`);
    console.log(`  - 记忆数量: ${context.memories ? {
      critical: context.memories.criticalDecisions.length,
      operation: context.memories.recentOperations.length,
      failure: context.memories.recentFailures.length,
    } : 'null'}`);
    console.log(`  - 失败尝试: ${context.failedAttempts.length} 条`);

  } catch (error) {
    console.error(`❌ ContextBuilder 测试失败: ${error.message}`);
  }

  // 6. 构建任务 Prompt
  console.log('\n📝 测试 6: 构建任务 Prompt');

  try {
    const ContextBuilder = (await import('../modules/context-builder.js')).default;
    const contextBuilder = new ContextBuilder();

    // 等待 MemoryStore 初始化
    await new Promise(resolve => setTimeout(resolve, 1000));

    const task = '配置设备网络，继续测试 demo_rtsp_multi_splice';
    const prompt = await contextBuilder.buildTaskPrompt('ffmedia', task);

    console.log('\n生成的 Prompt:');
    console.log('-'.repeat(60));
    console.log(prompt.substring(0, 500) + '...');
    console.log('-'.repeat(60));
    console.log(`\n总长度: ${prompt.length} 字符`);

  } catch (error) {
    console.error(`❌ Prompt 构建失败: ${error.message}`);
  }

  // 7. 测试记忆去重
  console.log('\n🔄 测试 7: 测试记忆去重');

  const beforeCount = memoryStore.cache.operation.length;
  await memoryStore.addOperationMemory('ffmedia', '启动 4 个 RTSP 输入服务器（端口 8554-8557）', MemoryPriority.MEDIUM);
  const afterCount = memoryStore.cache.operation.length;

  console.log(`去重前: ${beforeCount} 条`);
  console.log(`去重后: ${afterCount} 条`);
  console.log(`结果: ${beforeCount === afterCount ? '✅ 去重成功' : '❌ 去重失败'}`);

  // 8. 完成总结
  console.log('\n' + '='.repeat(60));
  console.log('  测试完成');
  console.log('='.repeat(60));
  console.log('\n📊 统计:');
  console.log(`  关键决策: ${memoryStore.cache.critical.length} 条`);
  console.log(`  操作记录: ${memoryStore.cache.operation.length} 条`);
  console.log(`  失败记录: ${memoryStore.cache.failure.length} 条`);
  console.log(`\n📁 存储位置:`);
  console.log(`  memory/critical.json`);
  console.log(`  memory/operation.jsonl`);
  console.log(`  memory/failure.jsonl`);
}
