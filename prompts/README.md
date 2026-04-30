# Win_Stock Prompt 版本管理

## 目录结构

```
prompts/
├── current/              # 当前生效的 prompts
│   ├── system_prompt.md  # 系统角色定义
│   ├── analysis_framework.md  # 分析框架
│   ├── t_strategy.md     # 做T策略
│   └── investment_rules.md  # 投资规则/纪律
├── archive/              # 历史版本归档
│   ├── v1/
│   ├── v2/
│   └── ...
└── experiments/          # 实验性 prompts（A/B 测试）
```

## 版本管理规则

1. **当前版本**: `current/` 目录下的文件为生效版本
2. **版本号格式**: `v{N}_{描述}.md`，如 `v1_technical_analysis.md`
3. **归档规则**: 每次更新当前版本时，旧版本移入 `archive/v{N}/`
4. **变更记录**: 每个版本文件头部必须包含变更日志

## Prompt 更新流程

```
发现问题/需要优化
    │
    ▼
创建新版本文件
    │
    ▼
旧版本移入 archive/
    │
    ▼
新版本放入 current/
    │
    ▼
记录变更到 changelog.md
    │
    ▼
可选: A/B 测试对比效果
```

## 当前生效 Prompts

- system_prompt.md - 系统角色与核心原则
- analysis_framework.md - 股票分析框架
- t_strategy.md - 做T策略指导
- investment_rules.md - 投资纪律与规则
