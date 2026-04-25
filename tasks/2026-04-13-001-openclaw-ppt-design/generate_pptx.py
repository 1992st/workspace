from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

def add_textbox(slide, left, top, width, height, text, font_size, font_color, bold=False, font_name="SF Pro Display"):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = font_color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = PP_ALIGN.LEFT


def add_code_block(slide, left, top, width, height, text, font_size=14):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(20, 20, 25)
    box.line.color.rgb = RGBColor(50, 50, 60)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = RGBColor(200, 200, 210)
    p.font.name = "SF Mono"
    p.alignment = PP_ALIGN.LEFT


# Page 1: Cover
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0, 0, 0)
add_textbox(slide, 1.5, 2.2, 10, 1.5, "OpenClaw 功能拆解", 72, RGBColor(255,255,255))
add_textbox(slide, 1.5, 3.5, 10, 0.8, "从 Prompt 工程到 Agent 上下文管理", 32, RGBColor(161,161,166))
add_textbox(slide, 5.2, 6.5, 3, 0.5, "Engineering Deep Dive", 16, RGBColor(110,110,115))

# Page 2: Overview
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.8, 0.6, 10, 1, "OpenClaw 解决什么问题？", 52, RGBColor(255,255,255))
add_textbox(slide, 0.8, 1.4, 12, 0.6, "在 LLM 无状态的前提下，搭建一条可控制的能力链", 24, RGBColor(161,161,166))
add_textbox(slide, 1.0, 3.0, 4, 2, "LLM Stateless\n（请导入 02-overview 截图）", 20, RGBColor(136,136,136))
add_textbox(slide, 5.0, 4.0, 3.5, 0.5, "OpenClaw Framework", 20, RGBColor(96,165,250))
add_textbox(slide, 9.0, 3.0, 4, 2.5, "Inject → Assemble → Extend → Persist\n（请导入 02-overview 截图）", 22, RGBColor(200,200,200))

# Page 3: Architecture
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.8, 0.6, 12, 1, "五层数据流", 52, RGBColor(255,255,255))
steps = [
    ("1. Gateway", "agentId + sessionKey"),
    ("2. Session", "history.jsonl"),
    ("3. Bootstrap", "contextFiles[]"),
    ("4. System Prompt", "prompt string"),
    ("5. Runtime", "LLM request"),
]
x = 0.6
for title, subtitle in steps:
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(2.8), Inches(2.2), Inches(1.6))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(10,10,12)
    shape.line.color.rgb = RGBColor(68,68,68)
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(22)
    p.font.color.rgb = RGBColor(255,255,255)
    p.font.bold = True
    p2 = tf.add_paragraph()
    p2.text = subtitle
    p2.font.size = Pt(14)
    p2.font.color.rgb = RGBColor(136,136,136)
    p2.font.name = "SF Mono"
    x += 2.5

# Page 4: Prompt Overview
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.8, 0.5, 12, 1, "Prompt 总览", 48, RGBColor(255,255,255))
add_textbox(slide, 0.8, 1.2, 12, 0.5, "System Prompt 由三部分拼成", 22, RGBColor(161,161,166))
add_textbox(slide, 0.8, 2.5, 3.8, 3.5, "硬编码规则 ~35%\nSafety\nExecution Bias\nCron\nCLI", 20, RGBColor(200,200,255))
add_textbox(slide, 4.8, 2.5, 3.8, 3.5, "工作区上下文 ~40%\nAGENTS.md\nSOUL.md\nTOOLS.md\nMEMORY.md", 20, RGBColor(255,200,170))
add_textbox(slide, 8.8, 2.5, 3.8, 3.5, "动态环境 ~25%\nWorkspace\nRuntime\nSandbox", 20, RGBColor(220,180,255))
add_textbox(slide, 5.5, 6.2, 3, 0.4, "buildAgentSystemPrompt()", 16, RGBColor(136,136,136))
add_textbox(slide, 6.0, 6.7, 1.5, 0.4, "LLM", 20, RGBColor(255,255,255))

