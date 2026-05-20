#!/usr/bin/env node
/**
 * Stone Agent - 监控 Cron 任务
 * 每 30 分钟运行一次监控
 *
 * 这个任务由 OpenClaw 的 cron 系统调用
 */

import { sessions_send } from 'sessions';
import { message } from 'message';

const STONE_SESSION_KEY = 'agent:stone:main';
const FEISHU_GROUP_ID = 'oc_5347fa823df2385fe75516285e7c215b';

async function runStoneMonitor() {
  console.log('========================================');
  console.log('  Stone - 监控 Cron 任务');
  console.log('========================================');
  console.log(`\n时间: ${new Date().toISOString()}`);

  try {
    // 向 Stone Agent 发送"运行监控"消息
    console.log('\n发送监控请求到 Stone Agent...');

    await sessions_send({
      sessionKey: STONE_SESSION_KEY,
      message: '运行监控',
      timeoutSeconds: 300, // 5 分钟超时
    });

    console.log('✅ 监控请求已发送');
    console.log('\n智能静默模式：不发送常规监控通知（只在需要时发送）');

    console.log('\n========================================');
    console.log('  任务完成');
    console.log('========================================');

    process.exit(0);

  } catch (error) {
    console.error('\n❌ 任务失败:', error);

    // 发送错误通知到飞书群
    try {
      await message({
        channel: 'feishu',
        target: FEISHU_GROUP_ID,
        message: `❌ Stone 监控任务失败\n时间: ${new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}\n错误: ${error.message}`,
      });
    } catch (feishuError) {
      console.error('发送飞书通知失败:', feishuError);
    }

    process.exit(1);
  }
}

runStoneMonitor();
