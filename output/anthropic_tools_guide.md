# Anthropic 工具全景图：从 Claude 到 Cowork，一文读懂

> 2026年2月，Anthropic 的一系列产品更新引发了华尔街软件股的"大抛售"。单日市值蒸发近3000亿美元。但很多人困惑：Anthropic 到底发布了什么？为什么仅仅是"连接器"和"插件"就能引发如此恐慌？
> 
> 本文将梳理 Anthropic 的产品布局，澄清容易混淆的概念，并用真实案例说明这些工具的实际功能。

---

**📸 本文配图截图**：
- *图1：Anthropic Healthcare & Life Sciences 官方公告页面（见上文截图）*
- *图2：The Future of AI at Work: Introducing Cowork 网络研讨会页面（见上文截图）*

---

## 一、Anthropic 产品矩阵：三个层次

Anthropic 的核心产品线可以分为三个层次，面向不同的用户群体：

| 产品 | 目标用户 | 载体形式 | 核心定位 |
|------|---------|---------|---------|
| **Claude.ai** | 普通消费者/知识工作者 | 网页版 + 手机 App | AI 聊天助手，回答问题、写作、分析 |
| **Claude Code** | 开发者/程序员 | 命令行终端工具 | AI 编程助手，直接操作代码库 |
| **Claude Cowork** | 非技术知识工作者 | Mac 桌面应用（研究预览版） | AI "数字同事"，自主执行多步骤任务 |

### 关键区别

**Claude.ai** 是"问答模式"：你提问，它回答，一轮一轮对话。

**Claude Code** 是"开发模式"：你给出一个目标，它自己规划步骤、读取代码文件、执行命令、完成开发任务。

**Claude Cowork** 是"办公模式"：你把任务描述给它，它能在你的电脑上自主工作——整理文件、分析数据、生成报告，不需要你一步步指导。

---

## 二、核心概念澄清：Skills vs Plugins vs Connectors

Anthropic 的术语体系容易让人混淆。以下是关键概念的清晰解释：

### 1. Connectors（连接器）

**是什么**：让 Claude 能够读取外部数据源的工具

**类比**：就像手机里的"账号绑定"，让 Claude 能访问你的 Google Drive、Gmail、Salesforce、医疗数据库等

**Healthcare 领域的真实连接器**：
- **CMS Coverage Database**：查询 Medicare/Medicaid 保险覆盖政策
- **ICD-10**：疾病和手术编码查询
- **NPI Registry**：医生资质验证
- **PubMed**：3500万+ 医学文献

**使用方式**：在 Claude.ai 设置中授权连接，然后在对话中让 Claude 查询这些数据

### 2. Agent Skills（智能体技能）

**是什么**：教 Claude 如何完成特定任务的"说明书"

**技术细节**：
- 每个 Skill 是一个文件夹，包含 SKILL.md 文件
- 加载成本极低：仅 30-50 tokens
- 只在需要时加载完整内容

**真实 Healthcare Skills**：
- **FHIR Development**：帮助开发人员构建医疗数据交换系统
- **Prior Authorization Review**：事先授权审查模板，可交叉比对保险政策、临床指南、患者记录

**使用方式**：开发者通过 Claude Developer Platform 使用；企业用户可以自定义 Skill 来编码内部工作流程

### 3. Plugins（插件）

**是什么**：面向 Cowork 的可共享功能包，打包了 Skill、命令和配置

**与 Skills 的区别**：

| 维度 | Skills | Plugins |
|------|--------|---------|
| 定位 | 教 Claude 如何做某事 | 打包完整的工作流 |
| 载体 | 单个文件夹 | 可安装的软件包 |
| 用户 | 开发者/技术用户 | 非技术知识工作者 |
| 包含内容 | 只有 instructions | Skill + 命令 + 配置 |

**Claude Cowork 的真实 Plugins**：
- **Legal Plugin**：合同审查、NDA分类、合规工作流
- **Sales Plugin**：HubSpot/CRM 集成、客户研究、Pipeline 分析
- **Finance Plugin**：数据对账、财务报表、差异分析
- **Healthcare Plugin**：医疗文档处理、编码查询

