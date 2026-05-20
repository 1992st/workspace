#!/usr/bin/env node
/**
 * Stone Agent - 启动脚本
 */

import { main } from './core/index.js';

// 启动 Stone
console.log('🗿 启动 Stone Agent...');
main().catch((error) => {
  console.error('启动失败:', error);
  process.exit(1);
});
