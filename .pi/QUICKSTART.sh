#!/bin/bash
# 快速开始指南

cat << 'EOF'
================================
抖音分析工具 - 快速开始
================================

步骤 1: 获取 TikHub API Key
---------------------------
1. 访问: https://tikhub.io
2. 注册账号
3. 每日签到获取免费额度
4. 复制 API Key

步骤 2: 获取 OpenClaw API Token
-------------------------------
运行: cat ~/.openclaw/openclaw.json
复制 "token" 字段的值

步骤 3: 配置
-----------
运行: vi config.yaml

修改以下字段:
- tikhub.api_key = "你的_TikHub_API_Key"
- openclaw.api_token = "你的_OpenClaw_API_Token"

步骤 4: 运行
-----------
分析关键词 "美食":
  ./start.sh 美食

或分析默认关键词 "热门":
  ./start.sh

步骤 5: 查看结果
--------------
控制台输出: 分析报告
结果文件: results.json
日志文件: analyzer.log

--------------------------------
高级用法
--------------------------------

定时任务（每小时分析）:
  crontab -e
  添加: 0 * * * * cd $(pwd) && ./start.sh 美食

测试配置:
  python3 test-config.py

查看详细文档:
  cat README.md

查看更新记录:
  cat CHANGELOG.md

================================
EOF
