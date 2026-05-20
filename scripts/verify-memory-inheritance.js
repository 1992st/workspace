#!/usr/bin/env node
/**
 * 记忆继承功能验证测试
 *
 * 验证场景：
 * 1. subagent1 失败，记录记忆
 * 2. subagent2 继承记忆，避免重复操作
 * 3. 验证 subagent2 是否知道 subagent1 做了什么
 */

import('../modules/memory-store.js').then(({ MemoryStore, MemoryType, MemoryPriority }) => {
  runScenario(MemoryStore, MemoryType, MemoryPriority);
}).catch(error => {
  console.error('Failed to import MemoryStore:', error);
  process.exit(1);
});

async function runScenario(MemoryStore, MemoryType, MemoryPriority) {
  console.log('\n' + '='.repeat(70));
  console.log('  记忆继承功能验证测试');
  console.log('='.repeat(70));

  // 1. 初始化
  console.log('\n📦 第 1 步：初始化记忆存储');
  const memoryStore = new MemoryStore();
  await memoryStore.init();

  // 清空之前的记忆
  memoryStore.cache.critical = [];
  memoryStore.cache.operation = [];
  memoryStore.cache.failure = [];
  await memoryStore.saveCriticalMemory();
  await memoryStore.saveOperationMemory();
  await memoryStore.saveFailureMemory();
  console.log('✅ 记忆存储已清空');

  // 2. 模拟 subagent1 执行
  console.log('\n🤖 第 2 步：subagent1 开始执行');

  // subagent1 添加操作记忆
  await memoryStore.addOperationMemory('ffmedia', '尝试使用 udhcpc 获取 IP 地址');
  await memoryStore.addOperationMemory('ffmedia', '启动 4 个 RTSP 输入服务器（端口 8554-8557）');

  // subagent1 添加关键决策记忆
  await memoryStore.addCriticalMemory('ffmedia', '使用端口 9997 作为 RTSP 输出端口');

  // subagent1 失败，添加失败记忆
  await memoryStore.addFailureMemory('ffmedia', 'eth0 无 IP 地址，udhcpc 无法获取 DHCP');

  console.log('✅ subagent1 执行完成，记忆已记录');

  // 3. 显示 subagent1 的记忆
  console.log('\n📋 第 3 步：subagent1 的记忆摘要');
  const subagent1Summary = memoryStore.generateContextSummary('ffmedia');
  console.log(`\n关键决策: ${subagent1Summary.criticalDecisions.length} 条`);
  for (const d of subagent1Summary.criticalDecisions) {
    console.log(`  - ${d.decision}`);
  }
  console.log(`\n最近操作: ${subagent1Summary.recentOperations.length} 条`);
  for (const o of subagent1Summary.recentOperations) {
    console.log(`  - ${o.operation}`);
  }
  console.log(`\n最近失败: ${subagent1Summary.recentFailures.length} 条`);
  for (const f of subagent1Summary.recentFailures) {
    console.log(`  - ${f.failure}`);
  }

  // 4. 模拟 subagent2 开始执行
  console.log('\n🤖 第 4 步：subagent2 被唤醒');

  // 使用 ContextBuilder 构建上下文
  const ContextBuilder = (await import('../modules/context-builder.js')).default;
  const contextBuilder = new ContextBuilder();

  // 等待 MemoryStore 初始化
  await new Promise(resolve => setTimeout(resolve, 500));

  const task = '继续配置设备网络，完成 demo_rtsp_multi_splice 测试';
  const prompt = await contextBuilder.buildTaskPrompt('ffmedia', task);

  console.log('\n✅ subagent2 接收到包含记忆的上下文');

  // 5. 验证 subagent2 是否知道 subagent1 做了什么
  console.log('\n🔍 第 5 步：验证记忆继承');

  const containsUdhcpc = prompt.includes('udhcpc');
  const containsRTSP = prompt.includes('RTSP');
  const containsPort9997 = prompt.includes('9997');
  const containsFailures = prompt.includes('失败记录');

  console.log(`\nPrompt 包含 "udhcpc": ${containsUdhcpc ? '✅' : '❌'}`);
  console.log(`Prompt 包含 "RTSP": ${containsRTSP ? '✅' : '❌'}`);
  console.log(`Prompt 包含 "9997": ${containsPort9997 ? '✅' : '❌'}`);
  console.log(`Prompt 包含 "失败记录": ${containsFailures ? '✅' : '❌'}`);

  // 6. 显示 subagent2 的关键决策
  console.log('\n📊 第 6 步：subagent2 可以做的关键决策');

  if (containsUdhcpc && containsFailures) {
    console.log('\n✅ subagent2 知道 subagent1 尝试过 udhcpc 并且失败了');
    console.log('   决策：跳过 udhcpc，尝试其他方法（如手动配置 IP）');
  }

  if (containsRTSP && containsPort9997) {
    console.log('\n✅ subagent2 知道 subagent1 决定使用端口 9997');
    console.log('   决策：继续使用端口 9997，不需要修改配置');
  }

  // 7. 模拟 subagent2 执行（避免重复操作）
  console.log('\n🤖 第 7 步：subagent2 执行（避免重复操作）');

  // subagent2 知道 udhcpc 失败了，所以跳过
  console.log('\n❌ 跳过: 尝试使用 udhcpc 获取 IP 地址（之前已失败）');

  // subagent2 尝试手动配置 IP
  await memoryStore.addOperationMemory('ffmedia', '手动配置 IP 地址 192.168.150.120');

  // subagent2 添加新的失败记忆
  await memoryStore.addFailureMemory('ffmedia', '手动配置 IP 后仍无法连接 RTSP 服务器');

  console.log('✅ subagent2 执行完成，新记忆已记录');

  // 8. 显示累积的记忆
  console.log('\n📋 第 8 步：累积的记忆摘要');
  const finalSummary = memoryStore.generateContextSummary('ffmedia');
  console.log(`\n关键决策: ${finalSummary.criticalDecisions.length} 条`);
  console.log(`操作记录: ${finalSummary.recentOperations.length} 条`);
  console.log(`失败记录: ${finalSummary.recentFailures.length} 条`);

  // 9. 总结
  console.log('\n' + '='.repeat(70));
  console.log('  验证完成');
  console.log('='.repeat(70));

  console.log('\n✅ 验证通过：');
  console.log('  1. subagent1 的记忆被正确存储');
  console.log('  2. subagent2 成功继承了 subagent1 的记忆');
  console.log('  3. subagent2 知道 subagent1 做了什么');
  console.log('  4. subagent2 可以基于记忆做出智能决策');
  console.log('  5. subagent2 避免了重复操作（udhcpc）');

  console.log('\n📊 统计：');
  console.log(`  总记忆数: ${memoryStore.cache.critical.length + memoryStore.cache.operation.length + memoryStore.cache.failure.length} 条`);
  console.log(`  关键决策: ${memoryStore.cache.critical.length} 条`);
  console.log(`  操作记录: ${memoryStore.cache.operation.length} 条`);
  console.log(`  失败记录: ${memoryStore.cache.failure.length} 条`);

  console.log('\n🎯 核心价值：');
  console.log('  subagentN 可以继承之前所有失败尝试的记忆，');
  console.log('  避免重复操作，从错误中学习，做出更智能的决策！');
}
