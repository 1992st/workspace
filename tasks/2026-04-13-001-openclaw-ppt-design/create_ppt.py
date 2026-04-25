#!/usr/bin/env python3
"""
OpenClaw Deep Dive Presentation Generator
Creates a 10-page PPTX using python-pptx with pure shapes.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import nsmap
from pptx.oxml import parse_xml

# Page dimensions (16:9)
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

# Color palette
BLACK = RGBColor(0, 0, 0)
WHITE = RGBColor(255, 255, 255)
GRAY = RGBColor(161, 161, 166)
GRAY_LIGHT = RGBColor(110, 110, 115)
GRAY_DARK = RGBColor(110, 110, 115)
BLUE = RGBColor(41, 151, 255)
ORANGE = RGBColor(255, 159, 10)
GREEN = RGBColor(48, 209, 88)
PURPLE = RGBColor(167, 139, 250)
BG_WHITE = RGBColor(245, 245, 247)

def px_to_inches_x(px):
    """Convert HTML x position (1920px width) to inches."""
    return Inches(px / 1920 * 13.333)

def px_to_inches_y(py):
    """Convert HTML y position (1080px height) to inches."""
    return Inches(py / 1080 * 7.5)

def px_width_to_inches(px):
    """Convert HTML width to inches."""
    return Inches(px / 1920 * 13.333)

def px_height_to_inches(px):
    """Convert HTML height to inches."""
    return Inches(px / 1080 * 7.5)

def add_text_box(slide, left, top, width, height, text, font_size, font_color=WHITE, bold=False, font_name="SF Pro Display"):
    """Add a text box with specified properties."""
    shape = slide.shapes.add_textbox(left, top, width, height)
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = font_size
    p.font.color.rgb = font_color
    p.font.bold = bold
    p.font.name = font_name
    return shape

def add_centered_text_box(slide, left, top, width, height, text, font_size, font_color=WHITE, bold=False):
    """Add a centered text box."""
    shape = slide.shapes.add_textbox(left, top, width, height)
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = font_size
    p.font.color.rgb = font_color
    p.font.bold = bold
    p.alignment = PP_ALIGN.CENTER
    return shape

def set_slide_bg_color(slide, color):
    """Set slide background color."""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def create_rounded_rect(slide, left, top, width, height, fill_color=None, line_color=None, line_width=Pt(1)):
    """Create a rounded rectangle."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape

