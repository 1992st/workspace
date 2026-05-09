# Win_Stock Prompt 版本管理

## 目录结构

```
prompts/
├── current/              # 当前生效的 prompts（唯一正式入口）
│   ├── system_prompt.md  # 系统角色定义
│   ├── analysis_framework.md  # 分析框架
│   ├── t_strategy.md     # 做T策略
│   ├── investment_rules.md  # 投资规则/纪律
│   └── book_method_extraction.md # 书籍提炼与方法沉淀
├── archive/              # 历史归档（如未来需要）
└── experiments/          # 实验性 prompts（A/B 测试）
```

## 生效规则

1. **唯一入口**: `current/` 目录下的文件为唯一生效版本
2. **直接维护**: Prompt 优化直接改 `current/`
3. **如需保留历史**: 再按需放入 `archive/`
4. **变更记录**: 重要变更记录到 `docs/changelog.md`

## Prompt 更新流程

```
发现问题/需要优化
    │
    ▼
直接更新 current/
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
- book_method_extraction.md - 书籍提炼、方法融合与最小归档指导

## 书籍提炼 Prompt 使用原则

- 只约束输入发现、综合思考顺序和最小归档要求
- 不强制固定条数、固定表格、固定规则编号
- 支持 PDF、EPUB、TXT、摘录文本、历史笔记等多种材料格式
- 在输出 Win_Stock 自己的方法前，必须先综合已有规则、已收录书籍和当前分析 Prompt
- 只有方法成熟度足够高时，才进一步进入 `strategy/registry.json` 与编译链路
- 统一入口最多只提供路径、索引和材料定位，不替代 Agent 自己阅读书籍
