#!/bin/bash

# 给小红书封面图加标题
# 用法: bash add-title-to-cover.sh

INPUT="/Users/zhangst/Downloads/pexels-cottonbro-3926745.jpg"
OUTPUT="/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-10-006-florida-openai/xiaohongshu-cover.png"

# 小红书封面尺寸: 1242x1660 (3:4)
WIDTH=1242
HEIGHT=1660

# 读取原图尺寸并等比裁剪/缩放为 1242x1660
magick convert "$INPUT" -resize ${WIDTH}x${HEIGHT}^ -gravity center -extent ${WIDTH}x${HEIGHT} +repage temp-bg.jpg

# 加暗色遮罩让文字更清晰
magick convert temp-bg.jpg -fill "rgba(0,0,0,0.35)" -draw "rectangle 0,0 ${WIDTH},${HEIGHT}" temp-bg-dark.jpg

# 加标题文字 - 主标题 (使用Mac常见中文字体)
# 优先尝试: Hiragino-Sans-GB-W3, STHeiti, Arial-Bold
FONT="Arial-Bold"
for f in "Hiragino-Sans-GB-W3" "STHeiti-Heavy" "STHeiti-Light" "Arial-Bold"; do
  magick convert -list font | grep -q "$f" && FONT="$f" && break
done

magick convert temp-bg-dark.jpg \
  -font "$FONT" \
  -pointsize 96 \
  -fill white \
  -gravity center \
  -annotate +0+0 "ChatGPT卷入\n校园枪击案调查" \
  -pointsize 52 \
  -fill "#ff6b6b" \
  -annotate +0+180 "家长该看什么" \
  -pointsize 32 \
  -fill "rgba(255,255,255,0.8)" \
  -annotate +0+320 "270条对话记录后的3点警醒" \
  "$OUTPUT"

# 清理临时文件
rm -f temp-bg.jpg temp-bg-dark.jpg

echo "封面已生成: $OUTPUT"
