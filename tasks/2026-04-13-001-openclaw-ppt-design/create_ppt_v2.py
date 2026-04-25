#!/usr/bin/env python3
"""
OpenClaw Deep Dive Presentation Generator v2
Unified pixel coordinate system, zero text-frame margins, precise layout.
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ---------------------------------------------------------------------------
# Canvas & coordinate system: 1920 x 1080 px mapped to 13.333" x 7.5"
# ---------------------------------------------------------------------------
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
SCALE_X = 13.333 / 1920.0
SCALE_Y = 7.5 / 1080.0

def to_px(x): return Inches(x * SCALE_X)
def to_py(y): return Inches(y * SCALE_Y)

def to_pw(w): return Inches(w * SCALE_X)
def to_ph(h): return Inches(h * SCALE_Y)

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
C_BLACK   = RGBColor(0, 0, 0)
C_WHITE   = RGBColor(255, 255, 255)
C_GRAY1   = RGBColor(161, 161, 166)
C_GRAY2   = RGBColor(110, 110, 115)
C_GRAY3   = RGBColor(134, 134, 139)
C_BLUE    = RGBColor(41, 151, 255)
C_ORANGE  = RGBColor(255, 159, 10)
C_GREEN   = RGBColor(48, 209, 88)
C_PURPLE  = RGBColor(167, 139, 250)
C_BGWHITE = RGBColor(245, 245, 247)
C_DARKBG  = RGBColor(10, 10, 12)
C_DARKBG2 = RGBColor(20, 20, 25)
C_CODEFG  = RGBColor(193, 193, 198)
C_REDDOT  = RGBColor(255, 69, 58)
C_LINE    = RGBColor(68, 68, 68)
C_LBLUE   = RGBColor(96, 165, 250)
C_LPURPLE = RGBColor(192, 132, 252)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def set_slide_bg(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def zero_margins(tf):
    tf.margin_left   = Inches(0)
    tf.margin_right  = Inches(0)
    tf.margin_top    = Inches(0)
    tf.margin_bottom = Inches(0)

def add_text(slide, x, y, w, h, text, size, color=C_WHITE, bold=False, font="SF Pro Display", align=PP_ALIGN.LEFT):
    shape = slide.shapes.add_textbox(to_px(x), to_py(y), to_px(w), to_px(h))
    tf = shape.text_frame
    tf.word_wrap = True
    zero_margins(tf)
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font
    p.alignment = align
    return shape

def add_code_text(slide, x, y, w, h, text, size=14, color=C_CODEFG):
    return add_text(slide, x, y, w, h, text, size, color, font="SF Mono")

def rounded_rect(slide, x, y, w, h, fill=None, line=None, line_w=Pt(1)):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, to_px(x), to_py(y), to_px(w), to_px(h))
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = line
        shape.line.width = line_w
    else:
        shape.line.fill.background()
    return shape

def rect(slide, x, y, w, h, fill=None, line=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, to_px(x), to_py(y), to_px(w), to_px(h))
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape

def oval(slide, x, y, w, h, fill=None, line=None, line_w=Pt(1)):
    shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, to_px(x), to_py(y), to_px(w), to_px(h))
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = line
        shape.line.width = line_w
    else:
        shape.line.fill.background()
    return shape

def badge(slide, x, y, text):
    bw = len(text) * 14 + 56
    rounded_rect(slide, x, y, bw, 45, fill=None, line=C_GRAY2, line_w=Pt(0.5))
    add_text(slide, x, y + 10, bw, 25, text, 16, C_GRAY2, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------------------
# Build presentation
# ---------------------------------------------------------------------------
prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H

# ==================== PAGE 1: Cover ====================
s1 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s1, C_BLACK)
add_text(s1, 80, 340, 1100, 120, "OpenClaw 功能拆解", 110, C_WHITE)
add_text(s1, 84, 490, 1000, 60, "从 Prompt 工程到 Agent 上下文管理", 42, C_GRAY1)
badge(s1, 84, 620, "Engineering Deep Dive")
rounded_rect(s1, 1380, 260, 420, 560, fill=None, line=C_WHITE)
oval(s1, 1480, 360, 220, 220, fill=None, line=C_WHITE, line_w=Pt(0.5))
oval(s1, 1540, 420, 100, 100, fill=None, line=C_WHITE, line_w=Pt(0.5))
oval(s1, 1580, 460, 20, 20, fill=C_BLUE, line=None)

# ==================== PAGE 2: Overview ====================
s2 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s2, C_BLACK)
add_text(s2, 80, 70, 900, 90, "OpenClaw 解决什么问题？", 72, C_WHITE, bold=True)
add_text(s2, 80, 165, 1200, 45, "在 LLM 无状态的前提下，搭建一条可控制的能力链", 32, C_GRAY1)
rect(s2, 900, 500, 120, 4, fill=C_BLUE)
add_text(s2, 80, 320, 280, 30, "Stateless LLM", 22, C_GRAY2)

bubbles = [(0, 0, 280, 80, "每次请求都是独立的"), (320, 40, 260, 80, "没有长期记忆"), (80, 160, 300, 80, "不会主动调用工具")]
for bx, by, bw, bh, txt in bubbles:
    rounded_rect(s2, 80+bx, 370+by, bw, bh, fill=C_DARKBG, line=C_WHITE)
    add_text(s2, 80+bx+22, 370+by+22, bw-44, bh-44, txt, 18, RGBColor(209,209,214))

rect(s2, 140, 480, 460, 2, fill=C_ORANGE)
oval(s2, 134, 474, 12, 12, fill=C_REDDOT, line=None)
oval(s2, 588, 474, 12, 12, fill=C_GREEN, line=None)
rect(s2, 340, 470, 40, 14, fill=C_BLACK)
add_text(s2, 80, 610, 800, 40, "断裂的链条：对话、记忆、工具彼此隔离", 24, C_REDDOT)

add_text(s2, 1040, 320, 350, 30, "OpenClaw Framework", 22, C_GRAY2)
stages = [("Inject", "注入上下文"), ("Assemble", "拼装 Prompt"), ("Extend", "挂载 Skills"), ("Persist", "持久化记忆")]
for i, (name, desc) in enumerate(stages):
    sx = 1040 + i * 210
    rounded_rect(s2, sx, 360, 156, 156, fill=None, line=C_WHITE)
    add_text(s2, sx, 395, 156, 40, name, 26, C_WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(s2, sx, 445, 156, 30, desc, 14, C_GRAY1, align=PP_ALIGN.CENTER)
    if i < 3:
        add_text(s2, sx + 156 + 9, 430, 30, 30, "→", 22, C_WHITE, align=PP_ALIGN.CENTER)
add_text(s2, 1040, 550, 800, 40, "闭环：把无状态的 LLM 变成可控的 Agent 引擎", 24, C_BLUE)

# ==================== PAGE 3: Architecture ====================
s3 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s3, C_BLACK)
add_text(s3, 80, 60, 800, 80, "五层数据流", 56, C_WHITE, bold=True)
add_text(s3, 80, 135, 1000, 40, "从 Gateway 到 LLM，每一层都精确可控", 26, C_GRAY1)

stage_data = [
    ("01", "Gateway", "接收用户消息，通过 agentId + channel 路由到正确的 Agent 实例。", ["agentId: agent-radar-desk", "channel: webchat"]),
    ("02", "Session", "维护当前对话的 history.jsonl，记录用户消息、Assistant 回复、工具调用和自定义标记。", ["history.jsonl", "custom entry"]),
    ("03", "Bootstrap", "加载工作区上下文文件（AGENTS.md、SOUL.md 等），并决定注入策略（always / skip / lightweight）。", ["contextFiles[]", "contextInjection"]),
    ("04", "System Prompt", "把硬编码规则、项目上下文、动态环境拼成完整的 prompt string，供 LLM 消费。", ["buildAgentSystemPrompt()"]),
    ("05", "Runtime", "发起 LLM 请求，接收回复，解析结构化工具调用，在沙盒或宿主机上执行。", ["model: kimi/kimi-code", "tools: exec, read, write..."]),
]

for i, (num, name, desc, code) in enumerate(stage_data):
    sx = 80 + i * (320 + 40)
    rounded_rect(s3, sx, 280, 320, 550, fill=C_DARKBG, line=RGBColor(40,40,40))
    add_text(s3, sx + 24, 316, 100, 30, num, 18, C_GRAY2)
    add_text(s3, sx + 24, 352, 280, 50, name, 34, C_WHITE, bold=True)
    add_text(s3, sx + 24, 420, 280, 140, desc, 20, C_GRAY1)
    rounded_rect(s3, sx + 24, 580, 260, 120, fill=C_DARKBG2, line=RGBColor(50,50,60))
    add_code_text(s3, sx + 40, 598, 240, 100, "\n".join(code), 15)
    if i < 4:
        add_text(s3, sx + 320 + 8, 530, 40, 50, "→", 28, C_WHITE, align=PP_ALIGN.CENTER)

add_text(s3, 80, 940, 1500, 40, "OpenClaw 的价值不在某一层，而在把五层打通成一个可观测、可配置、可替换的管道。", 22, C_GRAY2)

# ==================== PAGE 4: Prompt Overview ====================
s4 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s4, C_BLACK)
add_text(s4, 80, 60, 800, 80, "Prompt 总览", 56, C_WHITE, bold=True)
add_text(s4, 80, 135, 800, 40, "System Prompt 由三部分拼成", 26, C_GRAY1)

layers = [
    (30, 64, 175, C_LBLUE, "~35%", "硬编码规则", "Tooling · Safety · Execution Bias · Cron 约束 · Skills · Memory · Self-Update · Sandbox"),
    (194, 65, 12, C_ORANGE, "~40%", "工作区上下文", "AGENTS.md · SOUL.md · TOOLS.md · IDENTITY.md · USER.md · MEMORY.md"),
    (126, 34, 206, C_LPURPLE, "~25%", "动态环境", "Workspace path · Runtime info · Model aliases · Channel capabilities · Thinking mode"),
]

for i, (r, g, b, pct_c, pct, name, items) in enumerate(layers):
    ly = 240 + i * 140
    fill_c = RGBColor(r//8, g//8, b//8)
    line_c = RGBColor(r, g, b)
    rounded_rect(s4, 80, ly, 1200, 120, fill=fill_c, line=line_c)
    add_text(s4, 120, ly + 28, 140, 60, pct, 52, pct_c, bold=True)
    add_text(s4, 280, ly + 24, 500, 45, name, 28, C_WHITE, bold=True)
    add_text(s4, 280, ly + 68, 900, 45, items, 20, C_WHITE)

rounded_rect(s4, 1340, 240, 500, 600, fill=None, line=RGBColor(60,60,60))
add_text(s4, 1376, 276, 400, 30, "ASSEMBLY PROCESS", 22, C_GRAY2)
add_code_text(s4, 1376, 320, 400, 30, "buildAgentSystemPrompt()", 18)
steps = [("1","收集 workspace md 文件并做截断/过滤"),("2","注入框架级硬编码 section"),("3","拼接 Skills XML 与 Memory prompt"),("4","追加 Runtime line 和动态环境")]
for i, (num, txt) in enumerate(steps):
    sy = 380 + i * 100
    oval(s4, 1376, sy, 32, 32, fill=RGBColor(60,60,60), line=None)
    add_text(s4, 1376, sy + 4, 32, 28, num, 14, C_WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(s4, 1420, sy + 2, 400, 60, txt, 18, RGBColor(209,209,214))

add_text(s4, 80, 960, 1500, 40, "提示词工程的本质不是写更好的 prompt，而是建立一个稳定、可重复、可扩展的拼装管道。", 22, C_GRAY2)

# ==================== PAGE 5: Inject & Assemble ====================
s5 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s5, C_BLACK)
add_text(s5, 80, 60, 1000, 70, "注入与拼装", 56, C_WHITE, bold=True)
add_text(s5, 80, 135, 1200, 40, "以一句「你是谁？」为例，看 OpenClaw 注入了多少 Prompt", 26, C_GRAY1)

for i in range(6):
    oval(s5, 80 + i * 24, 210, 14, 14, fill=C_BLUE, line=None)

add_text(s5, 0, 310, 140, 25, "User Query", 14, C_BLUE)
rounded_rect(s5, 0, 340, 240, 80, fill=RGBColor(10,20,35), line=C_BLUE)
add_text(s5, 36, 360, 200, 40, "你是谁？", 28, C_WHITE)

rect(s5, 240, 375, 120, 2, fill=RGBColor(80,80,80))
add_text(s5, 348, 366, 20, 20, "▸", 12, RGBColor(80,80,80), align=PP_ALIGN.CENTER)

rounded_rect(s5, 360, 300, 220, 120, fill=None, line=C_GRAY2)
add_text(s5, 360, 325, 220, 30, "Gateway / Session", 18, C_WHITE, bold=True, align=PP_ALIGN.CENTER)
add_text(s5, 360, 360, 220, 25, "check bootstrap status", 13, C_GRAY2, align=PP_ALIGN.CENTER)

rounded_rect(s5, 360, 440, 420, 100, fill=C_DARKBG2, line=RGBColor(50,50,60))
add_code_text(s5, 378, 458, 400, 80,
              "hasCompletedBootstrapTurn(sessionFile)\n{ maxTailBytes: 256000, maxTailRecords: 500 }", 13)

rect(s5, 580, 355, 40, 2, fill=RGBColor(80,80,80))
add_text(s5, 610, 346, 20, 20, "▸", 12, RGBColor(80,80,80), align=PP_ALIGN.CENTER)

add_text(s5, 620, 280, 300, 25, "Workspace Context Files", 14, C_GRAY1)
file_items = [
    ("AGENTS.md", "~2.4k"), ("SOUL.md", "~1.1k"), ("TOOLS.md", "~3.8k"),
    ("IDENTITY.md", "~0.6k"), ("USER.md", "~0.4k"), ("MEMORY.md", "~5.2k")
]
for i, (fname, fsize) in enumerate(file_items):
    fy = 320 + i * 32
    rect(s5, 620, fy + 8, 8, 8, fill=C_ORANGE)
    add_code_text(s5, 640, fy, 140, 25, fname, 16)
    add_text(s5, 790, fy, 80, 25, fsize, 13, C_GRAY2, align=PP_ALIGN.RIGHT)

rect(s5, 960, 355, 60, 2, fill=RGBColor(80,80,80))
add_text(s5, 1008, 346, 20, 20, "▸", 12, RGBColor(80,80,80), align=PP_ALIGN.CENTER)

add_text(s5, 1020, 280, 400, 25, "buildAgentSystemPrompt()", 14, C_GRAY1)
layer_info = [
    ("硬编码规则 · ~30%", "Tooling · Safety · Execution Bias · Skills · Memory · Cron", RGBColor(8,16,35), RGBColor(48,99,209)),
    ("项目上下文 · ~45%", "AGENTS / SOUL / TOOLS / IDENTITY / USER / MEMORY.md", RGBColor(32,10,2), RGBColor(194,65,12)),
    ("动态环境 · ~25%", "Runtime · Workspace path · Model alias · Sandbox info", RGBColor(21,5,34), RGBColor(126,34,206)),
]
for i, (title, desc, fill_c, line_c) in enumerate(layer_info):
    ly = 320 + i * 110
    rounded_rect(s5, 1020, ly, 460, 90, fill=fill_c, line=line_c)
    add_text(s5, 1040, ly + 14, 440, 28, title, 17, C_WHITE, bold=True)
    add_text(s5, 1040, ly + 48, 440, 36, desc, 14, RGBColor(200,200,200))

rounded_rect(s5, 1020, 750, 460, 110, fill=None, line=RGBColor(60,60,60))
stats = [("System Prompt 总字符数", "~85,000 chars"), ("单用户 query 长度", "4 chars"), ("上下文膨胀倍数", "~21,250×")]
for i, (lab, val) in enumerate(stats):
    sy = 770 + i * 30
    add_text(s5, 1044, sy, 260, 25, lab, 16, C_GRAY1)
    add_code_text(s5, 1320, sy, 140, 25, val, 16)

rect(s5, 1480, 395, 60, 2, fill=RGBColor(80,80,80))
add_text(s5, 1528, 386, 20, 20, "▸", 12, RGBColor(80,80,80), align=PP_ALIGN.CENTER)

rounded_rect(s5, 1540, 360, 260, 180, fill=None, line=C_WHITE)
add_text(s5, 1540, 410, 260, 40, "LLM", 32, C_WHITE, bold=True, align=PP_ALIGN.CENTER)
add_text(s5, 1540, 460, 260, 50, "System Prompt + User Query\n→ Generate response", 15, C_GRAY1, align=PP_ALIGN.CENTER)
add_text(s5, 80, 940, 1640, 40,
         "核心洞察：你的 4 个字触发了 ~85K 字符的系统上下文注入与拼装，这是 OpenClaw 把无状态 LLM 变成可控 Agent 的关键机制。", 18, C_GRAY2)

# ==================== PAGE 6: Skills ====================
s6 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s6, C_BLACK)
add_text(s6, 80, 60, 1000, 70, "Skills — 可插拔的能力包", 56, C_WHITE, bold=True)
add_text(s6, 80, 135, 1200, 40, "不是写在代码里，而是写在声明文件与规范文档里的外部能力", 26, C_GRAY1)

rounded_rect(s6, 80, 220, 520, 200, fill=None, line=RGBColor(60,60,60))
add_text(s6, 112, 248, 400, 30, "What is a Skill?", 18, C_GRAY2)
add_text(s6, 112, 290, 470, 100,
         "一个 Skill 由 _manifest.yaml 注册，由 SKILL.md 定义执行规范。Agent 匹配到 Skill 后，必须 Read → Follow → Execute。", 22, C_WHITE)

add_text(s6, 80, 460, 300, 25, "Skill 触发 workflow", 14, C_GRAY2)
wf = ["匹配 skill", "read SKILL.md", "严格执行"]
for i, step in enumerate(wf):
    sx = 80 + i * 220
    hl = (i == 1)
    rounded_rect(s6, sx, 500, 180, 70, fill=RGBColor(10,25,40) if hl else None,
                 line=C_BLUE if hl else RGBColor(100,100,100))
    add_text(s6, sx, 520, 180, 30, step, 18, C_WHITE, align=PP_ALIGN.CENTER)
    if i < 2:
        add_text(s6, sx + 180 + 10, 520, 30, 30, "→", 22, RGBColor(100,100,100), align=PP_ALIGN.CENTER)

add_text(s6, 680, 220, 400, 25, "OpenClaw 内置 Skill 示例", 14, C_GRAY2)
skills = [
    ("device-build-debug", "SSH 编译、rsync 烧录、adb 调试完整链路", "hardware", True),
    ("weather", "调用 wttr.in / Open-Meteo 获取天气与预报", "api", False),
    ("github", "基于 gh CLI 的 Issue / PR / CI 操作", "cli", False),
    ("docx", "生成、编辑、重组 Word 文档", "document", False),
    ("pptx", "生成 PowerPoint 幻灯片与演讲稿", "document", False),
]
for i, (name, desc, tag, hl) in enumerate(skills):
    cx = 680 + i * 230
    rounded_rect(s6, cx, 260, 210, 220, fill=RGBColor(40,25,5) if hl else None,
                 line=C_ORANGE if hl else RGBColor(60,60,60))
    add_text(s6, cx + 22, 282, 180, 35, name, 20, C_WHITE, bold=True)
    add_text(s6, cx + 22, 330, 180, 90, desc, 15, C_GRAY1)
    add_text(s6, cx + 22, 440, 180, 25, tag, 12, C_GRAY2, font="SF Mono")

add_text(s6, 80, 660, 300, 25, "来源优先级（高 → 低）", 14, C_GRAY2)
pyramid = [
    (180, "workspace/skills（项目级，可覆盖内置）", True),
    (240, "workspace/.agents/skills", False),
    (300, "~/.agents/skills", False),
    (360, "~/.openclaw/skills", False),
    (420, "OpenClaw bundled", False),
    (480, "extraDirs / 外部目录", False),
]
for i, (width, txt, top) in enumerate(pyramid):
    pos_y = 700 + i * 38
    pos_x = 80 + (480 - width) // 2
    rounded_rect(s6, pos_x, pos_y, width, 34,
                 fill=RGBColor(40,25,5) if top else C_DARKBG,
                 line=C_ORANGE if top else RGBColor(60,60,60))
    add_text(s6, pos_x, pos_y + 6, width, 25, txt, 14, C_ORANGE if top else C_WHITE, align=PP_ALIGN.CENTER)

rounded_rect(s6, 680, 520, 520, 140, fill=RGBColor(5,25,10), line=C_GREEN)
add_text(s6, 704, 540, 400, 25, "性能优化：skillsSnapshot", 14, C_GRAY2)
add_text(s6, 704, 580, 480, 70,
         "父 Agent 通过 sessions_spawn 将 skillsSnapshot 直接传递给子 Agent，跳过磁盘扫描。一次解析，多次复用。", 16, RGBColor(209,209,214))
add_text(s6, 80, 980, 1500, 40,
         "OpenClaw 的 Skills 本质上是「把外部能力声明化」，让框架不用改核心代码就能持续扩展功能边界。", 18, C_GRAY2)

# ==================== PAGE 7: Memory ====================
s7 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s7, C_BLACK)
add_text(s7, 80, 60, 1200, 70, "Memory — 可替换的记忆后端", 56, C_WHITE, bold=True)
add_text(s7, 80, 135, 1200, 40, "不是把记忆写死在框架里，而是一个可插拔的 Plugin Slot", 26, C_GRAY1)

x1 = 80
rounded_rect(s7, x1, 240, 340, 400, fill=None, line=RGBColor(60,60,60))
add_text(s7, x1 + 28, 268, 300, 30, "1. 落盘 Files", 20, C_WHITE, bold=True)
files1 = [("MEMORY.md", "项目级主记忆"), ("memory/*.md", "按日期/主题拆分"), ("sessionFiles", "可选对话记录")]
for i, (fn, fm) in enumerate(files1):
    pos_y = 320 + i * 40
    oval(s7, x1 + 28, pos_y + 8, 6, 6, fill=C_PURPLE)
    add_code_text(s7, x1 + 50, pos_y, 140, 25, fn, 15)
    add_text(s7, x1 + 240, pos_y, 120, 25, fm, 12, C_GRAY2, align=PP_ALIGN.RIGHT)
rect(s7, x1 + 340, 420, 40, 2, fill=RGBColor(80,80,80))
add_text(s7, x1 + 360, 411, 20, 20, "▸", 12, RGBColor(80,80,80), align=PP_ALIGN.CENTER)

x2 = 460
rounded_rect(s7, x2, 240, 380, 400, fill=None, line=RGBColor(60,60,60))
add_text(s7, x2 + 28, 268, 300, 30, "2. 分块 Chunk + Hash", 20, C_WHITE, bold=True)
for row in range(3):
    for col in range(4):
        cx = x2 + 28 + col * 52
        cy = 320 + row * 52
        rounded_rect(s7, cx, cy, 44, 44, fill=RGBColor(25,20,30), line=C_PURPLE)
        add_text(s7, cx, cy + 10, 44, 24, f"C{row*4+col+1}", 10, C_PURPLE, align=PP_ALIGN.CENTER)
add_text(s7, x2 + 28, 500, 340, 30, "每个 chunk 生成 SHA256 用于增量同步", 14, C_GRAY2)
rect(s7, x2 + 380, 420, 40, 2, fill=RGBColor(80,80,80))
add_text(s7, x2 + 400, 411, 20, 20, "▸", 12, RGBColor(80,80,80), align=PP_ALIGN.CENTER)

x3 = 880
rounded_rect(s7, x3, 240, 420, 400, fill=None, line=RGBColor(60,60,60))
add_text(s7, x3 + 28, 268, 380, 30, "3. 向量检索 Vector Search", 20, C_WHITE, bold=True)
oval(s7, x3 + 150, 340, 120, 120, fill=None, line=C_WHITE)
oval(s7, x3 + 186, 376, 48, 48, fill=C_PURPLE, line=None)
add_text(s7, x3 + 28, 500, 420, 60, "回答前 必须先 search\nMEMORY.md + memory/*.md", 18, RGBColor(209,209,214), align=PP_ALIGN.CENTER)
rounded_rect(s7, x3 + 80, 580, 120, 32, fill=RGBColor(5,25,10), line=C_GREEN)
add_text(s7, x3 + 80, 586, 120, 25, "builtin 向量索引", 14, C_GREEN, align=PP_ALIGN.CENTER)
rounded_rect(s7, x3 + 220, 580, 100, 32, fill=RGBColor(5,15,25), line=C_BLUE)
add_text(s7, x3 + 220, 586, 100, 25, "qmd 外部后端", 14, C_BLUE, align=PP_ALIGN.CENTER)
rect(s7, x3 + 420, 420, 40, 2, fill=RGBColor(80,80,80))
add_text(s7, x3 + 440, 411, 20, 20, "▸", 12, RGBColor(80,80,80), align=PP_ALIGN.CENTER)

x4 = 1340
rounded_rect(s7, x4, 240, 460, 400, fill=None, line=RGBColor(60,60,60))
add_text(s7, x4 + 28, 268, 400, 30, "4. 注入 Prompt 规则", 20, C_WHITE, bold=True)
rounded_rect(s7, x4 + 28, 320, 420, 200, fill=C_DARKBG2, line=RGBColor(50,50,60))
add_code_text(s7, x4 + 48, 340, 400, 180,
              "## Memory\nMandatory recall step:\nsemantically search MEMORY.md\n+ memory/*.md before answering.", 15)

add_code_text(s7, 80, 680, 800, 30, "registerMemoryCapability(pluginId, capability)", 18)
rounded_rect(s7, 80, 720, 220, 90, fill=RGBColor(20,15,25), line=C_PURPLE)
add_text(s7, 80, 738, 220, 30, "Memory Plugin", 18, C_PURPLE, bold=True, align=PP_ALIGN.CENTER)
add_text(s7, 80, 770, 220, 25, "promptBuilder + runtime", 13, C_GRAY2, align=PP_ALIGN.CENTER)
rect(s7, 300, 762, 120, 2, fill=RGBColor(80,80,80))
add_text(s7, 400, 753, 20, 20, "▸", 12, RGBColor(80,80,80), align=PP_ALIGN.CENTER)
rounded_rect(s7, 440, 720, 220, 90, fill=None, line=RGBColor(60,60,60))
add_text(s7, 440, 738, 220, 30, "OpenClaw Core", 18, C_WHITE, bold=True, align=PP_ALIGN.CENTER)
add_text(s7, 440, 770, 220, 25, "不硬编码，只预留 slot", 13, C_GRAY2, align=PP_ALIGN.CENTER)

rounded_rect(s7, 840, 720, 840, 140, fill=None, line=RGBColor(60,60,60))
add_text(s7, 872, 738, 200, 30, "设计意图", 18, C_GRAY2)
add_text(s7, 872, 778, 780, 70,
         "Memory 对 OpenClaw 框架来说是 透明的 —— 框架只负责调用 Plugin 注册的 builder，把结果拼接进 System Prompt。你可以随时替换内置实现，接入自己的向量数据库或企业知识库。", 22, C_WHITE)

# ==================== PAGE 8: Optimizations ====================
s8 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s8, C_BLACK)
add_text(s8, 80, 60, 1000, 70, "效率与主动性", 56, C_WHITE, bold=True)
add_text(s8, 80, 135, 1200, 40, "框架在后台默默做的三件事，用户几乎无感知", 26, C_GRAY1)

cards = [
    ("≋", "Auto-Compaction", "当对话接近 token 上限时，自动调用 LLM 把 80 轮对话压缩成 3 条核心摘要，腾出上下文预算。", "80 → 3", "轮次压缩比例", C_ORANGE, RGBColor(40,25,5)),
    ("⚡", "Snapshot", "父 Agent 直接通过 skillsSnapshot 把已解析的 Skill 上下文传递给子 Agent，跳过重复磁盘扫描。", "秒启动", "子代理初始化时间", C_BLUE, RGBColor(5,15,25)),
    ("⟳", "Heartbeat", "每 30 分钟自动触发一次 LLM 巡检，读取 HEARTBEAT.md 检查系统状态、队列积压与未完成动作。", "30 min", "默认巡检间隔", C_GREEN, RGBColor(5,25,10)),
]
card_w = 560
gap = 40
start_x = 80
for i, (icon, title, desc, metric, mlabel, color, fill) in enumerate(cards):
    cx = start_x + i * (card_w + gap)
    rounded_rect(s8, cx, 280, card_w, 540, fill=None, line=RGBColor(40,40,40))
    rounded_rect(s8, cx + 50, 330, 80, 80, fill=fill, line=color)
    add_text(s8, cx + 50, 355, 80, 40, icon, 32, color, bold=True, align=PP_ALIGN.CENTER)
    add_text(s8, cx + 50, 430, 460, 45, title, 38, C_WHITE, bold=True)
    add_text(s8, cx + 50, 490, 460, 140, desc, 22, C_GRAY1)
    rect(s8, cx + 50, 660, 460, 2, fill=RGBColor(40,40,40))
    add_text(s8, cx + 50, 685, 460, 55, metric, 48, C_WHITE, bold=True)
    add_text(s8, cx + 50, 750, 460, 30, mlabel, 16, C_GRAY2)

add_text(s8, 80, 940, 1500, 40,
         "这三项优化的共同目标：让框架在大规模、长对话、多子代理场景下保持高效与稳定。", 24, C_GRAY2)

# ==================== PAGE 9: P100 Case ====================
s9 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s9, C_BLACK)
add_text(s9, 80, 60, 1200, 70, "P100-recordpen 编译 + 烧录 + 调试", 52, C_WHITE, bold=True)
add_text(s9, 80, 130, 1200, 40, "一个真实请求如何同时激活四个子系统", 24, C_GRAY1)

rounded_rect(s9, 660, 240, 600, 100, fill=RGBColor(5,15,25), line=C_BLUE)
add_text(s9, 660, 255, 600, 30, "User Request", 14, C_BLUE, align=PP_ALIGN.CENTER)
add_text(s9, 660, 285, 600, 40, "帮我编译最新固件，烧录到设备上，然后调试验证运行结果。", 26, C_WHITE, align=PP_ALIGN.CENTER)

subsys = [
    ("01", "Bootstrap", "加载 AGENTS.md、SOUL.md、TOOLS.md 等 5~6 个核心上下文文件，注入 System Prompt。", "~85K chars\ncontext injection"),
    ("02", "Skills", "语义匹配命中 device-build-debug，自动读取 SKILL.md，获得 SSH → make → rsync → adb 的执行规范。", "device-build-debug\nSKILL.md loaded"),
    ("03", "Memory", "检索 MEMORY.md 和 memory/*.md，找到之前的编译参数、设备 IP、失败记录，避免重复踩坑。", "qmd search\nIP + make params"),
    ("04", "System Prompt", "把 Sandbox 规则、Execution Bias、Runtime 信息拼入 Prompt，驱动 LLM 生成正确的 exec 调用。", "safety + bias\n+ runtime line"),
]
for i, (num, name, desc, code) in enumerate(subsys):
    sx = 80 + i * 440
    rounded_rect(s9, sx, 380, 410, 380, fill=None, line=RGBColor(60,60,60))
    add_text(s9, sx + 28, 408, 100, 30, num, 16, C_GRAY2)
    add_text(s9, sx + 28, 448, 370, 40, name, 24, C_WHITE, bold=True)
    add_text(s9, sx + 28, 500, 370, 120, desc, 17, C_GRAY1)
    rounded_rect(s9, sx + 28, 640, 370, 80, fill=C_DARKBG2, line=RGBColor(50,50,60))
    add_code_text(s9, sx + 48, 660, 350, 60, code, 14)

pipe = [("🖥", "SSH Compile", "make -j8"), ("⚡", "rsync Flash", "push firmware"), ("🔍", "adb Debug", "logcat verify")]
pipe_start = 560
for i, (icon, label, sub) in enumerate(pipe):
    p_x = pipe_start + i * 300
    rounded_rect(s9, p_x, 800, 90, 90, fill=None, line=RGBColor(100,100,100))
    add_text(s9, p_x, 825, 90, 40, icon, 28, C_WHITE, align=PP_ALIGN.CENTER)
    add_text(s9, p_x - 20, 910, 130, 30, label, 16, RGBColor(209,209,214), align=PP_ALIGN.CENTER)
    add_text(s9, p_x - 20, 940, 130, 25, sub, 13, C_GRAY2, align=PP_ALIGN.CENTER)
    if i < 2:
        add_text(s9, p_x + 100, 835, 40, 40, "→", 24, RGBColor(100,100,100), align=PP_ALIGN.CENTER)

add_text(s9, 80, 960, 1640, 40,
         "这个案例说明：OpenClaw 不是简单地把 LLM 包装一层，而是用四个子系统把无状态模型变成了能跨网络、跨设备完成工程任务的 Agent。", 20, C_GRAY2)

# ==================== PAGE 10: Summary ====================
s10 = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(s10, C_BGWHITE)

words = ["Inject", "Assemble", "Extend", "Persist"]
for i, word in enumerate(words):
    pos_y = 160 + i * 130
    add_text(s10, 0, pos_y, 1920, 100, word, 120, C_BLACK, bold=True, align=PP_ALIGN.CENTER)

rect(s10, 900, 700, 120, 3, fill=C_BLACK)
add_text(s10, 0, 750, 1920, 50, "Engineering, not magic.", 28, C_GRAY2, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
output = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-13-001-openclaw-ppt-design/OpenClaw_PPT_v2.pptx"
prs.save(output)
print(f"Saved: {output}")

import os
print(f"Size: {os.path.getsize(output) / 1024:.1f} KB")