# Page 5: Inject & Assemble
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.6, 0.4, 10, 1, "注入与拼装", 44, RGBColor(255,255,255))
add_textbox(slide, 0.6, 1.0, 12, 0.5, "以一句「你是谁？」为例，看 OpenClaw 注入了多少 Prompt", 20, RGBColor(161,161,166))
add_code_block(slide, 0.6, 1.8, 6.5, 1.2, "customType: openclaw:bootstrap-context:full -> Skip\ntype: message (assistant)\ntype: compaction -> Re-inject", 16)
add_textbox(slide, 0.6, 3.1, 4, 0.3, "hasCompletedBootstrapTurn()", 14, RGBColor(102,102,102))
layer_colors = [RGBColor(30,64,175), RGBColor(194,65,12), RGBColor(126,34,206)]
layer_texts = ["硬编码规则\nSafety / Execution Bias", "Project Context\nAGENTS.md / SOUL.md / MEMORY.md", "动态环境\nWorkspace / Runtime"]
x = 0.6
for color, text in zip(layer_colors, layer_texts):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(4.0), Inches(3.8), Inches(1.8))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.color.rgb = color
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(18)
    p.font.color.rgb = RGBColor(255,255,255)
    x += 4.1
add_textbox(slide, 12.5, 4.7, 1, 0.5, "LLM", 22, RGBColor(255,255,255))
add_textbox(slide, 0.6, 6.6, 10, 0.5, "核心洞察：你的 4 个字触发了 ~85K 字符的系统上下文注入与拼装。", 18, RGBColor(110,110,115))

# Page 6: Skills
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.6, 0.4, 10, 1, "Skills — 可插拔的能力包", 46, RGBColor(255,255,255))
add_textbox(slide, 0.6, 1.1, 12, 0.4, "匹配 skill -> 必须 read SKILL.md -> 严格执行", 20, RGBColor(161,161,166))
add_textbox(slide, 0.6, 2.0, 3, 3, "docx\nweather\ngithub\ndevice-build-debug（高亮）\npptx", 18, RGBColor(221,221,221))
add_textbox(slide, 4.0, 2.5, 3, 2, "SKILL.md\n1. SSH login remote\n2. Compile via make\n3. rsync firmware\n4. adb push & verify", 16, RGBColor(245,158,11))
add_textbox(slide, 7.5, 2.8, 4, 0.8, "Read  ->  Follow  ->  Execute", 20, RGBColor(255,255,255))
add_textbox(slide, 10.5, 2.0, 2.5, 1, "skillsSnapshot\n父传子\n跳过扫描", 14, RGBColor(96,165,250))
add_textbox(slide, 10.0, 5.0, 3, 1.5, "6 级来源优先级\nworkspace/skills（最高）", 16, RGBColor(245,158,11))

# Page 7: Memory
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.6, 0.4, 10, 1, "Memory — 可替换的记忆后端", 46, RGBColor(255,255,255))
add_textbox(slide, 0.6, 1.1, 10, 0.4, "registerMemoryCapability()", 20, RGBColor(161,161,166))
shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.6), Inches(3.0), Inches(3.0), Inches(2.2))
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(15,10,20)
shape.line.color.rgb = RGBColor(167,139,250)
tf = shape.text_frame
p = tf.paragraphs[0]
p.text = "Memory Plugin Slot"
p.font.size = Pt(22)
p.font.color.rgb = RGBColor(167,139,250)
add_textbox(slide, 4.2, 2.6, 1.8, 1, "落盘\nFiles", 18, RGBColor(96,165,250))
add_textbox(slide, 5.8, 3.8, 2.2, 0.8, "分块\nchunk · hash", 18, RGBColor(245,158,11))
add_textbox(slide, 4.2, 5.0, 1.8, 1, "检索\nVector DB", 18, RGBColor(167,139,250))
add_textbox(slide, 9.5, 3.5, 2.5, 1.5, "(  search  )\n大眼睛示意", 18, RGBColor(255,255,255))
add_textbox(slide, 5.0, 6.5, 1.8, 0.4, "builtin 向量索引", 16, RGBColor(96,165,250))
add_textbox(slide, 7.2, 6.5, 1.5, 0.4, "qmd 外部后端", 16, RGBColor(167,139,250))

