from PIL import Image, ImageDraw, ImageFont
import os

input_path = '/Users/zhangst/Downloads/pexels-cottonbro-3926745.jpg'
output_path = '/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-10-006-florida-openai/xiaohongshu-cover.png'

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

# 加半透明暗色遮罩
overlay = Image.new('RGBA', (W, H), (0, 0, 0, 90))
img = Image.alpha_composite(img.convert('RGBA'), overlay)

draw = ImageDraw.Draw(img)

# 字体探测：优先找Mac常见中文字体
font_paths = [
    '/System/Library/Fonts/PingFang.ttc',
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
    print('找不到中文字体，请检查 /System/Library/Fonts/ 目录')
    exit(1)

print(f'使用字体: {font_path}')

# 加载字体
font_title = ImageFont.truetype(font_path, 96)
font_sub = ImageFont.truetype(font_path, 52)
font_tag = ImageFont.truetype(font_path, 32)

# 文字内容
line1 = 'ChatGPT卷入'
line2 = '校园枪击案调查'
sub = '家长该看什么'
tag = '270条对话记录后的3点警醒'

# 居中绘制
def draw_centered_text(draw, text, y, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (W - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=fill)

draw_centered_text(draw, line1, 480, font_title, 'white')
draw_centered_text(draw, line2, 600, font_title, 'white')
draw_centered_text(draw, sub, 780, font_sub, '#ff6b6b')
draw_centered_text(draw, tag, 880, font_tag, 'rgba(255,255,255,0.85)')

img.convert('RGB').save(output_path)
print(f'封面已生成: {output_path}')
