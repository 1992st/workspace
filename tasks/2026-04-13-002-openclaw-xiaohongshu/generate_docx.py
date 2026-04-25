#!/usr/bin/env python3
"""Generate a readable article.docx from markdown content."""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn

def set_run_font(run, name="PingFang SC", size=11, bold=False, color=RGBColor(0x33,0x33,0x33)):
    font = run.font
    font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    font.size = Pt(size)
    font.bold = bold
    font.color.rgb = color

def add_heading_para(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18 if level == 1 else 14)
    p.paragraph_format.space_after = Pt(8 if level == 1 else 6)
    run = p.add_run(text)
    size = 16 if level == 1 else (14 if level == 2 else 12)
    set_run_font(run, "PingFang SC", size, True, RGBColor(0x1a,0x1a,0x1a))
    return p

def add_normal_para(doc, text, bold=False, indent=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    if indent:
        p.paragraph_format.left_indent = Inches(0.3)
    run = p.add_run(text)
    set_run_font(run, "PingFang SC", 11, bold)
    return p

def add_bullet_para(doc, keyword, desc):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.left_indent = Inches(0.25)
    run1 = p.add_run(f"{keyword}")
    set_run_font(run1, "PingFang SC", 11, True)
    run2 = p.add_run(f" {desc}")
    set_run_font(run2, "PingFang SC", 11, False)
    return p

def add_number_para(doc, keyword, desc):
    p = doc.add_paragraph(style='List Number')
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.left_indent = Inches(0.25)
    run1 = p.add_run(f"{keyword}")
    set_run_font(run1, "PingFang SC", 11, True)
    run2 = p.add_run(f"\n{desc}")
    set_run_font(run2, "PingFang SC", 11, False)
    return p

def add_separator(doc):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(12)
    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    run = p.add_run("—" * 20)
    set_run_font(run, "PingFang SC", 10, False, RGBColor(0xcc,0xcc,0xcc))

def add_quote(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.right_indent = Inches(0.4)
    run = p.add_run(f"\"{text}\"")
    set_run_font(run, "PingFang SC", 12, False, RGBColor(0x66,0x66,0x66))
    p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    return p

# Build document
doc = Document()

# Title
title = doc.add_paragraph()
title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
title.paragraph_format.space_after = Pt(6)
run = title.add_run("说个反常识的：AI 记不住你，不是 Prompt 的问题")
set_run_font(run, "PingFang SC", 20, True, RGBColor(0x0a,0x0a,0x0a))

# Intro
add_normal_para(doc, "很多人没意识到一件事：")
add_normal_para(doc, "你跟 ChatGPT 聊了 20 轮，它\"记得\"你，其实是假象。")
add_normal_para(doc, "每次你发新消息，系统只是把整段对话重新塞给模型。换个窗口、换个会话，它立刻归零。")
add_normal_para(doc, "这不是 Prompt 写得不好，而是 LLM 天生没有记忆。", True)
add_normal_para(doc, "最近我实测了一个框架叫 OpenClaw，它解决的就是这个底层问题。")

add_separator(doc)

# Section 01
add_heading_para(doc, "01 金鱼脑真相", 1)
add_normal_para(doc, "LLM 的默认状态叫 Stateless（无状态）。")
add_normal_para(doc, "大白话就是：它每处理一条消息，都是从头开始认识你。你感觉有连续感，是因为聊天界面在\"伪造\"连续性。")
add_normal_para(doc, "所以这些场景才会反复出现：")
add_bullet_para(doc, "让它参考\"上周那份方案\"", "—— 它一脸懵")
add_bullet_para(doc, "换个窗口", "—— 之前调教好的语气全没了")
add_bullet_para(doc, "想让它主动查个数据、发个邮件", "—— 根本做不到")
add_normal_para(doc, "问题不在模型，而在上下文管理没做好。", True)

add_separator(doc)

# Section 02
add_heading_para(doc, "02 OpenClaw 的四步解法", 1)
add_normal_para(doc, "OpenClaw 的核心思路，可以用四个字概括：")
add_normal_para(doc, "Inject → Assemble → Extend → Persist", True)
add_normal_para(doc, "下面一条一条拆开说。")

add_heading_para(doc, "Inject：给 AI 发一份入职手册", 2)
add_normal_para(doc, "你一开口，系统就往 LLM 里塞东西。相当于提前给它写好了一份「入职手册」，不用每次都重新交代\"你是谁我是谁\"。")
add_normal_para(doc, "具体塞进去的是这四份文档：")
add_bullet_para(doc, "AGENTS.md", "—— 它是谁、负责什么")
add_bullet_para(doc, "SOUL.md", "—— 该怎么说话")
add_bullet_para(doc, "TOOLS.md", "—— 能调用什么工具")
add_bullet_para(doc, "MEMORY.md", "—— 你的偏好和历史记录")
add_normal_para(doc, "一个 4 字的提问，背后可能注入了 8 万字的系统上下文。", True)

add_heading_para(doc, "Assemble：像流水线一样拼 Prompt", 2)
add_normal_para(doc, "OpenClaw 不是让你手写 Prompt，而是自动拼装出一份「导演通知单」。")
add_normal_para(doc, "拼装的结构大致是这样：")
add_bullet_para(doc, "35% 硬编码规则", "—— 安全策略、执行倾向、定时任务约束等")
add_bullet_para(doc, "40% 项目上下文", "—— AGENTS.md、SOUL.md、TOOLS.md 等文档内容")
add_bullet_para(doc, "25% 动态环境", "—— 当前时间、模型配置、沙盒状态")
add_normal_para(doc, "拼完再发给 LLM，保证每次输入都是稳定、可控的。")

add_heading_para(doc, "Extend：可插拔的工具抽屉柜", 2)
add_normal_para(doc, "想让 AI 查天气、发 GitHub PR、或者分析股票？")
add_normal_para(doc, "OpenClaw 的做法是挂载 Skills（技能包）。每个 Skill 就是一份规范文档 SKILL.md，AI 匹配到之后，必须先读取文档，再严格执行。")
add_normal_para(doc, "这相当于给 LLM 配了一个可插拔的工具抽屉柜，想用哪个拉哪个，不用改一行代码。")

add_heading_para(doc, "Persist：真正的长期记忆", 2)
add_normal_para(doc, "对话结束后，关键信息会自动写入 MEMORY.md。")
add_normal_para(doc, "下次再聊，系统会先检索记忆，把你之前的偏好、失败记录、持仓股票都找回来。")
add_normal_para(doc, "不是伪造连续，是真的记得你。")

add_separator(doc)

# Section 03
add_heading_para(doc, "03 一个真实场景：AI 股票助手", 1)
add_normal_para(doc, "我上周用它搭了一个 AI 股票助手。")
add_normal_para(doc, "测试请求只有 6 个字：")
add_quote(doc, "分析一下歌尔股份")
add_normal_para(doc, "OpenClaw 在背后同时激活了 4 个子系统：")
add_bullet_para(doc, "Bootstrap", "—— 注入选股策略 + 风险偏好")
add_bullet_para(doc, "Skills", "—— 命中 stock-api，自动拉取实时行情、板块热度、资金流向")
add_bullet_para(doc, "Memory", "—— 检索自选股列表和历史分析记录")
add_bullet_para(doc, "System Prompt", "—— 把「大盘→板块→新闻→个股」四阶段分析流程拼进 Prompt")
add_normal_para(doc, "然后系统自己跑完四个维度评分，输出一份完整的投资报告：")
add_bullet_para(doc, "总分", "")
add_bullet_para(doc, "操作建议（BUY / HOLD / SELL）", "")
add_bullet_para(doc, "目标价 / 止损价", "")
add_bullet_para(doc, "分批建仓 / 减仓策略", "")
add_normal_para(doc, "6 个字进去，一篇报告出来。", True)

add_separator(doc)

# Section 04
add_heading_para(doc, "04 三条可以今晚就试的动作", 1)
add_number_para(doc, "如果你在用 AI 做重复工作", "整理一份自己的「角色设定文档」，每次对话前贴进去，观察输出稳定性的变化。")
add_number_para(doc, "如果你在做 Agent 产品", "别卷 Prompt 了，去卷「上下文注入和拼装 pipeline」的可控性。")
add_number_para(doc, "如果你纯好奇", "理解「无状态 LLM」和「有状态 Agent」的区别，这会是未来一年的核心分水岭。")

add_separator(doc)

# Footer
add_normal_para(doc, "OpenClaw 的 slogan 很实在：")
quote_p = doc.add_paragraph()
quote_p.paragraph_format.space_before = Pt(8)
quote_p.paragraph_format.space_after = Pt(8)
quote_p.paragraph_format.left_indent = Inches(0.4)
quote_p.paragraph_format.right_indent = Inches(0.4)
run = quote_p.add_run("Engineering, not magic.")
set_run_font(run, "PingFang SC", 13, True, RGBColor(0x33,0x33,0x33))
quote_p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

add_normal_para(doc, "AI 不是魔法，是把无状态的模型，用工程方法变成可控的引擎。")

# Tags
tags = doc.add_paragraph()
tags.paragraph_format.space_before = Pt(16)
tags.paragraph_format.space_after = Pt(8)
run = tags.add_run("#OpenClaw #AI #Agent #LLM #人工智能 #科技分享 #产品经理 #AIGC")
set_run_font(run, "PingFang SC", 10, False, RGBColor(0x99,0x99,0x99))

output_path = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-13-002-openclaw-xiaohongshu/article.docx"
doc.save(output_path)
print(f"Saved: {output_path}")
