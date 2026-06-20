# Win_Stock 变更日志

## 2026-05-22 - 分析机制伤害审计

### 新增
- 新增 `reviews/audits/analysis_failure_audit_2026-05-22.md`

### 审计结论
- 旧机制的问题不是单次分析失误，而是允许在数据缺口、账户风险未知、接口失败或证据滞后时仍输出强操作建议。
- 做T、目标价、止损价、主力资金、外资态度等结论必须先通过数据资格和操作权限闸门。
- 后续修复重点从“报告写得完整”转为“证据资格完整、操作权限明确、缺口可审计”。

### 已落实
- `analysis_validation.py` 新增风险闸门、数据缺口和强资金语言硬校验。
- 缺分时拒绝做T；缺 K 线拒绝精确价位；缺融资融券拒绝杠杆压力结论；缺北向/南向拒绝外资态度结论。
- 新增验证测试，`python3 -m unittest skills.stock-skill.tests.test_stock_skill` 通过 29 项。

## 2026-04-24 - 初始创建

### 新增
- 创建 win_stock agent 工作区
- 初始化 4 只自选股档案（601211, 002241, 600519, 000001）
- 创建 5 个核心 skill 目录结构
- 创建 prompts 版本管理体系
- 创建投资规则文档 v1.0

### 目录结构
```
win_stock/
├── skills/
│   ├── workspace-organization/
│   ├── stock-data/
│   ├── stock-analysis/
│   ├── daily-review/
│   └── news-analysis/
├── prompts/
│   ├── current/
│   │   └── investment_rules.md
│   ├── archive/
│   └── experiments/
├── watchlist/
│   ├── 601211/profile.md
│   ├── 002241/profile.md
│   ├── 600519/profile.md
│   └── 000001/profile.md
├── data/
│   ├── history/
│   ├── special/
│   └── news/
├── reviews/
│   ├── daily/
│   └── weekly/
└── docs/
    ├── knowledge/
    ├── rules/
    └── changelog.md
```

### 待完成
- [ ] 配置 cron 任务（盘中监控、收盘复盘、晚间新闻）
- [ ] 初始化历史数据
- [ ] 测试数据获取 skill
- [ ] 创建数据库 schema

## 2026-05-09 - 书籍提炼 Prompt 优化

### 新增
- 新增 `prompts/current/book_method_extraction.md`

### 调整
- 更新 `prompts/README.md`，补充书籍提炼 Prompt 的使用原则
- 更新 `books/_index.md`，加入“当前阅读沉淀”和“阅读与方法沉淀规则”

### 设计变化
- 书籍任务从“机械读书摘要”调整为“方法沉淀任务”
- 支持多种输入材料格式，不绑定单一文件类型
- 要求在总结 Win_Stock 自己的方法前，先综合已有规则、已收录书籍和当前分析 Prompt
- 对归档只保留最小必要约束，避免过度机械化

### 补充
- 在 `skills/stock-analysis/SKILL.md` 中补充书籍/方法沉淀的正式入口
- 明确统一入口只负责路径和索引，不替代 Agent 自行阅读原始材料

## 2026-05-09 - Prompt 版本收敛

### 调整
- `prompts/current/` 收敛为唯一正式生效版本
- 删除 `prompts/v1/`、`prompts/v2/` 的并行维护模式
- 更新 `prompts/README.md` 与 `skills/workspace-organization/SKILL.md`，统一为直接维护 `current/`

### 说明
- 旧版本中没有必须回迁到 `current/` 的独有内容
- 后续如需保留历史，使用 `prompts/archive/`，不再维持 `v1/v2/current` 三套并行

## 2026-05-09 - 双书深度归档与投资规则升级 v2.0

### 新增
- 创建《量价分析 & 因子投资 — 双书归档与个人提炼》，位于 `books/_archive/`
- 完成两本书的 EPUB 原文通读，验证旧笔记准确性并补充细节（行为金融学、多重假设检验、VAP≠VPA 等）
- **投资规则文档升级至 v2.0**：新增 V系列（量价分析纪律 4条）、F系列（因子投资纪律 3条）、X系列（交叉验证与框架纪律 4条）

### 设计变化
- 分析流程从单一技术面升级为五层融合框架：市场环境扫描 → 因子选股 → 量价择时 → 交叉验证 → 执行
- 新增"双框架一致性检验"（X001）作为分析流程的核心安全装置
- 新增"市场可操作等级"（X002）作为每次分析的必输项
- 建立 A 股量价信号的可信度分层：缩量 > 放量（V003）
- 增加因子视角（F001-F003）填补原有分析框架的盲区

### 归档
- 完整归档两本书到 `books/` 目录：PDF 原版 + EPUB 提取版 + 笔记 + 独立批判

## 2026-05-09 - Current 体系完整收口

### 调整
- 修正 `prompts/current/stock_analysis.md`，使输出 schema 与运行时校验契约一致
- 将 `prompts/current/investment_rules.md` 的历史引用改为 `docs/changelog.md`
- 将 `prompts/current/compiled/` 的版本语义从目录版本改为策略包版本
- `compile_book_strategies.py` 改为只写入 `prompts/current/compiled/`
- `analysis_resources.py` 移除对 `prompts/v*` 的 fallback
- `analysis_validation.py` / `analysis_engine.py` 将 `strategy_version` 契约收敛为 `bundle_version`
- 清理 `daily-review`、`stock-skill`、`architecture`、`LLM_PROMPTS`、`books/reminiscences_2005/strategy/README.md` 中与旧版体系冲突的描述
