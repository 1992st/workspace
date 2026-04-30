# Win_Stock 变更日志

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