# Page 8: Optimizations
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.8, 0.5, 12, 1, "效率与主动性", 48, RGBColor(255,255,255))
add_textbox(slide, 0.8, 1.2, 12, 0.5, "框架在后台默默做的三件事", 22, RGBColor(161,161,166))
add_textbox(slide, 5.8, 2.2, 2.5, 1.2, "Auto-Compaction\n80 轮 -> 3 条 summary", 20, RGBColor(245,158,11))
add_textbox(slide, 2.2, 5.0, 2.2, 1.0, "Snapshot\n子代理秒启动", 20, RGBColor(96,165,250))
add_textbox(slide, 9.0, 5.0, 2.2, 1.0, "Heartbeat\n30 分钟自动巡检", 20, RGBColor(52,211,153))
add_textbox(slide, 5.8, 4.3, 2.5, 0.5, "Invisible to user", 16, RGBColor(85,85,85))

# Page 9: Agent Talk
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.5, 0.4, 10, 0.9, "Agent 杂谈 — 下一代趋势", 38, RGBColor(255,255,255))
add_textbox(slide, 0.5, 1.1, 10, 0.4, "从 Claude Code 泄露源码看 Agent 进化方向", 18, RGBColor(161,161,166))

# BUDDY
card1 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(2.0), Inches(2.8), Inches(2.0))
card1.fill.solid()
card1.fill.fore_color.rgb = RGBColor(30,20,10)
card1.line.color.rgb = RGBColor(245,158,11)
tf1 = card1.text_frame
tf1.word_wrap = True
p1 = tf1.paragraphs[0]
p1.text = "🐣 BUDDY"
p1.font.size = Pt(16)
p1.font.color.rgb = RGBColor(245,158,11)
p1.font.bold = True
p1b = tf1.add_paragraph()
p1b.text = "终端电子宠物\n骨骼-灵魂双架构"
p1b.font.size = Pt(12)
p1b.font.color.rgb = RGBColor(180,180,180)

# Dream System
card2 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.6), Inches(2.0), Inches(2.8), Inches(2.0))
card2.fill.solid()
card2.fill.fore_color.rgb = RGBColor(10,20,30)
card2.line.color.rgb = RGBColor(96,165,250)
tf2 = card2.text_frame
tf2.word_wrap = True
p2 = tf2.paragraphs[0]
p2.text = "💤 Dream System"
p2.font.size = Pt(16)
p2.font.color.rgb = RGBColor(96,165,250)
p2.font.bold = True
p2b = tf2.add_paragraph()
p2b.text = "自动记忆整理\n三层渐进压缩"
p2b.font.size = Pt(12)
p2b.font.color.rgb = RGBColor(180,180,180)

# KAIROS
card3 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.7), Inches(2.0), Inches(2.8), Inches(2.0))
card3.fill.solid()
card3.fill.fore_color.rgb = RGBColor(20,15,30)
card3.line.color.rgb = RGBColor(167,139,250)
tf3 = card3.text_frame
tf3.word_wrap = True
p3 = tf3.paragraphs[0]
p3.text = "⚡ KAIROS"
p3.font.size = Pt(16)
p3.font.color.rgb = RGBColor(167,139,250)
p3.font.bold = True
p3b = tf3.add_paragraph()
p3b.text = "主动式助手\nAlways-On 感知"
p3b.font.size = Pt(12)
p3b.font.color.rgb = RGBColor(180,180,180)

# Swarm
card4 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.8), Inches(2.0), Inches(2.8), Inches(2.0))
card4.fill.solid()
card4.fill.fore_color.rgb = RGBColor(10,25,20)
card4.line.color.rgb = RGBColor(52,211,153)
tf4 = card4.text_frame
tf4.word_wrap = True
p4 = tf4.paragraphs[0]
p4.text = "🐝 Swarm"
p4.font.size = Pt(16)
p4.font.color.rgb = RGBColor(52,211,153)
p4.font.bold = True
p4b = tf4.add_paragraph()
p4b.text = "多智能体协调\n原生并发架构"
p4b.font.size = Pt(12)
p4b.font.color.rgb = RGBColor(180,180,180)

