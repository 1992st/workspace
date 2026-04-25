# Claude 的四种"超能力"：Tools、Skills、MCP、Plugins 到底啥区别？

> 以及那几款让华尔街蒸发 2850 亿美元的金融 Plugin，到底怎么用？

---

2026年2月，Anthropic 发布了几款金融 Plugin，直接引发软件股抛售潮——Intuit、Oracle、SAP 等巨头股价大跌，**2850 亿美元市值一夜蒸发**。

华尔街慌什么？因为这几款 Plugin 让 Claude 从一个"聊天机器人"变成了能直接替代财务分析师的"数字员工"。

但很多人搞混了：Claude 生态里有 Tools、Skills、MCP、Plugins 四个概念，它们到底啥区别？那几款引发震动的金融 Plugin 又是怎么用的？

这篇文章一次讲清楚。

---

## 一、Claude 的四种"超能力"：一张表分清

| 概念 | 是什么 | 谁提供的 | 给谁用 | 白话解释 |
|------|--------|----------|--------|---------|
| **Tools** | 内置基础工具（28+个） | Anthropic 官方 | 开发者/所有用户 | Claude 的"手脚"——读写文件、执行命令、搜索网页 |
| **Skills** | 可安装的能力扩展包 | 社区/第三方 | 高级用户 | Claude 的"专业证书"——教它做特定任务 |
| **MCP** | 外部服务连接协议 | 开放标准 | 系统集成商 | Claude 的"USB 接口"——连 GitHub、数据库等外部系统 |
| **Plugins** | 企业级应用插件 | Anthropic + 生态伙伴 | 企业业务人员 | Claude 的"App Store"——即插即用的业务应用 |

### 层级关系图

```
┌─────────────────────────────────────────────┐
│  Plugins（企业应用商店）                      │
│  ├── 金融分析 Plugin                          │
│  ├── 投资银行 Plugin                          │
│  └── 财富管理 Plugin                          │
├─────────────────────────────────────────────┤
│  MCP Servers（外部连接层）                    │
│  ├── LSEG 金融数据                            │
│  ├── Snowflake 数据仓库                       │
│  └── GitHub/Slack 等                          │
├─────────────────────────────────────────────┤
│  Skills（专业知识包）                         │
│  ├── frontend-design（前端设计）              │
│  ├── code-reviewer（代码审查）                │
│  └── browser-use（浏览器自动化）              │
├─────────────────────────────────────────────┤
│  Tools（原生能力）                            │
│  ├── read/write/edit（文件操作）              │
│  ├── exec（命令执行）                         │
│  ├── web_search（网络搜索）                   │
│  └── browser（浏览器控制）                    │
└─────────────────────────────────────────────┘
```

**一句话总结**：
- **Tools** = 原生手脚（开箱即用）
- **Skills** = 知识加持（教 Claude 做事的方法）
- **MCP** = 连接外部世界的协议
- **Plugins** = 面向业务人员的完整应用

---

## 二、引发华尔街震动的三款金融 Plugin

2026年1-2月，Anthropic 发布了 **Claude for Financial Services** 解决方案，包含多款金融 Plugin。其中三款直接冲击了传统金融软件市场：

### 1. Financial Analysis Solution（财务分析解决方案）

**这是什么？**
Claude 的企业级金融分析平台，统一接入市场数据 + 企业内部数据。

**能干什么？**
- 从研究到报告：拉取实时数据、分析财报、生成研报
- 电子表格分析：搭建可比公司分析、DCF 估值模型、LBO 模型
- 财务建模：从 SEC 文件自动填充三表模型，压力测试
- 交易材料：起草 CIM、Teaser、流程信，生成 PPT

**数据源支持**：
- Daloopa（财报数据）
- Morningstar（估值数据）
- S&P Global（Capital IQ）
- FactSet（股价和基本面）
- LSEG（伦敦证交所数据）
- PitchBook（私募市场数据）

**为什么厉害？**
Claude Opus 4 在 Financial Modeling World Cup 中**通过了 7 个级别中的 5 个**，复杂 Excel 任务准确率达 **83%**。

---

### 2. LSEG 金融数据 Plugin

**合作方**：伦敦证券交易所集团（LSEG）

**功能**：
- 股票研究（Equity Research）
- 估值分析（Valuation）
- 私募股权分析（PE Analysis）
- 投资组合管理（Portfolio Management）

**为什么冲击华尔街？**
这是直接对标 **Bloomberg Terminal** 的功能。以前分析师要花几万美元订阅 Bloomberg，现在 Claude + LSEG Plugin 能用自然语言完成类似分析。

---

### 3. TaxEval（税务评估 Plugin）

**性能数据**：
- Claude Opus 4.6 在税务评估任务上达到 **76% 准确率**
- AIG（美国国际集团）实测：**承保流程提速 5 倍**

**为什么引发抛售？**
Intuit（TurboTax 母公司）的股价在消息发布后大跌——如果 AI 能自动完成 76% 的税务评估工作，传统税务软件的市场空间会被严重挤压。

---

## 三、这些 Plugin 到底怎么用？

### 使用前提

1. **订阅 Claude for Enterprise** 或 **Claude Cowork**
2. 联系 Anthropic 销售开通金融服务模块
3. 配置数据连接（MCP Servers）

### 典型使用场景示例

