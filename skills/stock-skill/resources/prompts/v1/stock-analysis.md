# 个股分析模块

分析重点：
- 不要只描述走势，要回答“这只票为什么会被交易”。
- 先构造 `core_hypothesis`：市场正在交易哪条逻辑，这只票为什么在受益链上。
- 再验证板块位置、个股相对强弱、新闻质量、资金承接、估值与财务约束。
- 明确区分：吸筹、试盘、拉升、分歧、派发、弱承接。

输出要求：
- 先说结论，再说证据，再说执行条件。
- 必须输出 `analysis_meta`，明确写出 `analysis_type`、`data_completeness`、`confidence_cap`、`degradation_reason`。
- 必须输出 `expectation_analysis`、`capital_confirmation`、`scenario_plan`、`trigger_and_invalidation`、`rumor_check`、`source_reliability`。
- 必须把 `data_requirements_context` 作为分析前置思路：先识别分析级别，再说明为什么当前数据足以或不足以支持该级别。
- 若存在 `financial_methodology_context`，必须在基本面判断或反证部分显式使用其中的财报方法摘要，而不是只给估值结论。
- 必须输出 `counter_evidence`：
  - `strongest_counter_points`
  - `why_not_decisive`
- 必须输出 `bias_check`：
  - `recency_bias_check`
  - `single_variable_check`
  - `narrative_check`
  - `cross_ticker_framework_check`
- `expectation_analysis.supporting_evidence` 至少列出 market / sector / capital 三类证据。
- `capital_confirmation.verdict` 只能从 `confirmed|mixed|distribution|unknown` 中选择。
- `rumor_check.final_verdict` 必须明确说明是 `official_confirmed`、`multi_source_confirmed`、`market_reacting_without_confirmation`、`rumor_only` 还是 `no_material_signal`。
- 交易建议必须包含触发条件、失效条件、止损逻辑和目标逻辑。
- 若使用 `profile_context`，必须在推理中明确区分“历史档案”与“本次新证据”。
- 若存在 `profile_context`，建议输出 `profile_updates`，说明本次新增的关键位、股性模式或分析索引。
- 输出必须包含 `strategy_usage`，明确写出本次注入的策略 ID、实际引用的策略 ID、违反的策略 ID 和选择原因。
- 高置信度 `BUY`/`SELL` 结论至少引用 2 条本次注入的策略；数据不足时不得输出高置信度交易计划。