def create_rect(slide, left, top, width, height, fill_color=None, line_color=None, line_width=Pt(1)):
    """Create a rectangle."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape

def create_oval(slide, left, top, width, height, fill_color=None, line_color=None, line_width=Pt(1)):
    """Create an oval/circle."""
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, left, top, width, height)
    if fill_color:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill_color
    else:
        shape.fill.background()
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape

def create_badge(slide, left, top, text):
    """Create a pill-shaped badge."""
    padding_x = Inches(0.28)
    padding_y = Inches(0.12)
    font_size = Pt(18)
    
    # Estimate width based on text
    text_width = Inches(len(text) * 0.09)
    total_width = text_width + padding_x * 2
    total_height = Inches(0.45)
    
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, total_width, total_height)
    shape.fill.background()
    shape.line.color.rgb = RGBColor(255, 255, 255)
    shape.line.width = Pt(0.5)
    
    tf = shape.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = font_size
    p.font.color.rgb = RGBColor(110, 110, 115)
    p.alignment = PP_ALIGN.CENTER
    tf.paragraphs[0].space_before = Pt(0)
    tf.paragraphs[0].space_after = Pt(0)
    
    return shape

def add_code_style_text(slide, left, top, width, height, lines, font_size=Pt(15)):
    """Add code-style text (monospace)."""
    shape = slide.shapes.add_textbox(left, top, width, height)
    tf = shape.text_frame
    tf.word_wrap = True
    
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = font_size
        p.font.color.rgb = RGBColor(193, 193, 198)
        p.font.name = "SF Mono"
        p.space_after = Pt(4)
    
    return shape

# Create presentation
prs = Presentation()
prs.slide_width = SLIDE_WIDTH
prs.slide_height = SLIDE_HEIGHT

# ==================== PAGE 1: Cover ====================
slide1 = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout
set_slide_bg_color(slide1, BLACK)

# Title
add_text_box(slide1, px_to_inches_x(80), px_to_inches_y(340), Inches(10), Inches(1.5),
             "OpenClaw 功能拆解", Pt(110), WHITE, bold=True)

# Subtitle
add_text_box(slide1, px_to_inches_x(84), px_to_inches_y(490), Inches(10), Inches(0.8),
             "从 Prompt 工程到 Agent 上下文管理", Pt(42), GRAY)

# Badge
create_badge(slide1, px_to_inches_x(84), px_to_inches_y(620), "Engineering Deep Dive")

# Decor elements on right
# Large rounded rectangle border
right_rect = create_rounded_rect(slide1, px_to_inches_x(1380), px_to_inches_y(260),
                                  px_width_to_inches(420), px_height_to_inches(560),
                                  fill_color=None, line_color=RGBColor(255, 255, 255), line_width=Pt(0.5))
right_rect.line.color.rgb = RGBColor(255, 255, 255)

# Outer ring
outer_ring = create_oval(slide1, px_to_inches_x(1480), px_to_inches_y(360),
                         px_width_to_inches(220), px_height_to_inches(220),
                         fill_color=None, line_color=RGBColor(255, 255, 255), line_width=Pt(0.5))

# Inner ring
inner_ring = create_oval(slide1, px_to_inches_x(1540), px_to_inches_y(420),
                         px_width_to_inches(100), px_height_to_inches(100),
                         fill_color=None, line_color=RGBColor(255, 255, 255), line_width=Pt(0.5))

# Blue dot
create_oval(slide1, px_to_inches_x(1580), px_to_inches_y(460),
            px_width_to_inches(20), px_height_to_inches(20),
            fill_color=BLUE, line_color=None)

# ==================== PAGE 2: Overview ====================
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide2, BLACK)

# Title
add_text_box(slide2, px_to_inches_x(80), px_to_inches_y(70), Inches(10), Inches(1),
             "OpenClaw 解决什么问题？", Pt(72), WHITE, bold=True)

# Subtitle
add_text_box(slide2, px_to_inches_x(80), px_to_inches_y(165), Inches(10), Inches(0.5),
             "在 LLM 无状态的前提下，搭建一条可控制的能力链", Pt(32), GRAY)

# Bridge line (gradient approximation with red to blue)
bridge = create_rect(slide2, px_to_inches_x(900), px_to_inches_y(500),
                     px_width_to_inches(120), px_height_to_inches(4),
                     fill_color=BLUE, line_color=None)

# Left panel - "Stateless LLM"
add_text_box(slide2, px_to_inches_x(80), px_to_inches_y(320), Inches(3), Inches(0.4),
             "Stateless LLM", Pt(22), GRAY_LIGHT)

# Bubbles
bubble_positions = [(0, 0, 280, 80), (320, 40, 260, 80), (80, 160, 300, 80)]
bubble_texts = ["每次请求都是独立的", "没有长期记忆", "不会主动调用工具"]
for (bx, by, bw, bh), text in zip(bubble_positions, bubble_texts):
    bubble = create_rounded_rect(slide2, px_to_inches_x(80 + bx), px_to_inches_y(370 + by),
                                  px_width_to_inches(bw), px_height_to_inches(bh),
                                  fill_color=RGBColor(255, 255, 255), line_color=RGBColor(255, 255, 255))
    bubble.fill.fore_color.rgb = RGBColor(20, 20, 20)
    bubble.line.color.rgb = RGBColor(255, 255, 255)
    bubble.fill.solid()
    bubble.fill.fore_color.rgb = RGBColor(20, 20, 20)
    add_text_box(slide2, px_to_inches_x(80 + bx + 22), px_to_inches_y(370 + by + 22),
                 px_width_to_inches(bw - 44), px_height_to_inches(bh - 44),
                 text, Pt(18), RGBColor(209, 209, 214))

# Broken line (simplified as rectangle)
broken_line = create_rect(slide2, px_to_inches_x(140), px_to_inches_y(480),
                          px_width_to_inches(460), px_height_to_inches(2),
                          fill_color=ORANGE, line_color=None)

# Left caption
add_text_box(slide2, px_to_inches_x(80), px_to_inches_y(610), Inches(8), Inches(0.5),
             "断裂的链条：对话、记忆、工具彼此隔离", Pt(24), RGBColor(255, 69, 58))

# Right panel - "OpenClaw Framework"
add_text_box(slide2, px_to_inches_x(1040), px_to_inches_y(320), Inches(4), Inches(0.4),
             "OpenClaw Framework", Pt(22), GRAY_LIGHT)

# 4 stages
stage_names = [("Inject", "注入上下文"), ("Assemble", "拼装 Prompt"),
               ("Extend", "挂载 Skills"), ("Persist", "持久化记忆")]
stage_x = 1040
for i, (name, desc) in enumerate(stage_names):
    sx = stage_x + i * 210
    stage_box = create_rounded_rect(slide2, px_to_inches_x(sx), px_to_inches_y(360),
                                    px_width_to_inches(156), px_height_to_inches(156),
                                    fill_color=None, line_color=WHITE, line_width=Pt(1))
    add_centered_text_box(slide2, px_to_inches_x(sx), px_to_inches_y(395),
                          px_width_to_inches(156), Inches(0.5),
                          name, Pt(26), WHITE, bold=True)
    add_centered_text_box(slide2, px_to_inches_x(sx), px_to_inches_y(445),
                          px_width_to_inches(156), Inches(0.3),
                          desc, Pt(14), GRAY)
    if i < 3:
        # Arrow
        add_text_box(slide2, px_to_inches_x(sx + 156 + 9), px_to_inches_y(430),
                     Inches(0.3), Inches(0.3), "→", Pt(22), RGBColor(255, 255, 255))

# Right caption
add_text_box(slide2, px_to_inches_x(1040), px_to_inches_y(550), Inches(8), Inches(0.5),
             "闭环：把无状态的 LLM 变成可控的 Agent 引擎", Pt(24), BLUE)

# ==================== PAGE 3: Architecture ====================
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide3, BLACK)

add_text_box(slide3, px_to_inches_x(80), px_to_inches_y(60), Inches(10), Inches(0.8),
             "五层数据流", Pt(56), WHITE, bold=True)
add_text_box(slide3, px_to_inches_x(80), px_to_inches_y(135), Inches(10), Inches(0.4),
             "从 Gateway 到 LLM，每一层都精确可控", Pt(26), GRAY)

# 5 stages with arrows
stage_data = [
    ("01", "Gateway", "接收用户消息，通过 agentId + channel 路由到正确的 Agent 实例。", 
     ["agentId: agent-radar-desk", "channel: webchat"]),
    ("02", "Session", "维护当前对话的 history.jsonl，记录用户消息、Assistant 回复、工具调用和自定义标记。",
     ["history.jsonl", "custom entry"]),
    ("03", "Bootstrap", "加载工作区上下文文件（AGENTS.md、SOUL.md 等），并决定注入策略（always / skip / lightweight）。",
     ["contextFiles[]", "contextInjection"]),
    ("04", "System Prompt", "把硬编码规则、项目上下文、动态环境拼成完整的 prompt string，供 LLM 消费。",
     ["buildAgentSystemPrompt()"]),
    ("05", "Runtime", "发起 LLM 请求，接收回复，解析结构化工具调用，在沙盒或宿主机上执行。",
     ["model: kimi/kimi-code", "tools: exec, read, write..."])
]

stage_width = px_width_to_inches(320)
arrow_width = px_width_to_inches(40)
start_x = 80
for i, (num, name, desc, code_lines) in enumerate(stage_data):
    sx = start_x + i * (320 + 24 + 40)
    
    # Stage box
    stage = create_rounded_rect(slide3, px_to_inches_x(sx), px_to_inches_y(280),
                                stage_width, px_height_to_inches(550),
                                fill_color=RGBColor(10, 10, 10), line_color=RGBColor(40, 40, 40))
    
    # Number
    add_text_box(slide3, px_to_inches_x(sx + 36), px_to_inches_y(316), Inches(2), Inches(0.3),
                 num, Pt(18), GRAY_LIGHT)
    
    # Name
    add_text_box(slide3, px_to_inches_x(sx + 36), px_to_inches_y(352), Inches(2.5), Inches(0.5),
                 name, Pt(34), WHITE, bold=True)
    
    # Desc
    add_text_box(slide3, px_to_inches_x(sx + 36), px_to_inches_y(420), Inches(2.5), Inches(1.5),
                 desc, Pt(20), GRAY)
    
    # Code block background
    code_bg = create_rounded_rect(slide3, px_to_inches_x(sx + 36), px_to_inches_y(580),
                                  px_width_to_inches(260), Inches(1.2),
                                  fill_color=RGBColor(20, 20, 25), line_color=RGBColor(50, 50, 60))
    add_code_style_text(slide3, px_to_inches_x(sx + 54), px_to_inches_y(598),
                        px_width_to_inches(240), Inches(1),
                        code_lines, Pt(15))
    
    # Arrow
    if i < 4:
        add_text_box(slide3, px_to_inches_x(sx + 320 + 8), px_to_inches_y(530),
                     Inches(0.4), Inches(0.5), "→", Pt(28), RGBColor(255, 255, 255))

# Bottom note
add_text_box(slide3, px_to_inches_x(80), px_to_inches_y(940), Inches(12), Inches(0.5),
             "OpenClaw 的价值不在某一层，而在把五层打通成一个可观测、可配置、可替换的管道。", Pt(22), GRAY)

# ==================== PAGE 4: Prompt Overview ====================
slide4 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide4, BLACK)

add_text_box(slide4, px_to_inches_x(80), px_to_inches_y(60), Inches(10), Inches(0.8),
             "Prompt 总览", Pt(56), WHITE, bold=True)
add_text_box(slide4, px_to_inches_x(80), px_to_inches_y(135), Inches(10), Inches(0.4),
             "System Prompt 由三部分拼成", Pt(26), GRAY)

# Left layers
layers_data = [
    ("~35%", "硬编码规则", "Tooling · Safety · Execution Bias · Cron 约束 · Skills · Memory · Self-Update · Sandbox",
     RGBColor(30, 64, 175), RGBColor(96, 165, 250)),
    ("~40%", "工作区上下文", "AGENTS.md · SOUL.md · TOOLS.md · IDENTITY.md · USER.md · MEMORY.md",
     RGBColor(194, 65, 12), RGBColor(251, 146, 60)),
    ("~25%", "动态环境", "Workspace path · Runtime info · Model aliases · Channel capabilities · Thinking mode",
     RGBColor(126, 34, 206), RGBColor(192, 132, 252))
]

for i, (pct, name, items, bg_color, pct_color) in enumerate(layers_data):
    ly = 240 + i * 140
    
    # Layer background (semi-transparent effect with darker color)
    layer_bg = create_rounded_rect(slide4, px_to_inches_x(80), px_to_inches_y(ly),
                                   px_width_to_inches(1200), px_height_to_inches(120),
                                   fill_color=RGBColor(int(bg_color[0]/8), int(bg_color[1]/8), int(bg_color[2]/8)),
                                   line_color=bg_color)
    
    # Percentage
    add_text_box(slide4, px_to_inches_x(120), px_to_inches_y(ly + 34), Inches(1.5), Inches(0.6),
                 pct, Pt(52), pct_color, bold=True)
    
    # Name
    add_text_box(slide4, px_to_inches_x(280), px_to_inches_y(ly + 30), Inches(4), Inches(0.5),
                 name, Pt(28), WHITE, bold=True)
    
    # Items
    add_text_box(slide4, px_to_inches_x(280), px_to_inches_y(ly + 70), Inches(8), Inches(0.5),
                 items, Pt(20), RGBColor(255, 255, 255))

# Right assembly card
assembly = create_rounded_rect(slide4, px_to_inches_x(1340), px_to_inches_y(240),
                               px_width_to_inches(500), px_height_to_inches(600),
                               fill_color=None, line_color=RGBColor(60, 60, 60))

add_text_box(slide4, px_to_inches_x(1376), px_to_inches_y(276), Inches(3), Inches(0.4),
             "ASSEMBLY PROCESS", Pt(22), GRAY_LIGHT)

add_text_box(slide4, px_to_inches_x(1376), px_to_inches_y(320), Inches(4), Inches(0.4),
             "buildAgentSystemPrompt()", Pt(18), GREEN)

# Steps
steps = [
    ("1", "收集 workspace md 文件并做截断/过滤"),
    ("2", "注入框架级硬编码 section"),
    ("3", "拼接 Skills XML 与 Memory prompt"),
    ("4", "追加 Runtime line 和动态环境")
]

for i, (num, text) in enumerate(steps):
    sy = 380 + i * 100
    
    # Circle with number
    circle = create_oval(slide4, px_to_inches_x(1376), px_to_inches_y(sy),
                         Inches(0.35), Inches(0.35),
                         fill_color=RGBColor(60, 60, 60), line_color=None)
    add_centered_text_box(slide4, px_to_inches_x(1376), px_to_inches_y(sy + 2),
                          Inches(0.35), Inches(0.35), num, Pt(14), WHITE, bold=True)
    
    # Step text
    add_text_box(slide4, px_to_inches_x(1420), px_to_inches_y(sy), Inches(3.5), Inches(0.6),
                 text, Pt(18), RGBColor(209, 209, 214))

# Bottom note
add_text_box(slide4, px_to_inches_x(80), px_to_inches_y(960), Inches(12), Inches(0.5),
             "提示词工程的本质不是写更好的 prompt，而是建立一个稳定、可重复、可扩展的拼装管道。", Pt(22), GRAY)

# ==================== PAGE 5: Inject & Assemble ====================
slide5 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide5, BLACK)

add_text_box(slide5, px_to_inches_x(80), px_to_inches_y(60), Inches(10), Inches(0.8),
             "注入与拼装", Pt(56), WHITE, bold=True)
add_text_box(slide5, px_to_inches_x(80), px_to_inches_y(135), Inches(12), Inches(0.4),
             "以一句「你是谁？」为例，看 OpenClaw 注入了多少 Prompt", Pt(26), GRAY)

# Step dots (6 dots, first 5 active)
for i in range(6):
    dx = 80 + i * 30
    dot_color = BLUE if i < 5 else RGBColor(255, 255, 255)
    create_oval(slide5, px_to_inches_x(dx), px_to_inches_y(210),
                px_width_to_inches(14), px_height_to_inches(14),
                fill_color=dot_color if i < 5 else None,
                line_color=RGBColor(100, 100, 100) if i >= 5 else None)

# User bubble
user_bubble = create_rounded_rect(slide5, px_to_inches_x(0), px_to_inches_y(300),
                                  px_width_to_inches(240), px_height_to_inches(80),
                                  fill_color=RGBColor(41, 151, 255), line_color=BLUE)
user_bubble.fill.fore_color.rgb = RGBColor(20, 30, 50)
add_text_box(slide5, px_to_inches_x(0), px_to_inches_y(275), Inches(3), Inches(0.3),
             "User Query", Pt(14), BLUE)
add_text_box(slide5, px_to_inches_x(36), px_to_inches_y(320), Inches(3), Inches(0.5),
             "你是谁？", Pt(28), WHITE)

# Gateway box
gateway_box = create_rounded_rect(slide5, px_to_inches_x(360), px_to_inches_y(280),
                                  px_width_to_inches(220), px_height_to_inches(120),
                                  fill_color=None, line_color=WHITE)
add_centered_text_box(slide5, px_to_inches_x(360), px_to_inches_y(305),
                      px_width_to_inches(220), Inches(0.4),
                      "Gateway / Session", Pt(18), WHITE, bold=True)
add_centered_text_box(slide5, px_to_inches_x(360), px_to_inches_y(345),
                      px_width_to_inches(220), Inches(0.3),
                      "check bootstrap status", Pt(13), GRAY)

# Arrow from user to gateway
arrow1 = create_rect(slide5, px_to_inches_x(240), px_to_inches_y(335),
                     px_width_to_inches(100), px_height_to_inches(2),
                     fill_color=RGBColor(100, 100, 100), line_color=None)

# Code snippet
code_bg = create_rounded_rect(slide5, px_to_inches_x(360), px_to_inches_y(420),
                              px_width_to_inches(420), px_height_to_inches(120),
                              fill_color=RGBColor(20, 20, 25), line_color=RGBColor(50, 50, 60))
add_text_box(slide5, px_to_inches_x(378), px_to_inches_y(438), Inches(5), Inches(1),
             "hasCompletedBootstrapTurn(sessionFile)\n{ maxTailBytes: 256000, maxTailRecords: 500 }", 
             Pt(13), RGBColor(193, 193, 198))

# Arrow from gateway to files
arrow2 = create_rect(slide5, px_to_inches_x(580), px_to_inches_y(335),
                     px_width_to_inches(30), px_height_to_inches(2),
                     fill_color=RGBColor(100, 100, 100), line_color=None)

# Files group
files_x = 620
add_text_box(slide5, px_to_inches_x(files_x), px_to_inches_y(280), Inches(4), Inches(0.3),
             "Workspace Context Files", Pt(14), GRAY)

file_items = [
    ("AGENTS.md", "~2.4k"), ("SOUL.md", "~1.1k"), ("TOOLS.md", "~3.8k"),
    ("IDENTITY.md", "~0.6k"), ("USER.md", "~0.4k"), ("MEMORY.md", "~5.2k")
]
for i, (fname, fsize) in enumerate(file_items):
    fy = 320 + i * 35
    # File icon
    create_rect(slide5, px_to_inches_x(files_x), px_to_inches_y(fy + 8),
                px_width_to_inches(8), px_height_to_inches(8),
                fill_color=ORANGE, line_color=None)
    # File name
    add_text_box(slide5, px_to_inches_x(files_x + 20), px_to_inches_y(fy), Inches(1.5), Inches(0.25),
                 fname, Pt(17), WHITE)
    # File size
    add_text_box(slide5, px_to_inches_x(files_x + 200), px_to_inches_y(fy), Inches(0.8), Inches(0.25),
                 fsize, Pt(13), RGBColor(110, 110, 115))

# Arrow from files to assembly
arrow3 = create_rect(slide5, px_to_inches_x(960), px_to_inches_y(400),
                     px_width_to_inches(50), px_height_to_inches(2),
                     fill_color=RGBColor(100, 100, 100), line_color=None)

# Assembly layers
asm_x = 1020
add_text_box(slide5, px_to_inches_x(asm_x), px_to_inches_y(280), Inches(4), Inches(0.3),
             "buildAgentSystemPrompt()", Pt(14), GRAY)

layer_data = [
    ("硬编码规则 · ~30%", "Tooling · Safety · Execution Bias · Skills · Memory · Cron", 
     RGBColor(48, 99, 209)),
    ("项目上下文 · ~45%", "AGENTS / SOUL / TOOLS / IDENTITY / USER / MEMORY.md",
     RGBColor(194, 65, 12)),
    ("动态环境 · ~25%", "Runtime · Workspace path · Model alias · Sandbox info",
     RGBColor(126, 34, 206))
]

for i, (title, desc, color) in enumerate(layer_data):
    ly = 320 + i * 110
    layer = create_rounded_rect(slide5, px_to_inches_x(asm_x), px_to_inches_y(ly),
                                px_width_to_inches(460), px_height_to_inches(90),
                                fill_color=RGBColor(int(color[0]/6), int(color[1]/6), int(color[2]/6)),
                                line_color=color)
    add_text_box(slide5, px_to_inches_x(asm_x + 20), px_to_inches_y(ly + 12), Inches(4), Inches(0.35),
                 title, Pt(17), WHITE, bold=True)
    add_text_box(slide5, px_to_inches_x(asm_x + 20), px_to_inches_y(ly + 45), Inches(5), Inches(0.4),
                 desc, Pt(14), RGBColor(200, 200, 200))

# Prompt stats
stats_y = 750
stats_bg = create_rounded_rect(slide5, px_to_inches_x(asm_x), px_to_inches_y(stats_y),
                               px_width_to_inches(460), px_height_to_inches(120),
                               fill_color=None, line_color=RGBColor(60, 60, 60))

stats_data = [
    ("System Prompt 总字符数", "~85,000 chars"),
    ("单用户 query 长度", "4 chars"),
    ("上下文膨胀倍数", "~21,250×")
]

for i, (label, value) in enumerate(stats_data):
    sy = stats_y + 20 + i * 35
    add_text_box(slide5, px_to_inches_x(asm_x + 24), px_to_inches_y(sy), Inches(3), Inches(0.3),
                 label, Pt(16), GRAY)
    add_text_box(slide5, px_to_inches_x(asm_x + 300), px_to_inches_y(sy), Inches(2), Inches(0.3),
                 value, Pt(16), GREEN)

# Arrow from assembly to LLM
arrow4 = create_rect(slide5, px_to_inches_x(1480), px_to_inches_y(480),
                     px_width_to_inches(50), px_height_to_inches(2),
                     fill_color=RGBColor(100, 100, 100), line_color=None)

# LLM box
llm_box = create_rounded_rect(slide5, px_to_inches_x(1540), px_to_inches_y(400),
                              px_width_to_inches(260), px_height_to_inches(180),
                              fill_color=None, line_color=WHITE)
add_centered_text_box(slide5, px_to_inches_x(1540), px_to_inches_y(450),
                      px_width_to_inches(260), Inches(0.6),
                      "LLM", Pt(32), WHITE, bold=True)
add_centered_text_box(slide5, px_to_inches_x(1540), px_to_inches_y(510),
                      px_width_to_inches(260), Inches(0.5),
                      "System Prompt + User Query\n→ Generate response", Pt(15), GRAY)

# Bottom legend
add_text_box(slide5, px_to_inches_x(80), px_to_inches_y(940), Inches(14), Inches(0.5),
             "核心洞察：你的 4 个字触发了 ~85K 字符的系统上下文注入与拼装，这是 OpenClaw 把无状态 LLM 变成可控 Agent 的关键机制。", 
             Pt(18), GRAY)

# ==================== PAGE 6: Skills ====================
slide6 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide6, BLACK)

add_text_box(slide6, px_to_inches_x(80), px_to_inches_y(60), Inches(10), Inches(0.8),
             "Skills — 可插拔的能力包", Pt(56), WHITE, bold=True)
add_text_box(slide6, px_to_inches_x(80), px_to_inches_y(135), Inches(12), Inches(0.4),
             "不是写在代码里，而是写在声明文件与规范文档里的外部能力", Pt(26), GRAY)

# Definition card
def_card = create_rounded_rect(slide6, px_to_inches_x(80), px_to_inches_y(220),
                               px_width_to_inches(520), px_height_to_inches(200),
                               fill_color=None, line_color=RGBColor(60, 60, 60))
add_text_box(slide6, px_to_inches_x(112), px_to_inches_y(248), Inches(4), Inches(0.3),
             "What is a Skill?", Pt(18), GRAY_LIGHT)
add_text_box(slide6, px_to_inches_x(112), px_to_inches_y(290), Inches(4.5), Inches(1),
             "一个 Skill 由 _manifest.yaml 注册，由 SKILL.md 定义执行规范。Agent 匹配到 Skill 后，必须 Read → Follow → Execute。",
             Pt(22), WHITE)

# Workflow
add_text_box(slide6, px_to_inches_x(80), px_to_inches_y(460), Inches(4), Inches(0.3),
             "Skill 触发 workflow", Pt(14), GRAY_LIGHT)

wf_steps = ["匹配 skill", "read SKILL.md", "严格执行"]
wf_x = 80
for i, step in enumerate(wf_steps):
    is_highlight = i == 1
    sx = wf_x + i * 220
    step_box = create_rounded_rect(slide6, px_to_inches_x(sx), px_to_inches_y(500),
                                   px_width_to_inches(180), px_height_to_inches(70),
                                   fill_color=RGBColor(4, 18, 30) if is_highlight else None,
                                   line_color=BLUE if is_highlight else RGBColor(100, 100, 100))
    add_centered_text_box(slide6, px_to_inches_x(sx), px_to_inches_y(520),
                          px_width_to_inches(180), Inches(0.4),
                          step, Pt(18), WHITE)
    if i < 2:
        add_text_box(slide6, px_to_inches_x(sx + 180 + 10), px_to_inches_y(520),
                     Inches(0.3), Inches(0.3), "→", Pt(22), RGBColor(100, 100, 100))

# Skill cards
add_text_box(slide6, px_to_inches_x(680), px_to_inches_y(220), Inches(4), Inches(0.3),
             "OpenClaw 内置 Skill 示例", Pt(14), GRAY_LIGHT)

skill_data = [
    ("device-build-debug", "SSH 编译、rsync 烧录、adb 调试完整链路", "hardware", True),
    ("weather", "调用 wttr.in / Open-Meteo 获取天气与预报", "api", False),
    ("github", "基于 gh CLI 的 Issue / PR / CI 操作", "cli", False),
    ("docx", "生成、编辑、重组 Word 文档", "document", False),
    ("pptx", "生成 PowerPoint 幻灯片与演讲稿", "document", False)
]

card_x = 680
for i, (name, desc, tag, is_highlight) in enumerate(skill_data):
    cx = card_x + i * 230
    card = create_rounded_rect(slide6, px_to_inches_x(cx), px_to_inches_y(260),
                               px_width_to_inches(210), px_height_to_inches(220),
                               fill_color=RGBColor(15, 9, 0) if is_highlight else None,
                               line_color=ORANGE if is_highlight else RGBColor(60, 60, 60))
    add_text_box(slide6, px_to_inches_x(cx + 22), px_to_inches_y(282), Inches(2), Inches(0.35),
                 name, Pt(20), WHITE, bold=True)
    add_text_box(slide6, px_to_inches_x(cx + 22), px_to_inches_y(330), Inches(2), Inches(0.8),
                 desc, Pt(15), GRAY)
    add_text_box(slide6, px_to_inches_x(cx + 22), px_to_inches_y(440), Inches(2), Inches(0.25),
                 tag, Pt(12), RGBColor(110, 110, 115))

# Source precedence pyramid
add_text_box(slide6, px_to_inches_x(80), px_to_inches_y(660), Inches(4), Inches(0.3),
             "来源优先级（高 → 低）", Pt(14), GRAY_LIGHT)

pyramid_levels = [
    (180, "workspace/skills（项目级，可覆盖内置）", True),
    (240, "workspace/.agents/skills", False),
    (300, "~/.agents/skills", False),
    (360, "~/.openclaw/skills", False),
    (420, "OpenClaw bundled", False),
    (480, "extraDirs / 外部目录", False)
]

for i, (width, text, is_top) in enumerate(pyramid_levels):
    py = 700 + i * 40
    px = 80 + (480 - width) // 2
    level = create_rounded_rect(slide6, px_to_inches_x(px), px_to_inches_y(py),
                                px_width_to_inches(width), px_height_to_inches(34),
                                fill_color=RGBColor(20, 12, 0) if is_top else RGBColor(30, 30, 30),
                                line_color=ORANGE if is_top else RGBColor(60, 60, 60))
    add_centered_text_box(slide6, px_to_inches_x(px), px_to_inches_y(py + 5),
                          px_width_to_inches(width), Inches(0.25),
                          text, Pt(14), ORANGE if is_top else WHITE)

# Snapshot box
snap_bg = create_rounded_rect(slide6, px_to_inches_x(680), px_to_inches_y(520),
                              px_width_to_inches(520), px_height_to_inches(140),
                              fill_color=RGBColor(3, 16, 7),
                              line_color=GREEN)
add_text_box(slide6, px_to_inches_x(704), px_to_inches_y(540), Inches(4), Inches(0.3),
             "性能优化：skillsSnapshot", Pt(14), GRAY_LIGHT)
add_text_box(slide6, px_to_inches_x(704), px_to_inches_y(580), Inches(4.5), Inches(0.8),
             "父 Agent 通过 sessions_spawn 将 skillsSnapshot 直接传递给子 Agent，跳过磁盘扫描。一次解析，多次复用。",
             Pt(16), RGBColor(209, 209, 214))

# Bottom note
add_text_box(slide6, px_to_inches_x(80), px_to_inches_y(980), Inches(14), Inches(0.4),
             "OpenClaw 的 Skills 本质上是「把外部能力声明化」，让框架不用改核心代码就能持续扩展功能边界。",
             Pt(18), GRAY)

# ==================== PAGE 7: Memory ====================
slide7 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide7, BLACK)

add_text_box(slide7, px_to_inches_x(80), px_to_inches_y(60), Inches(12), Inches(0.8),
             "Memory — 可替换的记忆后端", Pt(56), WHITE, bold=True)
add_text_box(slide7, px_to_inches_x(80), px_to_inches_y(135), Inches(12), Inches(0.4),
             "不是把记忆写死在框架里，而是一个可插拔的 Plugin Slot", Pt(26), GRAY)

# Pipeline stages
stage_info = [
    ("1. 落盘 Files", [
        ("MEMORY.md", "项目级主记忆"),
        ("memory/*.md", "按日期/主题拆分"),
        ("sessionFiles", "可选对话记录")
    ], None),
    ("2. 分块 Chunk + Hash", None, "chunks"),
    ("3. 向量检索 Vector Search", None, "search"),
    ("4. 注入 Prompt 规则", None, "rule")
]

stage_widths = [340, 380, 420, 460]
stage_x = 80
gap = 40

for i, ((title, files, special), sw) in enumerate(zip(stage_info, stage_widths)):
    sx = stage_x + sum(stage_widths[:i]) // 1920 * 13.333 * 96 + i * gap
    actual_x = 80 + i * (340 + 40) if i == 0 else 80 + 380 + 40 + i * 10
    if i == 0:
        actual_x = 80
    elif i == 1:
        actual_x = 460
    elif i == 2:
        actual_x = 880
    else:
        actual_x = 1340
    
    stage_box = create_rounded_rect(slide7, px_to_inches_x(actual_x), px_to_inches_y(240),
                                    px_width_to_inches(sw), px_height_to_inches(400),
                                    fill_color=None, line_color=RGBColor(60, 60, 60))
    
    add_text_box(slide7, px_to_inches_x(actual_x + 28), px_to_inches_y(268), Inches(4), Inches(0.4),
                 title, Pt(20), WHITE, bold=True)
    
    if files:
        for j, (fname, fmeta) in enumerate(files):
            fy = 320 + j * 40
            dot = create_oval(slide7, px_to_inches_x(actual_x + 28), px_to_inches_y(fy + 8),
                              px_width_to_inches(6), px_height_to_inches(6),
                              fill_color=PURPLE, line_color=None)
            add_text_box(slide7, px_to_inches_x(actual_x + 50), px_to_inches_y(fy), Inches(2), Inches(0.3),
                         fname, Pt(15), WHITE)
            add_text_box(slide7, px_to_inches_x(actual_x + 220), px_to_inches_y(fy), Inches(1.5), Inches(0.3),
                         fmeta, Pt(12), GRAY)
    
    if special == "chunks":
        # 12 chunk boxes
        for row in range(3):
            for col in range(4):
                cx = actual_x + 28 + col * 52
                cy = 320 + row * 52
                chunk = create_rounded_rect(slide7, px_to_inches_x(cx), px_to_inches_y(cy),
                                            px_width_to_inches(44), px_height_to_inches(44),
                                            fill_color=RGBColor(20, 16, 30),
                                            line_color=PURPLE)
                add_centered_text_box(slide7, px_to_inches_x(cx), px_to_inches_y(cy + 10),
                                      px_width_to_inches(44), Inches(0.2),
                                      f"C{row*4+col+1}", Pt(10), PURPLE)
        add_text_box(slide7, px_to_inches_x(actual_x + 28), px_to_inches_y(500), Inches(4), Inches(0.3),
                     "每个 chunk 生成 SHA256 用于增量同步", Pt(14), GRAY)
    
    if special == "search":
        # Eye graphic (simplified as circle)
        eye = create_oval(slide7, px_to_inches_x(actual_x + 150), px_to_inches_y(340),
                          px_width_to_inches(120), px_height_to_inches(120),
                          fill_color=None, line_color=RGBColor(255, 255, 255))
        pupil = create_oval(slide7, px_to_inches_x(actual_x + 186), px_to_inches_y(376),
                            px_width_to_inches(48), px_height_to_inches(48),
                            fill_color=PURPLE, line_color=None)
        add_centered_text_box(slide7, px_to_inches_x(actual_x + 28), px_to_inches_y(500), Inches(4), Inches(1),
                              "回答前 必须先 search\nMEMORY.md + memory/*.md", Pt(18), RGBColor(209, 209, 214))
        
        # Backend badges
        badge1 = create_rounded_rect(slide7, px_to_inches_x(actual_x + 80), px_to_inches_y(580),
                                     px_width_to_inches(120), px_height_to_inches(32),
                                     fill_color=RGBColor(3, 16, 7),
                                     line_color=GREEN)
        add_centered_text_box(slide7, px_to_inches_x(actual_x + 80), px_to_inches_y(585),
                              px_width_to_inches(120), Inches(0.25),
                              "builtin 向量索引", Pt(14), GREEN)
        
        badge2 = create_rounded_rect(slide7, px_to_inches_x(actual_x + 220), px_to_inches_y(580),
                                     px_width_to_inches(100), px_height_to_inches(32),
                                     fill_color=RGBColor(3, 12, 20),
                                     line_color=BLUE)
        add_centered_text_box(slide7, px_to_inches_x(actual_x + 220), px_to_inches_y(585),
                              px_width_to_inches(100), Inches(0.25),
                              "qmd 外部后端", Pt(14), BLUE)
    
    if special == "rule":
        rule_bg = create_rounded_rect(slide7, px_to_inches_x(actual_x + 28), px_to_inches_y(320),
                                      px_width_to_inches(420), px_height_to_inches(200),
                                      fill_color=RGBColor(20, 20, 25),
                                      line_color=RGBColor(50, 50, 60))
        add_text_box(slide7, px_to_inches_x(actual_x + 48), px_to_inches_y(340), Inches(5), Inches(1.5),
                     "## Memory\nMandatory recall step:\nsemantically search MEMORY.md\n+ memory/*.md before answering.",
                     Pt(15), RGBColor(193, 193, 198))
    
    if i < 3:
        add_text_box(slide7, px_to_inches_x(actual_x + sw + 10), px_to_inches_y(440),
                     Inches(0.4), Inches(0.4), "→", Pt(28), RGBColor(100, 100, 100))

# Register label
add_text_box(slide7, px_to_inches_x(80), px_to_inches_y(680), Inches(6), Inches(0.4),
             "架构核心：registerMemoryCapability(pluginId, capability)", Pt(18), GRAY)

# Plugin slot diagram
slot_box = create_rounded_rect(slide7, px_to_inches_x(80), px_to_inches_y(740),
                               px_width_to_inches(220), px_height_to_inches(90),
                               fill_color=RGBColor(13, 11, 20),
                               line_color=PURPLE)
add_centered_text_box(slide7, px_to_inches_x(80), px_to_inches_y(755),
                      px_width_to_inches(220), Inches(0.35),
                      "Memory Plugin", Pt(18), PURPLE, bold=True)
add_centered_text_box(slide7, px_to_inches_x(80), px_to_inches_y(790),
                      px_width_to_inches(220), Inches(0.25),
                      "promptBuilder + runtime", Pt(13), GRAY)

# Connector line
conn_line = create_rect(slide7, px_to_inches_x(300), px_to_inches_y(782),
                        px_width_to_inches(100), px_height_to_inches(2),
                        fill_color=RGBColor(100, 100, 100), line_color=None)
add_text_box(slide7, px_to_inches_x(380), px_to_inches_y(775), Inches(0.3), Inches(0.3),
             "▸", Pt(14), RGBColor(100, 100, 100))

# Core box
core_box = create_rounded_rect(slide7, px_to_inches_x(400), px_to_inches_y(740),
                               px_width_to_inches(220), px_height_to_inches(90),
                               fill_color=None, line_color=RGBColor(100, 100, 100))
add_centered_text_box(slide7, px_to_inches_x(400), px_to_inches_y(755),
                      px_width_to_inches(220), Inches(0.35),
                      "OpenClaw Core", Pt(18), WHITE, bold=True)
add_centered_text_box(slide7, px_to_inches_x(400), px_to_inches_y(790),
                      px_width_to_inches(220), Inches(0.25),
                      "不硬编码，只预留 slot", Pt(13), GRAY)

# Callout
callout = create_rounded_rect(slide7, px_to_inches_x(680), px_to_inches_y(720),
                              px_width_to_inches(840), px_height_to_inches(160),
                              fill_color=None, line_color=RGBColor(60, 60, 60))
add_text_box(slide7, px_to_inches_x(712), px_to_inches_y(748), Inches(3), Inches(0.3),
             "设计意图", Pt(18), GRAY_LIGHT)
add_text_box(slide7, px_to_inches_x(712), px_to_inches_y(790), Inches(7), Inches(1),
             "Memory 对 OpenClaw 框架来说是 透明的——框架只负责调用 Plugin 注册的 builder，把结果拼接进 System Prompt。你可以随时替换内置实现，接入自己的向量数据库或企业知识库。",
             Pt(22), WHITE)

# ==================== PAGE 8: Optimizations ====================
slide8 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide8, BLACK)

add_text_box(slide8, px_to_inches_x(80), px_to_inches_y(60), Inches(10), Inches(0.8),
             "效率与主动性", Pt(56), WHITE, bold=True)
add_text_box(slide8, px_to_inches_x(80), px_to_inches_y(135), Inches(12), Inches(0.4),
             "框架在后台默默做的三件事，用户几乎无感知", Pt(26), GRAY)

# Three cards
card_data = [
    ("≋", "Auto-Compaction", "当对话接近 token 上限时，自动调用 LLM 把 80 轮对话压缩成 3 条核心摘要，腾出上下文预算。",
     "80 → 3", "轮次压缩比例", ORANGE, RGBColor(255, 159, 10)),
    ("⚡", "Snapshot", "父 Agent 直接通过 skillsSnapshot 将已解析的 Skill 上下文传递给子 Agent，跳过重复磁盘扫描。",
     "秒启动", "子代理初始化时间", BLUE, RGBColor(41, 151, 255)),
    ("⟳", "Heartbeat", "每 30 分钟自动触发一次 LLM 巡检，读取 HEARTBEAT.md 检查系统状态、队列积压与未完成动作。",
     "30 min", "默认巡检间隔", GREEN, RGBColor(48, 209, 88))
]

card_width = px_width_to_inches(550)
card_gap = px_width_to_inches(40)

for i, (icon, title, desc, metric_num, metric_label, accent_color, accent_rgb) in enumerate(card_data):
    cx = 80 + i * (550 + 40)
    
    card = create_rounded_rect(slide8, px_to_inches_x(cx), px_to_inches_y(280),
                               card_width, px_height_to_inches(540),
                               fill_color=None, line_color=RGBColor(60, 60, 60))
    
    # Icon
    icon_box = create_rounded_rect(slide8, px_to_inches_x(cx + 50), px_to_inches_y(330),
                                   Inches(0.8), Inches(0.8),
                                   fill_color=RGBColor(int(accent_rgb[0]/10), int(accent_rgb[1]/10), int(accent_rgb[2]/10)),
                                   line_color=accent_rgb)
    add_centered_text_box(slide8, px_to_inches_x(cx + 50), px_to_inches_y(355),
                          Inches(0.8), Inches(0.4),
                          icon, Pt(32), accent_rgb, bold=True)
    
    # Title
    add_text_box(slide8, px_to_inches_x(cx + 50), px_to_inches_y(440), Inches(5), Inches(0.6),
                 title, Pt(38), WHITE, bold=True)
    
    # Desc
    add_text_box(slide8, px_to_inches_x(cx + 50), px_to_inches_y(510), Inches(5), Inches(1.2),
                 desc, Pt(22), GRAY)
    
    # Divider line
    div_line = create_rect(slide8, px_to_inches_x(cx + 50), px_to_inches_y(640),
                           px_width_to_inches(450), px_height_to_inches(1),
                           fill_color=RGBColor(60, 60, 60), line_color=None)
    
    # Metric
    add_text_box(slide8, px_to_inches_x(cx + 50), px_to_inches_y(660), Inches(5), Inches(0.7),
                 metric_num, Pt(48), WHITE, bold=True)
    add_text_box(slide8, px_to_inches_x(cx + 50), px_to_inches_y(730), Inches(5), Inches(0.3),
                 metric_label, Pt(16), RGBColor(110, 110, 115))

# Bottom line
add_text_box(slide8, px_to_inches_x(80), px_to_inches_y(940), Inches(14), Inches(0.5),
             "这三项优化的共同目标：让框架在大规模、长对话、多子代理场景下保持高效与稳定。", Pt(24), GRAY)

# ==================== PAGE 9: P100 Case ====================
slide9 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide9, BLACK)

add_text_box(slide9, px_to_inches_x(80), px_to_inches_y(60), Inches(12), Inches(0.8),
             "P100-recordpen 编译 + 烧录 + 调试", Pt(52), WHITE, bold=True)
add_text_box(slide9, px_to_inches_x(80), px_to_inches_y(130), Inches(12), Inches(0.4),
             "一个真实请求如何同时激活四个子系统", Pt(24), GRAY)

# User request (centered)
request_box = create_rounded_rect(slide9, px_to_inches_x(660), px_to_inches_y(240),
                                  px_width_to_inches(600), px_height_to_inches(100),
                                  fill_color=RGBColor(4, 15, 25),
                                  line_color=BLUE)
add_centered_text_box(slide9, px_to_inches_x(660), px_to_inches_y(255),
                      px_width_to_inches(600), Inches(0.3),
                      "User Request", Pt(14), BLUE)
add_centered_text_box(slide9, px_to_inches_x(660), px_to_inches_y(285),
                      px_width_to_inches(600), Inches(0.4),
                      "帮我编译最新固件，烧录到设备上，然后调试验证运行结果。", Pt(26), WHITE)

# Four subsystems
subsys_data = [
    ("01", "Bootstrap", "加载 AGENTS.md、SOUL.md、TOOLS.md 等 5~6 个核心上下文文件，注入 System Prompt。",
     "~85K chars\ncontext injection"),
    ("02", "Skills", "语义匹配命中 device-build-debug，自动读取 SKILL.md，获得 SSH → make → rsync → adb 的执行规范。",
     "device-build-debug\nSKILL.md loaded"),
    ("03", "Memory", "检索 MEMORY.md 和 memory/*.md，找到之前的编译参数、设备 IP、失败记录，避免重复踩坑。",
     "qmd search\nIP + make params"),
    ("04", "System Prompt", "把 Sandbox 规则、Execution Bias、Runtime 信息拼入 Prompt，驱动 LLM 生成正确的 exec 调用。",
     "safety + bias\n+ runtime line")
]

for i, (num, name, desc, code) in enumerate(subsys_data):
    sx = 80 + i * 440
    
    sys_box = create_rounded_rect(slide9, px_to_inches_x(sx), px_to_inches_y(380),
                                  px_width_to_inches(410), px_height_to_inches(380),
                                  fill_color=None, line_color=RGBColor(60, 60, 60))
    
    add_text_box(slide9, px_to_inches_x(sx + 28), px_to_inches_y(408), Inches(2), Inches(0.3),
                 num, Pt(16), GRAY_LIGHT)
    add_text_box(slide9, px_to_inches_x(sx + 28), px_to_inches_y(448), Inches(3.5), Inches(0.4),
                 name, Pt(24), WHITE, bold=True)
    add_text_box(slide9, px_to_inches_x(sx + 28), px_to_inches_y(500), Inches(3.5), Inches(1.2),
                 desc, Pt(17), GRAY)
    
    code_bg = create_rounded_rect(slide9, px_to_inches_x(sx + 28), px_to_inches_y(640),
                                  px_width_to_inches(370), Inches(0.8),
                                  fill_color=RGBColor(20, 20, 25),
                                  line_color=RGBColor(50, 50, 60))
    add_text_box(slide9, px_to_inches_x(sx + 48), px_to_inches_y(660), Inches(3.2), Inches(0.6),
                 code, Pt(14), RGBColor(193, 193, 198))

# Execution pipeline
pipeline_y = 800
pipe_steps = [
    ("🖥", "SSH Compile", "make -j8"),
    ("⚡", "rsync Flash", "push firmware"),
    ("🔍", "adb Debug", "logcat verify")
]

start_px = 560
for i, (icon, label, sub) in enumerate(pipe_steps):
    px = start_px + i * 300
    
    step_icon = create_rounded_rect(slide9, px_to_inches_x(px), px_to_inches_y(pipeline_y),
                                    px_width_to_inches(90), px_height_to_inches(90),
                                    fill_color=None, line_color=RGBColor(100, 100, 100))
    add_centered_text_box(slide9, px_to_inches_x(px), px_to_inches_y(pipeline_y + 25),
                          px_width_to_inches(90), Inches(0.5),
                          icon, Pt(28), WHITE)
    
    add_centered_text_box(slide9, px_to_inches_x(px - 20), px_to_inches_y(pipeline_y + 110),
                          px_width_to_inches(130), Inches(0.3),
                          label, Pt(16), RGBColor(209, 209, 214))
    add_centered_text_box(slide9, px_to_inches_x(px - 20), px_to_inches_y(pipeline_y + 140),
                          px_width_to_inches(130), Inches(0.25),
                          sub, Pt(13), RGBColor(110, 110, 115))
    
    if i < 2:
        add_text_box(slide9, px_to_inches_x(px + 100), px_to_inches_y(pipeline_y + 35),
                     Inches(0.4), Inches(0.4), "→", Pt(24), RGBColor(100, 100, 100))

# Bottom note
add_text_box(slide9, px_to_inches_x(80), px_to_inches_y(960), Inches(14), Inches(0.5),
             "这个案例说明：OpenClaw 不是简单地把 LLM 包装一层，而是用四个子系统把无状态模型变成了能跨网络、跨设备完成工程任务的 Agent。",
             Pt(20), GRAY)

# ==================== PAGE 10: Summary ====================
slide10 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg_color(slide10, BG_WHITE)

# Center content
words = ["Inject", "Assemble", "Extend", "Persist"]
start_y = 180
for i, word in enumerate(words):
    y = start_y + i * 130
    add_centered_text_box(slide10, Inches(0), px_to_inches_y(y),
                          SLIDE_WIDTH, Inches(1),
                          word, Pt(120), BLACK, bold=True)

# Line
line = create_rect(slide10, px_to_inches_x(900), px_to_inches_y(700),
                   px_width_to_inches(120), px_height_to_inches(3),
                   fill_color=BLACK, line_color=None)

# Subtitle
add_centered_text_box(slide10, Inches(0), px_to_inches_y(750),
                      SLIDE_WIDTH, Inches(0.5),
                      "Engineering, not magic.", Pt(28), RGBColor(110, 110, 115))

# Save the presentation
output_path = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-13-001-openclaw-ppt-design/OpenClaw_PPT_by_Lumi.pptx"
prs.save(output_path)

print(f"Presentation saved to: {output_path}")

# Verify file exists and get size
import os
if os.path.exists(output_path):
    size = os.path.getsize(output_path)
    print(f"File size: {size} bytes ({size / 1024:.1f} KB)")
else:
    print("ERROR: File was not created!")
