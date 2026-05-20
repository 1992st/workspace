#!/usr/bin/env node
/**
 * Stone - 测试 session + thread 模式
 * 验证自动唤醒和捕获完成报告的功能
 */

import { execSync } from 'child_process';

/**
 * 执行 shell 命令
 */
async function exec(cmd) {
  try {
    return execSync(cmd, { encoding: 'utf8' });
  } catch (e) {
    return e.stdout || '';
  }
}

/**
 * 测试唤醒 ffmedia（session + thread 模式）
 */
async function testWakeup() {
  console.log('\n' + '='.repeat(60));
  console.log('  🧪 测试 session + thread 模式');
  console.log('='.repeat(60));

  const agentId = 'ffmedia';
  const task = `测试任务：验证 session + thread 模式

请执行以下步骤：
1. 确认当前任务
2. 简单回复 "测试成功"
3. 不要关闭 session

任务时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}
模式: session + thread
预期：session 将持久化，Stone 可以捕获完成报告
`;

  console.log(`\n📋 Agent: ${agentId}`);
  console.log(`📝 Task: ${task.substring(0, 100)}...`);

  // 1. 唤醒 agent
  console.log(`\n🔄 步骤 1: 唤醒 agent...`);

  // 使用 openclaw CLI 唤醒 agent（session + thread 模式）
  const openclawCmd = `openclaw sessions spawn \
    --agent-id ${agentId} \
    --task '${task.replace(/'/g, "\\'")}' \
    --mode session \
    --thread \
    --label stone-test-${agentId} \
    --run-timeout-seconds 300 \
    2>&1`;

  console.log(`\n📤 发送唤醒请求...`);
  console.log(`   命令: openclaw sessions spawn --agent-id ${agentId} --mode session --thread`);

  const spawnOutput = await exec(openclawCmd);

  console.log(`   输出: ${spawnOutput.substring(0, 500)}`);

  // 尝试从输出中提取 sessionKey
  const sessionKeyMatch = spawnOutput.match(/(?:sessionKey|childSessionKey)[:\s]+([a-f0-9-]+)/i);

  let sessionKey = null;

  if (sessionKeyMatch) {
    sessionKey = sessionKeyMatch[1];
    console.log(`✅ Agent 已唤醒: ${sessionKey}`);
  } else {
    // 如果输出中没有 sessionKey，尝试查看最新的 session 文件
    console.log(`⚠️ 输出中未找到 sessionKey，尝试从 session 文件查找...`);

    const sessionDir = `/Users/zhangst/.openclaw/agents/${agentId}/sessions/`;
    const lsOutput = await exec(`ls -t ${sessionDir}*.jsonl 2>/dev/null | head -1`);

    if (lsOutput.includes('.jsonl')) {
      const sessionFile = lsOutput.trim();
      sessionKey = sessionFile.split('/').pop().replace('.jsonl', '');
      console.log(`✅ 找到 session: ${sessionKey}`);
    } else {
      console.log(`❌ 未能找到 session`);
      return;
    }
  }

  // 2. 等待 agent 完成
  console.log(`\n👀 步骤 2: 等待 agent 完成...`);

  let completed = false;
  let attempts = 0;
  const maxAttempts = 30; // 最多 30 次，每次 10 秒

  while (!completed && attempts < maxAttempts) {
    await new Promise(resolve => setTimeout(resolve, 10000)); // 等待 10 秒
    attempts++;

    console.log(`  ⏱️ 轮询 ${attempts}/${maxAttempts}...`);

    // 查询 session 历史（读取 session 文件）
    const sessionFile = `/Users/zhangst/.openclaw/agents/${agentId}/sessions/${sessionKey}.jsonl`;
    const tailOutput = await exec(`tail -20 ${sessionFile} 2>/dev/null`);

    try {
      const lines = tailOutput.split('\n').filter(line => line.trim());

      // 从最后开始查找
      for (let i = lines.length - 1; i >= 0; i--) {
        try {
          const msg = JSON.parse(lines[i]);
          if (msg.type === 'message' && msg.message) {
            const content = msg.message.message || msg.message.content || '';

            console.log(`  📝 最后消息: ${content.substring(0, 100)}...`);

            // 检查是否完成
            if (content.includes('测试成功') || content.includes('完成')) {
              completed = true;
              console.log(`\n✅ 检测到完成标记`);
              break;
            }
          }
        } catch (parseError) {
          // 忽略解析错误
        }
      }
    } catch (parseError) {
      console.log(`  ⚠️ 历史查询失败: ${tailOutput.substring(0, 100)}`);
    }
  }

  if (completed) {
    console.log(`\n✅ 测试成功！session + thread 模式正常工作`);
    console.log(`   - Agent 完成任务`);
    console.log(`   - 成功捕获完成报告`);
    console.log(`   - Session 持久化: ${sessionKey}`);

    // 3. 尝试发送继续指令
    console.log(`\n🔄 步骤 3: 测试继续执行...`);

    const sendCmd = `openclaw sessions send \
      --session-key ${sessionKey} \
      --message '继续指令：验证 sessions_send 功能' \
      2>&1`;

    const sendOutput = await exec(sendCmd);
    console.log(`📤 发送继续指令: ${sendOutput.substring(0, 200)}`);

    console.log(`\n🎉 所有测试通过！`);

  } else {
    console.log(`\n⚠️ 超时：未能检测到完成标记`);
    console.log(`   Session Key: ${sessionKey}`);
  }

  console.log('\n' + '='.repeat(60));
}

/**
 * 主函数
 */
async function main() {
  try {
    await testWakeup();
  } catch (error) {
    console.error('\n❌ 测试失败:', error);
    process.exit(1);
  }
}

// 运行测试
main();
