# MEMORY.md - 长期记忆

## 稳定有效经验
- 先定义问题，再搜集信息，能显著减少无效调研。
- 每篇都给 3 条可执行动作，执行转化更稳定。

## 常见失败模式
- 观点太中性导致行动建议不明确。
- 信息很多但缺少优先级，用户难落地。

## 用户稳定偏好
- 喜欢口语化、好理解的表达。
- 不接受无结论输出。
- 外发前必须明确确认。

## 维护策略
每周更新并去旧，保持 70% 经验 + 30% 用户偏好比例。

## 近期工作记录

### 2025-04-03
- **项目重命名**：从 "Agent 观察室" 改名为 **"Agent 小茶馆"**
- **公众号配置**：完成微信公众号后台接入，创建发布工具
- **首篇文章**：完成 Claude Code 源码泄露事件分析文章（task_id: 2025-04-03-001）
  - 泄露原因：sourcemap 文件未排除
  - 核心发现：BUDDY电子宠物、Undercover卧底模式、Dream记忆系统
  - 技术架构：46万行代码，40+工具，React+Ink终端渲染
  - **源码路径**：`/Volumes/zhangstExtern/openclaw/workspace/stone/claude-code-leaked`
- **浏览器自动化**：成功使用浏览器工具将文章直接保存到公众号草稿箱
- **发布规范**：调研完成公众号 Markdown 转换方案，建立发布规范文档
- **技能架构设计**：结合 OpenClaw 原理设计平台技能系统

## Promoted From Short-Term Memory (2026-05-02)

<!-- openclaw-memory-promotion:memory:memory/2026-04-14.md:1:20 -->
- # Memory Flush - 2026-04-14 ## 今日选题启动 - **时间**：08:43 - **选中选题**：Stanford AI Index 2026 解读：中美 AI 差距正式抹平 - **task_id**：2026-04-14-001 - **任务目录**：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-14-001-ai-index-2026/` - **当前状态**：SCOPING ## 关键情报摘要 - Stanford HAI 2026 AI Index Report 于 4 月 13 日发布 - 核心结论：U.S.-China AI model performance gap has effectively closed - 其他亮点：AI 三年采用率 53%、SWE-bench Verified 近 100%、OSWorld Agent 成功率 66% - 已创建任务文件：task.md / article.md ## 下一步 - 深度阅读报告 PDF 原文 - 收集反证与多元解读 - 输出文章大纲 [score=0.868 recalls=4 avg=0.886 source=memory/2026-04-14.md:1-20]
<!-- openclaw-memory-promotion:memory:memory/2026-04-09.md:35:66 -->
- - ❌ 工具梯队排序无权威来源 - ✅ Ox Security报告、GitClear数据有明确来源 --- ## 文档维护逻辑更新 ``` tasks/ └── YYYY-MM-DD-XXX-标题/ # 每个选题独立目录 ├── article.md # 文章正文 ├── inventory.md # 文件清单 └── assets/ # 图片等素材 publish_queue/ # 待发布包 └── [task_id]-[标题]/ ├── article.md ├── images/ └── publish_checklist.md memory/ └── YYYY-MM-DD.md # 每日工作日志 ``` --- ## 明日计划 - [ ] Task 002发布准备（小红书图片、公众号排版） - [ ] 清理intel/hot临时文件 - [ ] 如时间允许，启动新选题研究 [score=0.805 recalls=3 avg=0.917 source=memory/2026-04-09.md:35-66]

## Promoted From Short-Term Memory (2026-05-03)

