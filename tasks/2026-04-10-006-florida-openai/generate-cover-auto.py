from PIL import Image, ImageDraw, ImageFont
import os
import requests

input_path = '/Users/zhangst/Downloads/pexels-cottonbro-3926745.jpg'
output_path = '/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-10-006-florida-openai/xiaohongshu-cover.png'

# 如果本地原图不存在，从 Pexels 下载兜底
if not os.path.exists(input_path):
    img_url = 'https://images.pexels.com/photos/3926745/pexels-photo-3926745.jpeg?auto=compress&cs=tinysrgb&w=1920'
    input_path = '/tmp/xiaohongshu-bg.jpg'
    if not os.path.exists(input_path):
        print('正在下载背景图片...')
        r = requests.get(img_url, timeout=60)
        r.raise_for_status()
        with open(input_path, 'wb') as f:
            f.write(r.content)
        print(f'背景图已保存到: {input_path}')

# 字体探测
font_paths = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/PingFangSC.ttc',
    '/System/Library/Fonts/PingFang SC Regular.otf',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
    '/Library/Fonts/Arial Unicode.ttf',
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
]

font_path = None
for fp in font_paths:
    if os.path.exists(fp):
        font_path = fp
        break

if not font_path:
    font_path = '/tmp/xiaohongshu-fonts/NotoSansCJKsc-Bold.otf'
    if not os.path.exists(font_path):
        print('找不到中文字体，请检查 /System/Library/Fonts/ 目录')
        exit(1)

print(f'使用字体: {font_path}')

# 打开原图并裁剪为 3:4 (1242x1660)
img = Image.open(input_path)
W, H = 1242, 1660
img = img.resize((W, int(img.height * W / img.width)), Image.LANCZOS)
if img.height > H:
    top = (img.height - H) // 2
    img = img.crop((0, top, W, top + H))
else:
    img = img.resize((int(img.width * H / img.height), H), Image.LANCZOS)
    left = (img.width - W) // 2
    img = img.crop((left, 0, left + W, H))

# 遮罩 48%
overlay = Image.new('RGBA', (W, H), (0, 0, 0, 122))
img = Image.alpha_composite(img.convert('RGBA'), overlay)

draw = ImageDraw.Draw(img)

# 字号
font_title1 = ImageFont.truetype(font_path, 120)   # ChatGPT卷入
font_title2 = ImageFont.truetype(font_path, 90)    # 校园枪击案调查
font_sub    = ImageFont.truetype(font_path, 56)    # 副标题
font_tag    = ImageFont.truetype(font_path, 24)    # 右下角标签

line1 = 'ChatGPT卷入'
line2 = '校园枪击案调查'
sub   = '孩子AI越用越溜，家长要学会引导'
tag   = '270条对话记录后的3点警醒'

def draw_text_with_stroke(draw, text, y, font, fill, stroke_color=(0,0,0), stroke_width=4):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (W - (bbox[2] - bbox[0])) // 2
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    draw.text((x, y), text, font=font, fill=fill)

def draw_centered_text(draw, text, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (W - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)

WHITE       = '#ffffff'
DEEP_ORANGE = '#ff9100'   # 副标题深橙色
GRAY        = '#b0b0b0'   # 标签浅灰
BLACK       = '#000000'   # 黑色描边

# ChatGPT卷入：纯白无描边，y=320
draw_centered_text(draw, line1, 320, font_title1, WHITE)
# 校园枪击案调查：黑色描边，y=460
draw_text_with_stroke(draw, line2, 460, font_title2, WHITE, stroke_color=BLACK, stroke_width=4)

# 副标题：深橙色，与主标题拉开大呼吸区
draw_centered_text(draw, sub, 780, font_sub, DEEP_ORANGE)

# 标签：右下角
tag_bbox = draw.textbbox((0, 0), tag, font=font_tag)
tag_w = tag_bbox[2] - tag_bbox[0]
draw.text((W - tag_w - 50, H - 80), tag, font=font_tag, fill=GRAY)

img.convert('RGB').save(output_path)
print(f'✅ 封面已生成: {output_path}')
