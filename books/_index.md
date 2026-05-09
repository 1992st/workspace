# Win_Stock 书籍总索引

## 已收录书籍

### 1. 《股票大作手回忆录》
- **ID**: reminiscences_2005
- **原名**: Reminiscences of a Stock Operator
- **作者**: Edwin Lefèvre
- **口述**: Jesse Livermore
- **出版**: 1923 (原著) / 2005 (Wiley新版)
- **路径**: books/reminiscences_2005/
- **原则数**: 20
- **状态**: 已整理
- **投资规则**: 已合并到 prompts/current/investment_rules.md（R001-R020）

## 当前阅读沉淀

### 1. 《量价分析：威科夫的盘口解读方法》 + 《因子投资：方法与实践》
- **当前归档**: `books/_archive/_量价分析_因子投资_读书笔记.md`
- **状态**: 已完成阅读提炼，未进入正式运行时策略
- **说明**: 当前结论以方法候选和体系修正建议为主，后续应结合更多复盘验证后再决定是否进入 `strategy/registry.json`

## 收录标准
- 经典投资/交易书籍
- 有明确可执行的原则
- 跨越时间仍有价值

## 阅读与方法沉淀规则

- 书籍任务的目标不是单篇摘要，而是形成 Win_Stock 可复用的方法增量
- 支持多种材料格式：PDF、EPUB、TXT、提取文本、历史笔记、策略文档
- 提炼时先综合已有方法体系，再总结新的 Win_Stock 方法
- 只要求最小归档：主文档、方法总结、索引入口
- 只有方法成熟度足够高时，才进入 `strategy/registry.json` 和编译链路

## 规则合并状态

| 书籍 | 原则数 | 合并到投资规则 | 规则编号 |
|------|--------|--------------|---------|
| 《股票大作手回忆录》 | 20 | ✅ 已合并 | R001-R020 |
| 《量价分析》/《因子投资》 | 待稳定 | ⏳ 暂未合并 | 待定 |

## 待收录
- [ ] 《聪明的投资者》(The Intelligent Investor) - 预计贡献 R021-R040
- [ ] 《证券分析》(Security Analysis) - 预计贡献 R041-R060
- [ ] 《日本蜡烛图技术》(Japanese Candlestick Charting Techniques)
- [ ] 《漫步华尔街》(A Random Walk Down Wall Street)

## 规则合并流程
```
新增书籍
  │
  ▼
提取原则（books/{book_id}/principles/）
  │
  ▼
整理策略（books/{book_id}/strategy/registry.json）
  │
  ▼
评估是否与现有规则重复/冲突
  │
  ├─ 重复 ──▶ 跳过，标记来源
  │
  ├─ 冲突 ──▶ 标记冲突，人工决策
  │
  └─ 新规则 ─▶ 合并到 prompts/current/investment_rules.md
                │
                ▼
            直接更新 current
                │
                ▼
            如需保留历史再归档
                │
                ▼
            记录变更日志
```