<!-- openclaw-memory-promotion:memory:memory/2026-04-10.md:1:24 -->
- --- ## 2026-04-10 晚间归档 · task 2026-04-10-006 - **状态**：REVIEW_READY → APPROVED → **PACKAGED**（用户指令：存档） - **任务内容**：ChatGPT卷入佛罗里达州校园枪击案调查 / 家长AI素养指南 - **关键产出**： - 正文：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-10-006-florida-openai/article.md` - 封面：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-10-006-florida-openai/xiaohongshu-cover.png` - 备份：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-10-006-florida-openai/backups/article_2026-04-10_191530.md` - 小红书配文：已生成 - **内容摘要**： - 标题：😱 ChatGPT卷入校园枪击案调查｜孩子AI越用越溜，家长要学会引导 - 核心切换：由硬新闻事件 → 家长AI引导指南（3条铁律） - 事实锚点：佛罗里达州 / 20岁大学生 / 270条对话 / Uthmeier X声明 - 专家引用：FOSI / Children's National Hospital / Common Sense Media / OpenAI - lumi-writer 优化：因环境 agentToAgent/ACP 策略限制，无法远程委托，文章已在本地完成 xiaohongshu 风格优化并定稿 - **用户确认项**： - [x] 封面设计定稿（用户本地运行 `generate-cover-auto.py` 生成） - [x] 文章正文经多轮迭代定稿 - [x] 新闻链接与X声明引用已补充 - [x] 小红书配文已提供 [score=0.879 recalls=3 avg=1.000 source=memory/2026-04-10.md:1-24]
<!-- openclaw-memory-promotion:memory:memory/2026-04-09.md:1:46 -->
- # 2026-04-09 工作日志 --- ## 已完成任务 ### Task 001: 组织级Agent文章（小红书版） - **状态**: ✅ COMPLETED - **路径**: `publish_queue/` - **内容**: 《AI时代的组织机会：从电力革命到组织级Agent》 - **输出**: 文章v2.0 + HTML图片模板 + 素材清单 ### Task 002: AI技术债务文章 - **状态**: ✅ REVIEW_READY - **路径**: `tasks/2026-04-09-002-AI技术债务/` - **标题**: 《AI让我们产出快了10倍，但维护成本涨了4倍》 - **核心数据**: - 73%工程团队每天使用AI编程工具（2026.3） - 41%新代码由AI生成 - 代码流失率比传统项目高39% - 24%问题存活率 - **数据来源**: Gradually.ai, Tianpan.co, GitClear, Ox Security --- ## 选题记录 ### 选题过程 1. 原选题（Claude 4 vs Cursor）被否 → 数据不可验证 2. 转向AI技术债务选题 → 数据更可靠，跨行业共鸣 3. 标题优化 → 从程序员困境扩展到各行业 ### 数据核实教训 - ❌ Claude Code $25亿ARR无法验证（Medium文章） - ❌ 工具梯队排序无权威来源 - ✅ Ox Security报告、GitClear数据有明确来源 --- ## 文档维护逻辑更新 ``` tasks/ └── YYYY-MM-DD-XXX-标题/ # 每个选题独立目录 ├── article.md # 文章正文 ├── inventory.md # 文件清单 [score=0.851 recalls=3 avg=0.969 source=memory/2026-04-09.md:1-46]

## Promoted From Short-Term Memory (2026-05-10)

<!-- openclaw-memory-promotion:memory:memory/2026-04-13.md:88:108 -->
- - **Design intent**: `SOUL.md` injection note explicitly states "follow its guidance unless higher-priority instructions override it" — `safetySection` is treated as a higher-priority instruction. ## OpenClaw PPT Design — 2026-04-13 产出 - **Status**: Content complete; `.pptx` generation pending manual script fix. - **Case study**: P100-recordpen compile + flash + debug workflow. - **Target**: Engineering deep-dive presentation. - **Output dir**: `/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/dev-topics/_migrated/openclaw-ppt-design/` ### Deliverables completed - `TECH_DOC.md` — comprehensive technical whitepaper on bootstrap injection, prompt assembly, non-`.md` embedded prompts, and default implicit LLM calls. - `SPEECH_SCRIPT.md` — verbatim 10-page speaker notes (~22 min). - `FINAL_PPT_SCRIPT.md` — frame-by-frame design spec (typography, colors, layout, code snippets) produced by `lumi-writer` subagent. - `01-cover.html` … `10-summary.html` — 10 visual concept slides (1920×1080, HTML/SVG) for screenshot import. - `generate_pptx.py` — `python-pptx` scaffold script to produce `.pptx` with correct Apple-style dark/light palette and text placeholders. ### Blockers / next actions - `generate_pptx.py` contains a `RgbColor` → `RGBColor` import typo (fixed in text but needs file rewrite after compaction ends). - Current environment `exec` is `allowlist` for `agent-radar-desk`; user manually running script locally is the fastest path. - Pending user confirmation to batch-screenshot the 10 HTML prototypes or refine any slide content. [score=0.963 recalls=3 avg=1.000 source=memory/2026-04-13.md:88-108]
<!-- openclaw-memory-promotion:memory:memory/2026-04-11.md:1:19 -->
- ## 2026-04-11 工作记录 ### 记忆机制对比文章（task: 2026-04-11-008） - 完成了 Claude Code 与 OpenClaw 记忆机制的深度技术对比长文。 - 文章路径：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/publish_queue/2026-04-11-008/article.md` - 当前标题反馈：**用户认为标题不够好**，需要重新想一个更吸引人的标题。当前标题为《你的 AI 是怎么记住你的？我扒了两个顶级产品的底层代码》。 ### 为文章生成的对比图片素材 - 应用户要求，制作了 3 张对比图（HTML 源文件）： 1. `img1-memory-philosophies.html` — 左右分栏的"反思派 vs 算法派"视觉对比 2. `img2-memory-pipelines.html` — 双栏流水线对比（extractMemories/autoDream vs memory_search/dreaming） 3. `img3-memory-files.html` — 文件布局与数据结构对比 - 存放路径：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/publish_queue/2026-04-11-008/` ### 待办 - [ ] 为 2026-04-11-008 文章换一个更好的标题 - [ ] 将 3 张 HTML 对比图导出为 PNG/PDF 并插入文章 [score=0.944 recalls=4 avg=0.723 source=memory/2026-04-11.md:1-19]
