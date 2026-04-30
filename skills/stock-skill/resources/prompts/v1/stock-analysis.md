# 个股分析模块

分析重点：
- 不要只描述走势，要回答“这只票为什么会被交易”。
- 先构造 `core_hypothesis`：市场正在交易哪条逻辑，这只票为什么在受益链上。
- 再验证板块位置、个股相对强弱、新闻质量、资金承接、估值与财务约束。
- 明确区分：吸筹、试盘、拉升、分歧、派发、弱承接。

输出要求：
- 先说结论，再说证据，再说执行条件。
- 必须输出 `expectation_analysis`、`capital_confirmation`、`scenario_plan`、`trigger_and_invalidation`、`rumor_check`、`source_reliability`。
- `expectation_analysis.supporting_evidence` 至少列出 market / sector / capital 三类证据。
- `capital_confirmation.verdict` 只能从 `confirmed|mixed|distribution|unknown` 中选择。
- `rumor_check.final_verdict` 必须明确说明是 `official_confirmed`、`multi_source_confirmed`、`market_reacting_without_confirmation`、`rumor_only` 还是 `no_material_signal`。
- 交易建议必须包含触发条件、失效条件、止损逻辑和目标逻辑。
- 输出必须包含 `strategy_usage`，明确写出本次注入的策略 ID、实际引用的策略 ID、违反的策略 ID 和选择原因。
- 高置信度 `BUY`/`SELL` 结论至少引用 2 条本次注入的策略；数据不足时不得输出高置信度交易计划。
