#!/usr/bin/env node
/**
 * Stone -> Agent 消息发送脚本
 * 使用 Gateway HTTP API 向其他 agent 发送消息
 */

import http from 'http';

const GATEWAY_HOST = '127.0.0.1';
const GATEWAY_PORT = 18789;
const GATEWAY_TOKEN = '6026dcc4ffe9663a47656f60f08c0f77561b31a5ca0133a9';

/**
 * 向指定 agent 发送消息
 * @param {string} agentId - Agent ID (如: ffmedia, agentmesh, Ai-StockAssistant)
 * @param {string} message - 消息内容
 * @returns {Promise<void>}
 */
function sendToAgent(agentId, message) {
  return new Promise((resolve, reject) => {
    const postData = JSON.stringify({
      model: 'openclaw',
      input: message
    });

    const options = {
      hostname: GATEWAY_HOST,
      port: GATEWAY_PORT,
      path: '/v1/responses',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
        'Authorization': `Bearer ${GATEWAY_TOKEN}`,
        'x-openclaw-session-key': `agent:${agentId}:main`
      }
    };

    const req = http.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        if (res.statusCode === 200) {
          console.log(`✅ 成功发送消息到 ${agentId}`);
          console.log(`   消息: ${message}`);
          resolve();
        } else {
          console.error(`❌ 发送失败，状态码: ${res.statusCode}`);
          console.error(`   响应: ${data}`);
          reject(new Error(`HTTP ${res.statusCode}`));
        }
      });
    });

    req.on('error', (error) => {
      console.error(`❌ 发送失败: ${error.message}`);
      reject(error);
    });

    req.write(postData);
    req.end();
  });
}

// CLI 接口
if (import.meta.url === `file://${process.argv[1]}`) {
  const agentId = process.argv[2];
  const message = process.argv[3];

  if (!agentId || !message) {
    console.error('用法: node send-to-agent.js <agentId> <message>');
    console.error('示例: node send-to-agent.js ffmedia "继续执行任务"');
    process.exit(1);
  }

  sendToAgent(agentId, message)
    .then(() => {
      console.log('✅ 完成');
      process.exit(0);
    })
    .catch((error) => {
      console.error('❌ 失败:', error.message);
      process.exit(1);
    });
}

export { sendToAgent };