# TeamMemory
card5 = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(4.4), Inches(2.8), Inches(1.8))
card5.fill.solid()
card5.fill.fore_color.rgb = RGBColor(30,15,25)
card5.line.color.rgb = RGBColor(236,72,153)
tf5 = card5.text_frame
tf5.word_wrap = True
p5 = tf5.paragraphs[0]
p5.text = "👥 TeamMemory"
p5.font.size = Pt(16)
p5.font.color.rgb = RGBColor(236,72,153)
p5.font.bold = True
p5b = tf5.add_paragraph()
p5b.text = "团队共享记忆\n隐私边界设计"
p5b.font.size = Pt(12)
p5b.font.color.rgb = RGBColor(180,180,180)

# Summary
summary = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(3.6), Inches(4.4), Inches(9.0), Inches(1.8))
summary.fill.solid()
summary.fill.fore_color.rgb = RGBColor(15,15,15)
summary.line.color.rgb = RGBColor(80,80,80)
tf_sum = summary.text_frame
tf_sum.word_wrap = True
p_sum = tf_sum.paragraphs[0]
p_sum.text = "趋势洞察：AI 从被动工具向主动伙伴进化"
p_sum.font.size = Pt(16)
p_sum.font.color.rgb = RGBColor(255,255,255)
p_sum.font.bold = True
p_sum2 = tf_sum.add_paragraph()
p_sum2.text = "情感连接 → 记忆延续 → 主动介入 → 能力扩展 → 组织融入"
p_sum2.font.size = Pt(14)
p_sum2.font.color.rgb = RGBColor(150,150,150)

add_textbox(slide, 0.5, 6.8, 12, 0.5, '"我们不是在造更好的工具，而是在造更好的伙伴。"', 16, RGBColor(110,110,115))

# Page 11: Summary
fill.solid()
fill.fore_color.rgb = RGBColor(0,0,0)
add_textbox(slide, 0.5, 0.4, 10, 0.9, "P100-recordpen 编译 + 烧录 + 调试", 38, RGBColor(255,255,255))
add_textbox(slide, 0.5, 1.1, 10, 0.4, "一个请求激活四个子系统", 18, RGBColor(161,161,166))
shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(5.5), Inches(2.6), Inches(2.4), Inches(2.4))
shape.fill.solid()
shape.fill.fore_color.rgb = RGBColor(10,10,12)
shape.line.color.rgb = RGBColor(255,255,255)
tf = shape.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "帮我编译并\n烧录到设备上\n调试固件"
p.font.size = Pt(16)
p.font.color.rgb = RGBColor(255,255,255)
p.alignment = PP_ALIGN.CENTER
add_textbox(slide, 2.0, 1.8, 2.2, 1.0, "1. Bootstrap\n加载 5 个核心 md", 15, RGBColor(96,165,250))
add_textbox(slide, 9.0, 1.8, 2.2, 1.0, "2. Skills\n命中 device-build-debug", 15, RGBColor(245,158,11))
add_textbox(slide, 1.2, 5.0, 2.2, 1.0, "3. Memory\n检索 IP / 编译参数", 15, RGBColor(167,139,250))
add_textbox(slide, 9.8, 5.0, 2.4, 1.0, "4. System Prompt\n拼 SSH + Sandbox", 15, RGBColor(52,211,153))
add_textbox(slide, 4.5, 6.2, 4.5, 0.8, "SSH (Compile)  ->  rsync (Flash)  ->  adb (Debug)", 18, RGBColor(200,200,200))
add_code_block(slide, 0.5, 5.4, 3.5, 0.8, "device-build-debug", 14)

# Page 11: Summary
slide = prs.slides.add_slide(prs.slide_layouts[6])
fill = slide.background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(245,245,247)
add_textbox(slide, 5.2, 1.6, 3, 1.2, "Inject", 90, RGBColor(0,0,0))
add_textbox(slide, 5.0, 2.8, 3.4, 1.2, "Assemble", 90, RGBColor(0,0,0))
add_textbox(slide, 5.3, 4.0, 3, 1.2, "Extend", 90, RGBColor(0,0,0))
add_textbox(slide, 5.2, 5.2, 3, 1.2, "Persist", 90, RGBColor(0,0,0))
add_textbox(slide, 5.0, 6.8, 3.5, 0.4, "Engineering, not magic.", 18, RGBColor(136,136,136))

output_path = '/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-13-001-openclaw-ppt-design/OpenClaw_PPT_Template.pptx'
prs.save(output_path)
print(f"Saved: {output_path}")
