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

## 收录标准
- 经典投资/交易书籍
- 有明确可执行的原则
- 跨越时间仍有价值

## 规则合并状态

| 书籍 | 原则数 | 合并到投资规则 | 规则编号 |
|------|--------|--------------|---------|
| 《股票大作手回忆录》 | 20 | ✅ 已合并 | R001-R020 |

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
            创建新版本 v{N+1}
                │
                ▼
            更新软链接 current -> v{N+1}
                │
                ▼
            记录变更日志
```
