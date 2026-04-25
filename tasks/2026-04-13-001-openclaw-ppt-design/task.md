---
task_id: 2026-04-13-001
title: "openclaw-ppt-design 专题迁移"
status: REVIEW_READY
owner: agent-radar-desk
created_at: "2026-04-13T15:16:22+0800"
updated_at: "2026-04-16T15:55:00+0800"
---

## 状态
- status: REVIEW_READY

## 交付物清单（已更新）
- `01-cover.html`：封面
- `09-agent-talk.html`：新增 —— Agent 杂谈（5 大实验性功能）
- `10-p100-case.html`：P100 案例演示页
- `11-summary.html`：总结页
- `generate_pptx.py`：`python-pptx` 生成脚本（已更新至 11 页）
- `SPEECH_SCRIPT.md`：完整演讲稿 + 现场演示脚本 + Q&A

## 更新记录（2026-04-16）
1. 新增 Slide 9 "Agent 杂谈"：从 Claude Code 泄露源码看下一代 Agent 趋势
   - BUDDY / Dream System / KAIROS / Swarm / TeamMemory 五大功能
   - 趋势洞察：AI 从被动工具向主动伙伴进化
2. 优化 `generate_pptx.py`：添加第 9 页 Agent Talk 卡片布局
3. 重写 `SPEECH_SCRIPT.md`：
   - 20-25 分钟演讲节奏控制
   - 添加现场演示脚本（P100 / StockAssistant / Agent 观察室）
   - 准备 Q&A 常见问题

## 演讲结构建议
```
PPT 部分 (15 分钟)
├── Slide 1: Cover
├── Slide 2-3: 问题与架构
├── Slide 4-7: Prompt / Skills / Memory / 优化
├── Slide 8: Agent 杂谈（Claude 实验性功能）
└── Slide 9: P100 案例（过渡到现场演示）

现场演示 (5-8 分钟)
├── P100-recordpen 编译烧录
└── 其他案例简要展示

Q&A (5 分钟)
```

## 迁移记录
- source: /Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/dev-topics/_migrated/openclaw-ppt-design
- 由 dev-topics 迁移至 tasks/ 规范目录
- 2026-04-16 新增 Agent Talk 章节和演示脚本
