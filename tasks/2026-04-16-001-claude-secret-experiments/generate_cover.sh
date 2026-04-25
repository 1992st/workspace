#!/bin/bash
# 使用 Chrome 命令行生成配图
# 需要先安装 Chrome 或 Chromium

HTML_FILE="/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-16-001-claude-secret-experiments/xiaohongshu-cover.html"
OUTPUT_FILE="/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-16-001-claude-secret-experiments/xiaohongshu-cover.png"

# 使用 Chrome headless 截图
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless \
  --screenshot="$OUTPUT_FILE" \
  --window-size=900,1200 \
  --hide-scrollbars \
  --disable-gpu \
  "file://$HTML_FILE"

echo "✅ 配图已生成: $OUTPUT_FILE"
echo "尺寸: 900x1200 (3:4 小红书标准)"
