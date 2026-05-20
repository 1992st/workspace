#!/usr/bin/env python3
"""Generate ByteDance Volcengine solution architect resume."""

from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

doc = Document()

for s in doc.sections:
    s.top_margin = Cm(2)
    s.bottom_margin = Cm(2)
    s.left_margin = Cm(2.5)
    s.right_margin = Cm(2.5)

style = doc.styles['Normal']
style.font.name = '微软雅黑'
style.font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

def add_h(text, level=1):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.name = '微软雅黑'
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    return h

def add_p(text, bold=False, italic=False, size=Pt(10.5), color=None, align=None, space_after=Pt(6)):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = '微软雅黑'; r.font.size = size; r.bold = bold; r.italic = italic
    r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    if color: r.font.color.rgb = color
    if align: p.alignment = align
    p.paragraph_format.space_after = space_after
    p.paragraph_format.space_before = Pt(0)
    return p

def add_b(text, bp="", size=Pt(10.5)):
    p = doc.add_paragraph(style='List Bullet')
    if bp:
        r = p.add_run(bp); r.bold = True; r.font.name = '微软雅黑'; r.font.size = size
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        r = p.add_run(text); r.font.name = '微软雅黑'; r.font.size = size
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    else:
        r = p.add_run(text); r.font.name = '微软雅黑'; r.font.size = size
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    p.paragraph_format.space_after = Pt(2)
    return p

# ===== HEADER =====
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run('张树童')
r.bold = True; r.font.size = Pt(26); r.font.color.rgb = RGBColor(0x1A,0x1A,0x2E)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run('AI Agent 解决方案架构师  ·  12 年产品落地经验')
r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x55,0x55,0x55)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = info.add_run('📞 15099939831  |  ✉️ stone8668534@gmail.com  |  📍 深圳  |  本科')
r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x88,0x88,0x88)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

doc.add_paragraph().paragraph_format.space_after = Pt(2)

# ===== 个人总结 =====
add_h('个人总结', level=2)
add_p('12 年技术产品化经验，从嵌入式开发转型 AI Agent 架构设计。近两年主导自研 Multi-Agent 协作平台，完成从架构设计到产品落地的全链路闭环。既懂 Agent 技术架构（Multi-Agent、MCP、RAG、LLM 集成），又具备完整的产品化思维——12 年从需求到量产的端到端经验。能将 AI 技术转化为可落地的产品方案，与技术团队和客户高效沟通。')

# ===== 核心能力 =====
add_h('核心能力', level=2)
add_p('▎ AI Agent 与 LLM 应用', bold=True, size=Pt(11), space_after=Pt(2))
add_b('Multi-Agent 协作平台架构、工作流引擎、状态监控与自愈机制', bp='Agent 架构设计：')
add_b('RAG 检索、MCP 协议、Function Calling、Prompt Engineering', bp='LLM 集成：')
add_b('MemoryStore 三级记忆架构（Critical/Operation/Failure）、上下文继承', bp='记忆系统：')
add_b('从需求分析→架构设计→开发落地→部署运维的全生命周期', bp='Agent 产品化：')

add_p('▎ 产品化与嵌入式', bold=True, size=Pt(11), space_after=Pt(2))
add_b('君正 X、全志 872、物奇 7036、TL7519、RK3588', bp='芯片平台：')
add_b('Linux 嵌入式、FreeRTOS、Buildroot、ALSA、LVGL、Qt', bp='系统开发：')
add_b('WiFi、BLE/BT 双模、USB HID/MSC', bp='无线通信：')
add_b('智能音箱、智能面板、录音卡牌、录音笔——4 条产品线从 0 到量产', bp='产品量产：')

# ===== 项目经验 =====
add_h('项目经验', level=2)

