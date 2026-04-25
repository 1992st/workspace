#!/bin/bash
# 使用 Chrome 命令行生成系列配图

HTML_FILE="/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-16-001-claude-secret-experiments/xiaohongshu-series-1-cover.html"
OUTPUT_FILE="/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-16-001-claude-secret-experiments/xiaohongshu-series-1-cover.png"

/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless \
  --screenshot="$OUTPUT_FILE" \
  --window-size=900,1200 \
  --hide-scrollbars \
  --disable-gpu \
  --virtual-time-budget=1500 \
  "file://$HTML_FILE"

echo "✅ 小红书配图已生成: $OUTPUT_FILE"
echo "尺寸: 900x1200 (3:4 小红书标准)"
echo "主题: Claude 五大实验功能 + BUDDY 重点"