**使用方式**：在 Cowork 应用内安装，通过斜杠命令调用（如 `/review-contract`）

---

## 三、引发华尔街恐慌的服务详解

2026年1月30日，Anthropic 发布了 Claude Cowork 的 11 个开源插件。2月初，软件股遭遇血洗：

| 公司 | 跌幅 |
|------|------|
| Salesforce | -6.85% |
| ServiceNow | -6.97% |
| Thomson Reuters | 严重下跌 |
| LegalZoom | 严重下跌 |
| S&P 500 软件指数 | -4%（单日） |

### 真正引发恐慌的两类服务

#### 1. Claude for Healthcare（医疗解决方案）

**真实功能**：

**事先授权审查（Prior Authorization）**
- **场景**：保险公司审批癌症靶向药申请
- **传统流程**：人工核对患者病历、保险政策、临床指南，耗时数小时
- **Claude 增强**：
  1. 连接 CMS 数据库，查询药物是否在 Medicare 覆盖范围内
  2. 核对 ICD 诊断编码是否符合药物适应症
  3. 查阅 PubMed 文献验证临床证据
  4. 生成结构化审批建议报告

**患者消息分类（Care Coordination）**
- **场景**：医院每天收到大量患者门户消息
- **Claude 增强**：自动分类消息优先级，识别需要立即处理的事项

**为什么引发恐慌**：
- 医疗编码查询、事先授权审查是医疗软件公司的核心业务
- 如果这些重复性工作被 AI 自动化，相关软件服务的价值会被重构

#### 2. Claude Cowork Legal Plugin（法律插件）

**真实功能**：

| 命令 | 实际功能 |
|------|---------|
| `/review-contract` | 逐条审查合同，对照公司谈判手册标记风险 |
| `/triage-nda` | 快速分类保密协议：标准通过/法务复核/全面审查 |
| `/vendor-check` | 检查供应商协议状态 |
| `/brief` | 生成简报（每日简报、专题研究） |
| `/respond` | 生成标准化回复邮件 |

**真实案例**：

**NDA 分类处理**
- **场景**：公司法务部每周收到 30 份 NDA
- **传统流程**：法务助理逐份扫描分类（每份 15-30 分钟）
- **使用 `/triage-nda` 后**：
  - 🟢 标准条款（15份）→ 直接批准
  - 🟡 需要复核（10份）→ 标记具体异常条款
  - 🔴 需要谈判（5份）→ 列出争议点
- **结果**：律师只需看标记好的队列

**合同审查**
- **场景**：收到 47 页供应商协议，业务希望周五前签约
- **使用 `/review-contract`**：
  - Claude 逐条比对合同条款 vs 公司谈判手册
  - 标记偏离公司立场的条款
  - 生成具体修订建议（redline）
- **结果**：律师几小时完成初审，而非几天

**为什么引发恐慌**：
- LegalZoom 等公司的基础合同服务可能被替代
- 初级法律工作（文档分类、初稿审查）的自动化威胁传统法律服务模式

---

## 四、用户如何使用：三种场景

### 场景一：普通消费者（Claude.ai）

**你需要的**：浏览器或手机 App

**能做什么**：
- 日常问答、写作、翻译
- 如果购买 Pro/Max 计划，可以使用部分 Connectors（如连接 Apple Health 查看健康数据）

**不能做什么**：
- 无法使用 Cowork 的自主执行功能
- 无法访问企业级 Healthcare/Legal 连接器

### 场景二：开发者（Claude Code）

**你需要的**：终端命令行工具

**能做什么**：
- 代码开发、重构、调试
- 使用 Skills 和 MCP 连接外部工具
- 构建自定义 Agent Skills

**使用示例**：
```bash
# 让 Claude Code 分析代码库并生成文档
claude "分析这个项目的架构，生成 API 文档"

# 使用 Skill 进行代码审查
claude /review-code
```

### 场景三：企业用户（Claude Cowork + Enterprise）

**你需要的**：Mac 桌面应用 + 企业订阅

