#!/bin/bash
#
# Stone -> Agent 消息发送命令
# 用法: stone-msg <agentId> <message>
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "用法: stone-msg <agentId> <message>"
    echo ""
    echo "示例:"
    echo "  stone-msg ffmedia \"继续执行任务\""
    echo "  stone-msg Ai-StockAssistant \"检查上周预测\""
    echo ""
    echo "支持的 Agents:"
    echo "  - ffmedia"
    echo "  - agentmesh"
    echo "  - Ai-StockAssistant"
    exit 1
fi

AGENT_ID="$1"
MESSAGE="$2"

node scripts/send-to-agent.js "$AGENT_ID" "$MESSAGE"
