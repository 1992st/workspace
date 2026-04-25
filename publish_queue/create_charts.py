#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 Claude 信息图表
"""

import os
from PIL import Image, ImageDraw, ImageFont

# 设置输出目录
OUTPUT_DIR = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/publish_queue/2026-04-07-optimized"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 画布尺寸
WIDTH, HEIGHT = 800, 500

# 配色方案
colors = {
    'enterprise_bg': '#FFE4EC',      # 粉色
    'enterprise_border': '#E91E63',
    'code_bg': '#FFF8E1',            # 黄色
    'code_border': '#FFB300',
    'ai_bg': '#E3F2FD',              # 蓝色
    'ai_border': '#1976D2',
    'insight_bg': '#F5F5F5',
    'insight_border': '#424242',
    'text_dark': '#212121',
    'text_light': '#FFFFFF',
    'arrow': '#757575',
}

def get_font(size):
    """获取字体"""
    font_paths = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/Helvetica.ttc',
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=2):
    """绘制圆角矩形"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_arrow(draw, start, end, color, width=2):
    """绘制箭头"""
    import math
    x1, y1 = start
    x2, y2 = end
    
    # 绘制主线
    draw.line([start, end], fill=color, width=width)
    
    # 计算箭头角度
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 10
    arrow_angle = math.pi / 6
    
    # 箭头两个翼
    x3 = x2 - arrow_len * math.cos(angle - arrow_angle)
    y3 = y2 - arrow_len * math.sin(angle - arrow_angle)
    x4 = x2 - arrow_len * math.cos(angle + arrow_angle)
    y4 = y2 - arrow_len * math.sin(angle + arrow_angle)
    
    draw.polygon([(x2, y2), (x3, y3), (x4, y4)], fill=color)