#### 场景 1：快速生成 DCF 估值模型

**传统流程**：
1. 打开 Bloomberg 下载公司财务数据
2. 打开 Excel 手动搭建模型
3. 查找可比公司数据
4. 调整假设、做敏感性分析
5. 整理成报告
**耗时：4-6 小时**

**用 Claude Financial Plugin**：

```
用户：帮我给 Tesla 做一个 DCF 估值模型，用最新财报数据，
      假设 WACC 8%、永续增长率 3%，做敏感性分析。

Claude：
[自动执行以下步骤]
1. 通过 Daloopa MCP 拉取 Tesla 最新 10-K/10-Q 数据
2. 生成三表联动模型（带蓝/黑/绿颜色规范）
3. 计算自由现金流、折现值
4. 生成敏感性分析表（WACC 6-10%、g 2-4%）
5. 输出为 Excel 文件，带完整公式
```

**耗时：10-15 分钟**

---

#### 场景 2：撰写投行 CIM（保密信息备忘录）

**传统流程**：
1. 收集公司基本信息、财务数据
2. 手动撰写业务概述、市场分析
3. 找设计师做排版
4. 律师审核
**耗时：2-3 天**

**用 Claude Investment Banking Plugin**：

```
用户：为一家 SaaS 公司起草 CIM，ARR 5000 万美元，
      增长率 45%，目标客户是中型 PE 基金。

Claude：
[自动执行]
1. 调取 CIM 标准模板
2. 生成业务概述、财务摘要、市场机会
3. 创建可比公司分析（Comps）
4. 生成 PowerPoint（使用公司品牌模板）
5. 标记需要人工核实的数据点
```

**耗时：30 分钟出初稿，1-2 轮迭代完成**

---

#### 场景 3：财富管理客户报告

**使用 Wealth Management Plugin**：

```
用户：给客户 Zhang 生成本季度投资组合报告，
      需要包含收益分析、税务优化建议、再平衡方案。

Claude：
1. 连接客户持仓数据（通过 Snowflake/Databricks MCP）
2. 计算 Q1 收益、对比基准
3. 识别税务亏损收割（Tax Loss Harvesting）机会
4. 生成再平衡建议
5. 输出客户友好的报告（PDF + 可交互版本）
```

---

## 四、华尔街为什么慌？

**冲击逻辑**：

```
旧模式：
分析师 → Excel + Bloomberg + 多个数据源 → 手工建模 → 报告
人工耗时：4-8 小时/任务
人力成本：$100K-300K/年/分析师

新模式：
自然语言指令 → Claude Plugin → 自动生成分析 → 交付物
耗时：10-30 分钟/任务
成本：Claude Enterprise 订阅费
```

**被威胁的软件公司**：

| 公司 | 产品 | 被替代风险 |
|------|------|-----------|
| Intuit | TurboTax | 税务评估自动化 |
| Oracle | 财务系统 | 企业财务分析 |
| SAP | ERP 财务模块 | 业务流程自动化 |
| Bloomberg | Terminal | 金融数据分析 |
| FactSet | 数据分析平台 | 研究报告生成 |

**市场反应**：
- 2026年2月3日：WSJ 报道引发关注
- 2月4日：CNN 称"Wall Street is panicked"
- 2月5日：金融软件板块蒸发 **$2850 亿市值**

---

## 五、开源资源

Anthropic 在 GitHub 开源了部分金融 Plugin 模板：

- **仓库**：`github.com/anthropics/financial-services-plugins`
- **包含**：
  - `financial-analysis/` - 核心财务分析（41 个 skills，38 个 commands，11 个 MCP 集成）
  - `investment-banking/` - 投资银行工作流
  - `equity-research/` - 股票研究
  - `private-equity/` - 私募股权
  - `wealth-management/` - 财富管理

这些 Plugin 同时兼容 **Claude Cowork**（企业平台）和 **Claude Code**（开发者 CLI）。

---

## 六、总结：四个层级的演进逻辑

Claude 的生态从底层到应用层逐步递进：

1. **Tools**（2024）→ 让 Claude 能动手做事
2. **Skills**（2024-2025）→ 让 Claude 有专业知识
3. **MCP**（2024-2025）→ 让 Claude 能连外部系统
4. **Plugins**（2026）→ 让业务人员直接用

**Plugins 的颠覆性在于**：
- 不需要懂编程（像用 App 一样简单）
- 不需要学 Bloomberg 指令（自然语言就行）
- 不需要切换多个软件（数据到交付物一站式）

---

## 三条可执行动作

1. **如果你是金融从业者**：关注 Claude for Financial Services 的试用申请，特别是如果你每天花大量时间在 Excel 建模上
2. **如果你是开发者**：研究 MCP 协议和 Financial Plugin 的开源实现，思考如何将 AI Agent 能力接入你所在的行业
3. **如果你是投资者/管理者**：重新评估你的软件供应商依赖——哪些工作流可能被 AI Agent + Plugin 替代？数据资产的价值是否被低估？

---

*参考资料：*
- *Anthropic 官方：Claude for Financial Services 发布 (2025.7)*
- *GitHub：anthropics/financial-services-plugins*
- *WSJ/CNN 报道：Anthropic AI Tools Wall Street Impact (2026.2)*
- *Yahoo Finance：$285B Software Selloff Analysis*
