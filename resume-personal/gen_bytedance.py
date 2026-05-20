#!/usr/bin/env python3
"""Generate ByteDance-targeted resume .docx"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

doc = Document()

for section in doc.sections:
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(10.5)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

def add_h(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = '微软雅黑'
        run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    return h

def add_p(text, bold=False, italic=False, size=Pt(10.5), color=None, align=None, space_after=Pt(6)):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = '微软雅黑'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    run.font.size = size
    run.bold = bold
    run.italic = italic
    if color: run.font.color.rgb = color
    if align: p.alignment = align
    p.paragraph_format.space_after = space_after
    p.paragraph_format.space_before = Pt(0)
    return p

def add_bullet(text, bold_prefix="", size=Pt(10.5)):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        r = p.add_run(bold_prefix)
        r.bold = True; r.font.name = '微软雅黑'; r.font.size = size
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        r = p.add_run(text)
        r.font.name = '微软雅黑'; r.font.size = size
        r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    else:
        r = p.add_run(text)
        r.font.name = '微软雅黑'; r.font.size = size
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
r = sub.add_run('AI Agent 应用开发 / 嵌入式 AI 架构师')
r.font.size = Pt(12); r.font.color.rgb = RGBColor(0x55,0x55,0x55)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = info.add_run('📞 15099939831  |  ✉️ stone8668534@gmail.com  |  📍 深圳  |  12 年开发经验')
r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x88,0x88,0x88)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

doc.add_paragraph().paragraph_format.space_after = Pt(4)

# ===== 个人总结 (对靶 JD) =====
add_h('个人总结', level=2)
add_p(
    '12 年嵌入式全栈开发经验，近两年深耕 AI Agent 应用领域。'
    '独立设计并实现 Multi-Agent 协作平台（Stone），管理 6 个专业 Agent 的完整生命周期，'
    '涵盖 Agent 工作流引擎、分层记忆系统、MCP 协议集成、LLM 综合决策等核心能力。'
    '同时具备丰富的智能硬件产品落地经验（智能面板/录音卡牌/录音笔/音箱），'
    '对 AI 技术与硬件的结合有深度实践。',
    size=Pt(10.5))

# ===== JD 关键词匹配亮点 =====
add_h('JD 关键词匹配', level=3)
t = doc.add_table(rows=5, cols=2, style='Light Grid Accent 1')
t.alignment = WD_TABLE_ALIGNMENT.CENTER
data = [
    ('JD 要求', '你的经验匹配'),
    ('AI Agent 系统全生命周期开发', 'Stone 平台：Multi-Agent 架构 → 工作流搭建 → 监控 → 异常自愈'),
    ('LLM/RAG/MCP 前沿技术', 'MCP 协议集成、RAG 检索、Function Calling、LLM 综合决策'),
    ('Multi-Agent 协同架构', 'Stone 协调 6 个 Agent，状态监控 + 智能唤醒 + 消息系统'),
    ('Agent 记忆系统设计', 'MemoryStore + ContextBuilder，三级记忆（Critical/Operation/Failure）'),
]
for i, (k, v) in enumerate(data):
    for j, val in enumerate([k, v]):
        cell = t.rows[i].cells[j]
        cell.text = val
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9.5)
                run.font.name = '微软雅黑'
                run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
                if i == 0:
                    run.bold = True

# ===== 项目经验 =====
add_h('项目经验', level=2)

# Project 1: Stone
add_p('AI Agent 多 Agent 协作平台（Stone）', bold=True, size=Pt(12))
add_p('2025 — 至今 · 个人项目', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_bullet('', bold_prefix='Agent 工作流引擎：', size=Pt(10))
add_p('设计 Multi-Agent 协作架构，6 个专业 Agent 的注册、调度、状态监控与异常自愈。支持自适应监控周期（10 分钟/30 分钟），Agent 异常中断后通过 Gateway HTTP API 自动唤醒恢复。', size=Pt(10), space_after=Pt(2))

add_bullet('', bold_prefix='分层记忆系统（MemoryStore）：', size=Pt(10))
add_p('设计三级记忆架构：Critical Memory（持久决策）、Operation Memory（30 天操作记录）、Failure Memory（7 天失败记录）。ContextBuilder 自动组装上下文摘要传递给 subagent，实现跨 session 的上下文继承。', size=Pt(10), space_after=Pt(2))

add_bullet('', bold_prefix='MCP 协议与 LLM 集成：', size=Pt(10))
add_p('集成 MCP Server/Tools 调用机制，通过 Function Calling 实现 Agent 与外部工具的自主交互。支持飞书/WebChat 多渠道消息推送。', size=Pt(10), space_after=Pt(2))

add_bullet('', bold_prefix='LLM 综合决策系统（Win_Stock）：', size=Pt(10))
add_p('用 LLM 四阶段分析（大盘→板块→新闻→个股）替代传统代码评分，构建数据管道（AkShare）→ LLM 推理 → 结果落地的完整闭环。', size=Pt(10), space_after=Pt(2))

add_p('技术栈：OpenClaw Agent Framework · MCP · RAG · LLM (DeepSeek/GPT) · Node.js · Python · Go', size=Pt(9), color=RGBColor(0x66,0x66,0x66), space_after=Pt(8))

# Project 2: Smart Panel
add_p('智能语音面板（Linux + RTOS 双版本）', bold=True, size=Pt(12))
add_p('2018 — 至今 · 思必驰 · 团队 Leader', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_bullet('主导语音对话功能架构设计，完成 SDK 封装维护，应用于整机与车载产品线')
add_bullet('Linux 版：ALSA 音频框架 + Qt 图形界面；RTOS 版：LVGL 轻量化方案')
add_bullet('集成 BLE/BT + WiFi 网络协议栈，打通设备连接全链路')
add_bullet('产品形态包括 86 面板音箱、带屏音箱，均已规模量产')
add_p('技术栈：Linux · FreeRTOS · ALSA · Qt · LVGL · BLE/BT · WiFi · C/C++', size=Pt(9), color=RGBColor(0x66,0x66,0x66), space_after=Pt(8))

# Project 3: Recording Card
add_p('录音卡牌（物奇 7036 芯片）', bold=True, size=Pt(12))
add_p('2023 — 至今 · 思必驰 · 嵌入式 Leader', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_bullet('芯片选型与方案设计，DSP 固件开发，USB HID/MSC Class 集成')
add_bullet('IPC 通信架构，BLE/BT 功能开发，OTA 升级')
add_bullet('攻坚点：CPU 性能调优 + 低功耗优化，实现长时间录音 + 语音分离')
add_p('技术栈：物奇 7036 · DSP · USB HID/MSC · IPC · BLE/BT · C', size=Pt(9), color=RGBColor(0x66,0x66,0x66), space_after=Pt(8))

# Project 4: Recording Pen
add_p('智能录音笔（TL7519+TL9118 双芯片）', bold=True, size=Pt(12))
add_p('2025 — 至今 · 思必驰 · 嵌入式 Leader', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_bullet('BLE 通信协议设计，9 个 GATT 服务，20+ Characteristic，覆盖时间同步/文件传输/OTA/设备控制')
add_bullet('大文件 WiFi 传输通道设计，跨平台兼容（Android/iOS）')

# ===== 工作经历 =====
add_h('工作经历', level=2)

add_p('苏州思必驰信息科技有限公司 · 嵌入式开发 Leader', bold=True, size=Pt(12))
add_p('2018/03 — 至今  |  深圳·南山区', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_bullet('带领嵌入式团队完成 4 条产品线量产：智能音箱、智能面板（Linux/RTOS）、录音卡牌（物奇 7036）、智能录音笔')
add_bullet('负责方案设计、架构评审、核心模块开发、团队管理与跨部门协调')

add_p('上海庆科信息技术有限公司 · 嵌入式开发', bold=True, size=Pt(12))
add_p('2014/07 — 2018/02  |  深圳', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88))
add_bullet('WiFi 模块固件开发，主导阿里小智、京东微联等 IoT 平台设备对接')
add_bullet('带领团队（嵌入式+销售+产品经理）完成智能硬件从立项到生产')

# ===== 技术栈 =====
add_h('技术栈', level=2)
t = doc.add_table(rows=6, cols=2, style='Light Grid Accent 1')
t.alignment = WD_TABLE_ALIGNMENT.CENTER
data = [
    ('AI/Agent', 'Multi-Agent 架构、MCP 协议、RAG、Function Calling、LLM 应用、OpenClaw Framework'),
    ('编程语言', 'C/C++（主力）、Python、Go、Node.js、Shell'),
    ('嵌入式系统', 'Linux 嵌入式、FreeRTOS、Buildroot、交叉编译、ALSA、DSP'),
    ('无线通信', 'BLE/BT 协议栈、WiFi 双模、USB HID/MSC'),
    ('芯片平台', '君正 X 系列、全志 872、物奇 7036、TL7519、RK3588'),
    ('工具与平台', 'Git、Docker、SSH/rsync/adb、Feishu API'),
]
for i, (k, v) in enumerate(data):
    t.rows[i].cells[0].text = k
    t.rows[i].cells[1].text = v
    for cell in t.rows[i].cells:
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.size = Pt(10)
                run.font.name = '微软雅黑'
                run.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

# ===== 教育 =====
add_h('教育经历', level=2)
add_p('广东石油化工学院  |  电气工程及其自动化  |  本科  |  2011/09 — 2015/07')

p = '/Volumes/zhangstExtern/openclaw/workspace/stone/resume-personal/versions/张树童_简历_字节AI智能体岗.docx'
doc.save(p)
print(f'✅ {p}')
