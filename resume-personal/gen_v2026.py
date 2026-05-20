#!/usr/bin/env python3
"""Generate v2026 resume .docx."""

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

# ===== Header =====
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title.add_run('张树童 — 简历 v2026')
r.bold = True; r.font.size = Pt(22); r.font.color.rgb = RGBColor(0x1A,0x1A,0x2E)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run('嵌入式开发 Leader  ·  智能硬件产品落地  ·  AI Agent 应用')
r.font.size = Pt(11); r.font.color.rgb = RGBColor(0x66,0x66,0x66)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

add_p('📞 15099939831  |  ✉️ stone8668534@gmail.com  |  📍 深圳', size=Pt(9), color=RGBColor(0x88,0x88,0x88), align=WD_ALIGN_PARAGRAPH.CENTER)

doc.add_paragraph().paragraph_format.space_after = Pt(2)

# ===== 工作经历 =====
add_h('工作经历', level=2)

# 思必驰
add_p('苏州思必驰信息科技有限公司 · 嵌入式开发 Leader', bold=True, size=Pt(12))
add_p('2018/03 — 至今  |  深圳·南山区', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88), space_after=Pt(4))
add_p('带领嵌入式团队完成四大产品线量产：智能音箱、智能面板、录音卡牌、智能录音笔，覆盖 Linux 和 RTOS 双平台。', space_after=Pt(6))

add_p('▎ 智能语音面板（Linux + RTOS 双版本）', bold=True, size=Pt(10.5), space_after=Pt(2))
add_bullet('主导语音对话功能架构设计，完成 SDK 封装维护')
add_bullet('Linux 版：ALSA 音频框架 + Qt 图形界面，完整语音交互')
add_bullet('RTOS 版：LVGL 轻量化方案，资源受限条件下的完整语音方案')
add_bullet('集成 BLE/BT + WiFi 网络协议栈，打通设备连接全链路')
add_bullet('产品形态：86 面板音箱、带屏音箱等，已规模量产')

add_p('▎ 录音卡牌（物奇 7036 芯片）', bold=True, size=Pt(10.5), space_after=Pt(2))
add_bullet('芯片选型与方案设计，DSP 固件开发')
add_bullet('USB HID/MSC Class 集成，PC/移动端即插即用')
add_bullet('IPC 通信架构设计，多任务协同处理')
add_bullet('BLE/BT 功能开发，OTA 升级和远程控制')
add_bullet('攻坚：CPU 性能调优 + 低功耗优化，长时间录音 + 语音分离')

add_p('▎ 智能录音笔（TL7519+TL9118 双芯片）', bold=True, size=Pt(10.5), space_after=Pt(2))
add_bullet('BLE 通信协议设计，9 个 GATT 服务，20+ Characteristic')
add_bullet('时间同步、文件传输、OTA 升级、设备控制完整能力')
add_bullet('大文件传输通道设计（WiFi 通道），跨平台兼容（Android/iOS）')

add_p('▎ 智能音箱与语音方案', bold=True, size=Pt(10.5), space_after=Pt(2))
add_bullet('Linux（君正 X 系列）和 FreeRTOS（全志 872）智能音箱方案')
add_bullet('录音机、语音模块、网络维护模块等核心模块自主设计')
add_bullet('语音 SDK 封装维护，应用于整机与车载产品线')

# 慧声
add_p('深圳市慧声信息科技有限公司 · 嵌入式软件工程师', bold=True, size=Pt(12))
add_p('2018/03 — 2020/01  |  深圳·南山区', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88), space_after=Pt(4))
add_bullet('应用开发 Team Leader（Linux + FreeRTOS）')
add_bullet('基于思必驰语音技术完成智能语音产品方案落地')
add_bullet('SDK 设计与维护，支持客户落地开发')

# 庆科
add_p('上海庆科信息技术有限公司 · 嵌入式开发', bold=True, size=Pt(12))
add_p('2014/07 — 2018/02  |  深圳', italic=True, size=Pt(9), color=RGBColor(0x88,0x88,0x88), space_after=Pt(4))
add_bullet('带领团队（嵌入式+销售+产品经理）完成智能硬件从立项到生产')
add_bullet('WiFi 模块固件开发，主导阿里小智、京东微联、苏宁云等平台设备对接')
add_bullet('成功对接产品数十款：艾美特电暖器（阿里小智首批上线）、长帝烤箱（首个云食谱功能）、格兰仕微波炉全线产品等')

# ===== 技术栈 =====
add_h('技术栈', level=2)
t = doc.add_table(rows=6, cols=2, style='Light Grid Accent 1')
t.alignment = WD_TABLE_ALIGNMENT.CENTER
data = [
    ('芯片平台', '君正 X 系列、全志 872、物奇 7036、TL7519、RK3588'),
    ('嵌入式系统', 'Linux 嵌入式、FreeRTOS、Buildroot、交叉编译'),
    ('编程语言', 'C/C++、Python、Go、Shell'),
    ('无线通信/协议', 'WiFi、BLE/BT 双模、USB HID/MSC、ALSA、DSP'),
    ('AI/Agent', 'OpenClaw Agent 框架、MCP 协议、RAG、LLM 应用'),
    ('图形界面', 'Qt、LVGL'),
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

# ===== Footer =====
doc.add_paragraph()
f = doc.add_paragraph()
f.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = f.add_run('— v2026 · 基于实际项目经验整理 · 2026-05 —')
r.font.size = Pt(9); r.font.color.rgb = RGBColor(0x99,0x99,0x99)
r.font.name = '微软雅黑'; r.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

p = '/Volumes/zhangstExtern/openclaw/workspace/stone/resume-personal/versions/张树童_简历_v2026.docx'
doc.save(p)
print(f'✅ {p}')