def create_architecture_chart():
    """创建三线部署架构图"""
    img = Image.new('RGB', (WIDTH, HEIGHT), '#FAFAFA')
    draw = ImageDraw.Draw(img)
    
    # 字体
    font_title = get_font(24)
    font_layer = get_font(18)
    font_desc = get_font(13)
    font_insight = get_font(14)
    
    # 标题
    title = "Anthropic 三线部署架构"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - title_w) // 2, 20), title, fill=colors['text_dark'], font=font_title)
    
    # 三层结构的参数
    layer_width = 280
    layer_height = 100
    layer_spacing = 25
    start_y = 70
    center_x = WIDTH // 2 - 100  # 偏左，给右侧洞察框留空间
    
    # 第三线 - Enterprise (最上层)
    y3 = start_y
    x3 = center_x - layer_width // 2
    draw_rounded_rect(draw, [x3, y3, x3 + layer_width, y3 + layer_height], 
                      radius=12, fill=colors['enterprise_bg'], 
                      outline=colors['enterprise_border'], width=2)
    
    # Enterprise 文字
    text = "第三线 Enterprise"
    bbox = draw.textbbox((0, 0), text, font=font_layer)
    tw = bbox[2] - bbox[0]
    draw.text((x3 + (layer_width - tw) // 2, y3 + 15), text, 
              fill=colors['enterprise_border'], font=font_layer)
    
    desc = "主战场 · 法律/医疗/金融"
    bbox = draw.textbbox((0, 0), desc, font=font_desc)
    tw = bbox[2] - bbox[0]
    draw.text((x3 + (layer_width - tw) // 2, y3 + 50), desc, 
              fill=colors['text_dark'], font=font_desc)
    
    # 第二线 - Claude Code (中间层)
    y2 = y3 + layer_height + layer_spacing
    x2 = center_x - layer_width // 2
    draw_rounded_rect(draw, [x2, y2, x2 + layer_width, y2 + layer_height], 
                      radius=12, fill=colors['code_bg'], 
                      outline=colors['code_border'], width=2)
    
    text = "第二线 Claude Code"
    bbox = draw.textbbox((0, 0), text, font=font_layer)
    tw = bbox[2] - bbox[0]
    draw.text((x2 + (layer_width - tw) // 2, y2 + 15), text, 
              fill=colors['code_border'], font=font_layer)
    
    desc = "场景支点 · ARR $14-19亿 (13-18%)"
    bbox = draw.textbbox((0, 0), desc, font=font_desc)
    tw = bbox[2] - bbox[0]
    draw.text((x2 + (layer_width - tw) // 2, y2 + 50), desc, 
              fill=colors['text_dark'], font=font_desc)
    
    # 第一线 - Claude.ai (最下层)
    y1 = y2 + layer_height + layer_spacing
    x1 = center_x - layer_width // 2
    draw_rounded_rect(draw, [x1, y1, x1 + layer_width, y1 + layer_height], 
                      radius=12, fill=colors['ai_bg'], 
                      outline=colors['ai_border'], width=2)
    
    text = "第一线 Claude.ai"
    bbox = draw.textbbox((0, 0), text, font=font_layer)
    tw = bbox[2] - bbox[0]
    draw.text((x1 + (layer_width - tw) // 2, y1 + 15), text, 
              fill=colors['ai_border'], font=font_layer)
    
    desc = "认知基建"
    bbox = draw.textbbox((0, 0), desc, font=font_desc)
    tw = bbox[2] - bbox[0]
    draw.text((x1 + (layer_width - tw) // 2, y1 + 55), desc, 
              fill=colors['text_dark'], font=font_desc)
    
    # 绘制箭头（从下往上指）
    # 从 AI 到 Code
    arrow_x = x1 - 30
    draw_arrow(draw, (arrow_x, y1 + layer_height // 2), 
               (arrow_x, y2 + layer_height // 2), colors['arrow'], 2)
    
    # 从 Code 到 Enterprise
    draw_arrow(draw, (arrow_x, y2 + layer_height // 2), 
               (arrow_x, y3 + layer_height // 2), colors['arrow'], 2)
    
    # 右侧洞察框
    insight_x = center_x + layer_width // 2 + 30
    insight_y = y2 - 10
    insight_w = 200
    insight_h = 120
    
    draw_rounded_rect(draw, [insight_x, insight_y, insight_x + insight_w, insight_y + insight_h],
                      radius=8, fill=colors['insight_bg'], 
                      outline=colors['insight_border'], width=2)
    
    # 洞察标题
    insight_title = "核心洞察"
    bbox = draw.textbbox((0, 0), insight_title, font=font_layer)
    tw = bbox[2] - bbox[0]
    draw.text((insight_x + (insight_w - tw) // 2, insight_y + 12), 
              insight_title, fill=colors['insight_border'], font=font_layer)
    
    # 洞察内容
    lines = [
        "三线是递进关系",
        "不是替代关系",
        "",
        "Code = 战术验证场",
        "Enterprise = 变现终点"
    ]
    line_y = insight_y + 45
    for line in lines:
        if line:
            bbox = draw.textbbox((0, 0), line, font=font_insight)
            tw = bbox[2] - bbox[0]
            draw.text((insight_x + (insight_w - tw) // 2, line_y), 
                      line, fill=colors['text_dark'], font=font_insight)
        line_y += 18
    
    # 保存
    output_path = os.path.join(OUTPUT_DIR, "claude_architecture.png")
    img.save(output_path, "PNG", dpi=(150, 150))
    print(f"✅ 架构图已保存: {output_path}")
    return output_path

def create_revenue_chart():
    """创建收入结构对比图"""
    img = Image.new('RGB', (WIDTH, HEIGHT), '#FAFAFA')
    draw = ImageDraw.Draw(img)
    
    # 字体
    font_title = get_font(22)
    font_subtitle = get_font(14)
    font_label = get_font(16)
    font_percent = get_font(24)
    
    # 标题
    title = "Claude Code 为什么只占收入的 13-18%？"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - title_w) // 2, 25), title, fill=colors['text_dark'], font=font_title)
    
    # 副标题
    subtitle = '因为定位是"验证战术的试验场"，不是变现终点'
    bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    sub_w = bbox[2] - bbox[0]
    draw.text(((WIDTH - sub_w) // 2, 60), subtitle, fill='#757575', font=font_subtitle)
    
    # 绘制饼图
    center_x = 250
    center_y = 280
    radius = 130
    
    # 数据
    code_percent = 15.5  # 取中间值
    other_percent = 100 - code_percent
    
    # 计算角度（从顶部开始，顺时针）
    import math
    
    # 绘制饼图背景（其他业务）
    start_angle = -90  # 从12点钟方向开始
    code_angle = (code_percent / 100) * 360
    
    # 其他业务扇形 (82-87%)
    draw.pieslice([center_x - radius, center_y - radius, 
                   center_x + radius, center_y + radius],
                  start=start_angle + code_angle, end=start_angle + 360,
                  fill='#E0E0E0', outline='#9E9E9E', width=2)
    
    # Claude Code 扇形 (13-18%)
    draw.pieslice([center_x - radius, center_y - radius, 
                   center_x + radius, center_y + radius],
                  start=start_angle, end=start_angle + code_angle,
                  fill=colors['code_bg'], outline=colors['code_border'], width=3)
    
    # 图例区域
    legend_x = 480
    legend_y = 180
    legend_w = 280
    
    # Claude Code 图例
    draw.rectangle([legend_x, legend_y, legend_x + 30, legend_y + 30], 
                   fill=colors['code_bg'], outline=colors['code_border'], width=2)
    draw.text((legend_x + 45, legend_y + 3), "Claude Code", 
              fill=colors['text_dark'], font=font_label)
    draw.text((legend_x + 45, legend_y + 28), "ARR $14-19亿", 
              fill='#757575', font=get_font(12))
    draw.text((legend_x + 180, legend_y + 5), "13-18%", 
              fill=colors['code_border'], font=font_percent)
    
    # 其他业务图例
    legend_y2 = legend_y + 70
    draw.rectangle([legend_x, legend_y2, legend_x + 30, legend_y2 + 30], 
                   fill='#E0E0E0', outline='#9E9E9E', width=2)
    draw.text((legend_x + 45, legend_y2 + 3), "其他业务", 
              fill=colors['text_dark'], font=font_label)
    draw.text((legend_x + 45, legend_y2 + 28), "Enterprise + Claude.ai", 
              fill='#757575', font=get_font(12))
    draw.text((legend_x + 180, legend_y2 + 5), "82-87%", 
              fill='#616161', font=font_percent)
    
    # 底部说明框
    box_x = 80
    box_y = 420
    box_w = 640
    box_h = 60
    
    draw_rounded_rect(draw, [box_x, box_y, box_x + box_w, box_y + box_h],
                      radius=6, fill='#FFF3E0', outline='#FF9800', width=1)
    
    note = "📊 Claude Code 是战术试验场 → 验证成功 → 向 Enterprise 输出"
    bbox = draw.textbbox((0, 0), note, font=font_label)
    tw = bbox[2] - bbox[0]
    draw.text((box_x + (box_w - tw) // 2, box_y + 18), 
              note, fill='#E65100', font=font_label)
    
    # 保存
    output_path = os.path.join(OUTPUT_DIR, "claude_revenue.png")
    img.save(output_path, "PNG", dpi=(150, 150))
    print(f"✅ 收入结构图已保存: {output_path}")
    return output_path

def main():
    print("🎨 开始生成 Claude 信息图表...")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    print()
    
    # 生成两张图表
    path1 = create_architecture_chart()
    path2 = create_revenue_chart()
    
    print()
    print("✨ 全部完成！")
    print(f"   1. {path1}")
    print(f"   2. {path2}")

if __name__ == "__main__":
    main()