**能做什么**：
- 使用预置 Plugins（Legal、Sales、Finance 等）
- 连接企业数据源（Google Drive、Gmail、Salesforce、内部数据库）
- 自定义 Plugins 编码内部工作流程

**使用示例**：

**法律团队工作流**：
1. 将 30 份 NDA 放入指定文件夹
2. 输入：`/triage-nda`
3. Claude 自动分类并输出优先级队列
4. 律师按标记处理

**医疗行政工作流**：
1. 连接 CMS、ICD-10、PubMed 连接器
2. 输入："审查这份事先授权申请"
3. Claude 自动查询保险政策、核对诊断编码、生成审查报告
4. 审批员基于报告做最终决定

---

## 五、真实新闻标题回顾

以下是被广泛报道的新闻标题，反映了市场对 Anthropic 产品发布的反应：

> **"Selloff wipes out nearly $1 trillion from software and services stocks"**
> — Reuters, Feb 4, 2026

> **"Anthropic's new AI tool sends shudders through software stocks"**
> — CNN Business, Feb 4, 2026

> **"AI fears pummel software stocks: Is it 'illogical' panic or a SaaS apocalypse?"**
> — CNBC, Feb 6, 2026

> **"Anthropic brings agentic plug-ins to Cowork"**
> — TechCrunch, Jan 30, 2026

> **"Anthropic's Cowork plug-ins and Palantir's claims of faster SAP migrations highlight how AI could potentially erode application service revenues"**
> — Jefferies Analyst Note, Feb 2026

---

## 六、总结：为什么"只是连接器"会引发恐慌？

很多人困惑：如果只是"连接器"，为什么软件股会暴跌？

**核心逻辑**：

1. **不只是连接，而是自主执行**
   - Claude Cowork 不是简单地"读取"你的文件，而是能"操作"你的文件系统
   - 它能自主规划多步骤任务，不需要人工逐步指导

2. **替代的是"人机交互层"**
   - 传统 SaaS 的商业模式：用户通过软件界面操作数据
   - AI Agent 模式：AI 直接操作数据，跳过了软件界面
   - 如果 AI 能直接操作数据，企业可能不再需要买那么多软件许可

3. **压缩的是服务时间**
   - Palantir 宣称：AI 能将 SAP ERP 迁移从"数年"压缩到"两周"
   - 如果实施周期缩短 90%，咨询公司的服务费、软件实施合同金额都会缩水

4. **威胁的是初级工作**
   - 文档分类、数据录入、初稿审查等重复性工作首当其冲
   - 这些正是许多 SaaS 公司和外包公司的核心业务

**但边界也很清楚**：

- Healthcare 不做诊断，只做辅助审查
- Legal 不做判例研究，只做文档处理
- 最终决策仍需人工做出

正如 Thomson Reuters（Westlaw 母公司）的负责人所说：

> "市场正在分化为**操作型 AI** 和**权威型 AI**。两者都有价值，但不是一回事。"

---

## 参考资源

1. [Anthropic Healthcare & Life Sciences 公告](https://www.anthropic.com/news/healthcare-life-sciences) - 2026年1月11日
2. [TechCrunch - Anthropic brings agentic plug-ins to Cowork](https://techcrunch.com/2026/01/30/anthropic-brings-agentic-plugins-to-cowork/) - 2026年1月30日
3. [CNBC - AI fears pummel software stocks](https://www.cnbc.com/2026/02/06/ai-anthropic-tools-saas-software-stocks-selloff.html) - 2026年2月6日
4. [Fortune - Legal AI is splitting in two](https://fortune.com/2026/03/04/legal-ai-thomson-retuers-cocounsel-anthropic-claude-cowork-whats-the-difference/) - 2026年3月4日
5. [MorphLLM - Claude Code Skills vs MCP vs Plugins](https://morphllm.com/claude-code-skills-mcp-plugins) - 2026年指南

---

*文章配图：
- 图1：Anthropic Healthcare 公告页面截图
- 图2：The Future of AI at Work: Introducing Cowork 网络研讨会页面*
