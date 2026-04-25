#!/usr/bin/env python3
"""生成 Claude 三线部署架构图和收入结构对比图"""

from PIL import Image, ImageDraw, ImageFont
import os

# 创建输出目录
output_dir = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/publish_queue/2026-04-07-optimized"
os.makedirs(output_dir, exist_ok=True)

def get_font(size):
    """获取字体，优先使用系统字体"""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def create_architecture_chart():
    """创建三线部署架构图"""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), '#f8fafc')
    draw = ImageDraw.Draw(img)
    
    # 字体
    font_title = get_font(26)
    font_layer_title = get_font(18)
    font_layer_desc = get_font(15)
    font_sub = get_font(12)
    font_insight = get_font(15)
    font_insight_sub = get_font(13)
    
    # 标题
    draw.text((width//2, 45), "Anthropic 三线部署架构", 
              fill='#0f172a', font=font_title, anchor='mm')
    
    # 三层金字塔结构
    layers = [
        {
            'y': 90, 'w': 500, 'h': 110,
            'color': '#fce7f3', 'border': '#ec4899',
            'title': '🏢 第三线：Enterprise（主战场）',
            'desc': '法律 · 医疗 · 金融 · 全线推进',
            'subtext': '真正的现金牛'
        },
        {
            'y': 220, 'w': 620, 'h': 90,
            'color': '#fef3c7', 'border': '#f59e0b',
            'title': '💻 第二线：Claude Code（场景支点）',
            'desc': '打透 Coding 垂直场景',
            'subtext': 'ARR: 14-19亿美元 (13-18%)'
        },
        {
            'y': 330, 'w': 700, 'h': 80,
            'color': '#e0f2fe', 'border': '#0ea5e9',
            'title': '🔍 第一线：Claude.ai（认知基建）',
            'desc': '建立用户对 AI 的信任',
            'subtext': '前哨侦察 · 铺垫认知'
        }
    ]
    
    for layer in layers:
        x = (width - layer['w']) // 2
        y, w, h = layer['y'], layer['w'], layer['h']
        
        # 阴影
        draw.rectangle([x+4, y+4, x+w+4, y+h+4], fill='#00000015')
        
        # 层背景
        draw.rectangle([x, y, x+w, y+h], fill=layer['color'])
        
        # 边框
        draw.rectangle([x, y, x+w, y+h], outline=layer['border'], width=2)
        
        # 标题
        draw.text((x+20, y+15), layer['title'], 
                  fill='#1e293b', font=font_layer_title)
        
        # 描述
        draw.text((x+20, y+42), layer['desc'], 
                  fill='#475569', font=font_layer_desc)
        
        # 小字（右对齐）
        bbox = draw.textbbox((0, 0), layer['subtext'], font=font_sub)
        text_w = bbox[2] - bbox[0]
        draw.text((x+w-20-text_w, y+18), layer['subtext'], 
                  fill=layer['border'], font=font_sub)
    
    # 绘制虚线箭头
    arrow_color = '#64748b'
    # 箭头1
    for i in range(0, 90, 12):
        draw.line([(400, 310-i), (400, 310-i-6)], fill=arrow_color, width=2)
    # 箭头2
    for i in range(0, 90, 12):
        draw.line([(400, 200-i), (400, 200-i-6)], fill=arrow_color, width=2)
    
    # 箭头头
    draw.polygon([(395, 95), (400, 85), (405, 95)], fill=arrow_color)
    
    # 核心洞察框
    insight_y = 430
    draw.rectangle([50, insight_y, 750, insight_y+55], fill='#1e3a5f')
    draw.text((width//2, insight_y+18), 
              '💡 核心洞察：Claude Code 是"验证战术的试验场"', 
              fill='#ffffff', font=font_insight, anchor='mm')
    draw.text((width//2, insight_y+40), 
              '成功后将复制到法律、医疗等更广阔的企业战场', 
              fill='#ffffff', font=font_insight_sub, anchor='mm')
    
    # 保存
    img.save(f"{output_dir}/chart_architecture.png")
    print(f"✅ 架构图已保存: {output_dir}/chart_architecture.png")

def create_revenue_chart():
    """创建收入结构对比图"""
    width, height = 800, 500
    img = Image.new('RGB', (width, height), '#f8fafc')
    draw = ImageDraw.Draw(img)
    
    # 字体
    font_title = get_font(26)
    font_subtitle = get_font(16)
    font_label = get_font(18)
    font_percent = get_font(32)
    font_desc = get_font(14)
    
    # 标题
    draw.text((width//2, 45), "Claude Code 为什么只占 13-18%？", 
              fill='#0f172a', font=font_title, anchor='mm')
    draw.text((width//2, 75), "定位是'验证战术的试验场'，不是变现终点", 
              fill='#64748b', font=font_subtitle, anchor='mm')
    
    # 饼图中心
    cx, cy, radius = 400, 220, 120
    
    # Claude Code 部分（15%）- 黄色
    draw.pieslice([cx-radius, cy-radius, cx+radius, cy+radius], 
                  start=270, end=324, fill='#fbbf24', outline='#f59e0b', width=2)
    
    # 其他业务部分（85%）- 灰色
    draw.pieslice([cx-radius, cy-radius, cx+radius, cy+radius], 
                  start=324, end=270, fill='#e5e7eb', outline='#9ca3af', width=2)
    
    # 中心文字
    draw.text((cx, cy), "25亿", fill='#0f172a', font=get_font(36), anchor='mm')
    draw.text((cx, cy+30), "美元 ARR", fill='#64748b', font=get_font(14), anchor='mm')
    
    # 图例
    # Claude Code
    draw.rectangle([100, 380, 130, 410], fill='#fbbf24', outline='#f59e0b', width=2)
    draw.text((145, 385), "Claude Code", fill='#1e293b', font=font_label)
    draw.text((145, 405), "13-18% 收入 · 场景支点", fill='#64748b', font=font_desc)
    draw.text((320, 395), "约 14-19 亿美元", fill='#f59e0b', font=get_font(20))
    
    # 其他业务
    draw.rectangle([100, 430, 130, 460], fill='#e5e7eb', outline='#9ca3af', width=2)
    draw.text((145, 435), "其他业务", fill='#1e293b', font=font_label)
    draw.text((145, 455), "82-87% 收入 · API + Enterprise", fill='#64748b', font=font_desc)
    draw.text((320, 445), "约 206-231 亿美元", fill='#9ca3af', font=get_font(20))
    
    # 关键数字标注
    # Claude Code 区域标注
    angle = 297 * 3.14159 / 180
    lx = cx + (radius+40) * 0.9
    ly = cy - (radius+40) * 0.4
    draw.text((lx, ly), "13-18%", fill='#f59e0b', font=get_font(24))
    
    # 保存
    img.save(f"{output_dir}/chart_revenue.png")
    print(f"✅ 收入图已保存: {output_dir}/chart_revenue.png")

if __name__ == "__main__":
    print("🎨 开始生成图表...")
    create_architecture_chart()
    create_revenue_chart()
    print("✨ 全部完成！")
