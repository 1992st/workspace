# 阅读提炼计划

## 总目标

把书变成 Win_Stock 的方法增量，而不是摘要。每本书最后必须落到以下至少一类：

- 数据需求变化
- 分析顺序变化
- 风险闸门变化
- 对抗审查变化
- 报告模板变化
- 复盘标签变化
- 运行时策略候选

## P0-1 Trading and Exchanges

核心问题：

- 盘口和成交如何形成价格？
- 哪些交易者提供流动性，哪些交易者消耗流动性？
- 价差、冲击成本、深度、订单类型如何影响短线判断？
- Win_Stock 现在哪些“主力资金”语言应该被替换为市场微结构语言？

预期产物：

- `books/trading_and_exchanges/method_summary.md`
- `references/market_microstructure_notes.md`
- 对 `stock_analysis.md` 的盘口/分时部分提出修订建议

## P0-2 Evidence-Based Technical Analysis

核心问题：

- 技术信号如何避免数据挖掘偏误？
- 样本内有效和样本外有效如何区分？
- Win_Stock 的均线、MACD、放量突破、破位判断哪些必须降级？
- 哪些形态只能作为描述，不能作为预测？

预期产物：

- `books/evidence_based_technical_analysis/method_summary.md`
- `references/technical_signal_validation.md`
- 新增对抗审查项：技术信号是否有验证基础

## P0-3 The Art of Execution

核心问题：

- 判断对错和交易盈亏为什么不是一回事？
- 错误仓位应该如何处理？
- 赢利仓位和亏损仓位应如何区别管理？
- Win_Stock 的操作建议如何从“买卖点”升级为“执行路径”？

预期产物：

- `books/the_art_of_execution/method_summary.md`
- `references/execution_and_position_management.md`
- 报告模板新增“如果判断错了怎么办”

## P1-1 Expected Returns

核心问题：

- 收益来源究竟是什么？
- 风险溢价、估值、成长、动量、流动性、行为偏误如何拆分？
- A 股个股分析里哪些收益来源不可直接套用？

预期产物：

- `books/expected_returns/method_summary.md`
- `references/return_sources_framework.md`

## P1-2 Thinking, Fast and Slow

核心问题：

- Win_Stock 最容易犯哪些认知偏误？
- 用户持仓亏损时，agent 如何防止迎合？
- 如何把行为偏误变成对抗审查清单？

预期产物：

- `books/thinking_fast_and_slow/method_summary.md`
- 更新 `prompts/current/adversarial_review.md` 的偏误审查

## 接入节奏

1. 先归档阅读笔记，不直接进入策略 registry。
2. 每本书至少经过一次实际分析回放验证。
3. 只有能减少误判、能被审查、能复盘的规则才进入 `strategy/registry.json`。