# P1: Stone
add_p('AI Agent 多 Agent 协作平台（Stone）', bold=True, size=Pt(12))
add_p('2025 — 至今 · 架构设计与产品落地', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_b('设计 6 个专业 Agent 的协作架构，完成从需求分析、架构设计到产品交付的完整闭环', bp='架构设计与产品化：')
add_b('10 分钟级自适应监控周期，Agent 异常中断后自动唤醒恢复', bp='工作流引擎：')
add_b('MemoryStore + ContextBuilder，跨 session 上下文继承', bp='分层记忆系统：')
add_b('MCP 协议 + Function Calling，打通 Agent 与外部工具的数据通道', bp='MCP 协议集成：')
add_b('LLM 四阶段分析（大盘→板块→新闻→个股），替代传统规则评分', bp='LLM 决策系统：')
add_b('飞书/WebChat 多渠道集成，提供完整技术文档', bp='产品交付：')
add_p('技术栈：OpenClaw Framework · MCP · RAG · LLM (DeepSeek/GPT) · Node.js · Python', size=Pt(9), color=RGBColor(0x66,0x66,0x66), space_after=Pt(8))

# P2: Smart Panel
add_p('智能语音面板 SDK — 产品方案与客户交付', bold=True, size=Pt(12))
add_p('2018 — 至今 · 思必驰 · 团队 Leader', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_b('Linux 版（ALSA + Qt）和 RTOS 版（LVGL），覆盖不同客户需求', bp='双平台方案：')
add_b('语音 SDK 封装维护，多客户快速集成，达到量产标准', bp='SDK 产品化：')
add_b('语音对话功能架构、BLE/BT + WiFi 全链路连接方案', bp='架构设计：')
add_b('86 面板音箱、带屏音箱，均规模量产', bp='产品交付：')

# P3: Recording Card + Pen
add_p('录音卡牌与智能录音笔', bold=True, size=Pt(12))
add_p('2023 — 至今 · 思必驰 · 团队 Leader', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_b('物奇 7036：DSP 固件、USB HID/MSC、IPC 通信、BLE/BT、CPU 调优+低功耗攻坚')
add_b('TL7519+TL9118：BLE 协议设计（9 GATT 服务，20+ Characteristic）、跨平台兼容')

# ===== 工作经历 =====
add_h('工作经历', level=2)
add_p('苏州思必驰信息科技有限公司 · 团队 Leader', bold=True, size=Pt(12))
add_p('2018/03 — 至今  |  深圳', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_b('带领团队完成 4 条产品线量产：智能音箱、智能面板、录音卡牌、智能录音笔')
add_b('负责方案设计、架构评审、核心模块开发、跨部门协调')

add_p('上海庆科信息技术有限公司 · 嵌入式开发', bold=True, size=Pt(12))
add_p('2014/07 — 2018/02  |  深圳', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_b('WiFi 模块固件开发，主导阿里小智、京东微联等 IoT 平台设备对接')
add_b('负责售前方案沟通、联调测试、产线搭建')

# ===== 技术栈 =====
add_h('技术栈', level=2)
t = doc.add_table(rows=5, cols=2, style='Light Grid Accent 1')
t.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, (k, v) in enumerate([
    ('AI/Agent', 'Multi-Agent 架构、MCP 协议、RAG、LLM 集成、Prompt Engineering'),
    ('编程语言', 'C/C++（主力）、Python、Go、Node.js、Shell'),
    ('嵌入式系统', 'Linux、FreeRTOS、Buildroot、ALSA、DSP、LVGL、Qt'),
    ('芯片平台', '君正 X、全志 872、物奇 7036、TL7519、RK3588'),
    ('产品能力', 'SDK 产品化、需求分析、客户方案、量产交付'),
]):
    t.rows[i].cells[0].text = k
    t.rows[i].cells[1].text = v
    for cell in t.rows[i].cells:
        for para in cell.paragraphs:
            for r in para.runs:
                r.font.size = Pt(10); r.font.name = '微软雅黑'
                r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# ===== 教育 =====
add_h('教育经历', level=2)
add_p('广东石油化工学院  |  电气工程及其自动化  |  本科  |  2011/09 — 2015/07')

# ===== 为什么适合 =====
add_h('为什么我适合这个岗位', level=2)
add_p(
    '技术够深：从底层芯片驱动到上层 Agent 架构，每个层都亲手做过。不是只会说"Agent"概念，'
    '而是真正写过 Agent 框架、搭过 MCP 协议、调过 LLM 推理的人。', space_after=Pt(4))
add_p(
    '能落地：12 年从需求到量产的完整产品经验。不是纸上谈兵的架构师，是能把方案变成产品的执行者。',
    space_after=Pt(4))
add_p(
    '懂客户：做过对外 SDK、客户方案、产线搭建。能理解客户需求，也能和技术团队沟通清楚。',
    space_after=Pt(6))

# Footer
f = doc.add_paragraph()
f.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = f.add_run('— 目标岗位：字节跳动 · 火山引擎 · AI Agent 产品解决方案架构师 —')
r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x99,0x99,0x99)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

p = '/Volumes/zhangstExtern/openclaw/workspace/stone/resume-personal/versions/张树童_简历_字节火山引擎_解决方案架构师.docx'
doc.save(p)
print(f'✅ {p}')
