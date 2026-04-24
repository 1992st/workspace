# Stock Skills 接口需求说明文档（A股优先，免费数据源）

## 1. 文档目的
本文件定义全新 `stock skills` 的数据接口需求，用于指导后续开发与验收。

约束如下：
- 仅允许使用免费数据源。
- 旧代码只作为参考，不作为设计约束。
- 不限制接口形式（REST/SDK/CLI/MCP 均可）。
- 必须统一输出数据契约，保证 Agent 可稳定消费。

## 2. 设计原则
- 分析优先：接口设计围绕“能否支撑有效分析结论”。
- 基础优先：先保证基础接口稳定可用，再叠加高阶接口。
- 可降级：高阶接口失败不得阻断主流程。
- 可追溯：所有数据必须带来源和时间戳。
- 免费可持续：避免依赖高频易封禁的单一源。

## 3. 分层模型（Agent 调用语义）

### 3.1 基础接口（必须有）
基础接口用于形成最小分析闭环，缺失会导致结论不可靠。

### 3.2 高阶接口（增强项）
高阶接口用于提升解释深度、置信度和可操作性，缺失时允许降级。

### 3.3 Agent 调用规则
- 默认先调用基础接口形成初步结论。
- 出现异动、分歧信号、催化事件或用户请求深度分析时，再调用高阶接口。
- 高阶接口失败时，必须输出基础结论并标注“证据缺口”和置信度下调原因。

## 4. 统一请求/响应契约

### 4.1 请求公共字段
- `symbol`: 股票代码（如 `601211`）。
- `market`: 市场标识（首版默认 `CN-A`）。
- `start_time`, `end_time`: 时间范围。
- `timeframe`: 周期（`1m/5m/1d/1w/1M` 等，按能力支持）。
- `adjust`: 复权（`qfq/hfq/none`）。
- `limit`: 返回条数。
- `timeout_ms`: 超时阈值。
- `force_refresh`: 是否跳过缓存。

### 4.2 响应公共结构
- `status`: `ok | degraded | error`。
- `data`: 业务数据主体。
- `meta`: `source`, `source_chain`, `fetched_at`, `latency_ms`。
- `quality`: `completeness`, `freshness`, `consistency`, `score`。
- `error`: `code`, `message`, `retryable`, `failed_sources`。

## 5. 基础接口需求（必须稳定）

## 5.1 `quote.get`（单票实时行情）

### 必需数据（必须返回）
- `symbol`, `name`
- `price`
- `change`, `change_pct`
- `open`, `high`, `low`, `pre_close`
- `volume`, `amount`
- `timestamp`

### 高阶数据（可选增强）
- `bid1_price`, `bid1_volume`, `ask1_price`, `ask1_volume`
- `turnover_rate`, `amplitude`

### 分析价值
- 必需数据用于判断当日强弱、波动区间、量价是否匹配。
- 高阶数据用于盘中博弈判断（压盘/拉抬/出货迹象）。

## 5.2 `quotes.batch.get`（批量行情）

### 必需数据
- `items[]`（每只股票至少包含 `quote.get` 必需字段）
- `universe_size`
- `timestamp`

### 高阶数据
- `advancers`, `decliners`, `flat_count`
- `limit_up_count`, `limit_down_count`

### 分析价值
- 用于横向比较、相对强弱排序、批量异动筛选。

## 5.3 `kline.get`（历史K线）

### 必需数据
- `symbol`, `period`, `adjust`
- `bars[]`:
  - `date`
  - `open`, `high`, `low`, `close`
  - `volume`, `amount`

### 高阶数据
- `turnover_rate`
- `vwap`
- `suspension_flag`

### 分析价值
- 必需数据用于趋势、支撑阻力、回撤与波动分析。
- 高阶数据用于量价结构精细判断和异常交易日识别。

## 5.4 `index.get`（主要指数）

### 必需数据
- `index_code`, `index_name`
- `price`, `change_pct`
- `timestamp`

### 高阶数据
- `volume`, `amount`
- `index_breadth`
- `style_tag`

### 分析价值
- 避免脱离市场环境做个股判断，作为系统性风险锚点。

## 5.5 `trading.calendar.get`（交易日历）

### 必需数据
- `date`
- `is_trading_day`
- `session`（`pre/open/noon/close/post`）
- `next_trading_day`

### 高阶数据
- `holiday_name`
- `special_session_flag`

### 分析价值
- 保证分析时点正确，避免把非交易时段数据当实时数据使用。

## 5.6 `market.snapshot.get`（市场快照）

### 必需数据
- `timestamp`
- `market_change_pct`
- `total_amount`
- `advancers`, `decliners`, `flat_count`

### 高阶数据
- `top_sector_list`
- `turnover_concentration`

### 分析价值
- 用于市场情绪与风险偏好判断，是组合级决策的基础上下文。

## 6. 高阶接口需求（增强分析）

## 6.1 `news.stock.get`（个股新闻）

### 必需数据
- `symbol`
- `events[]`:
  - `title`, `source`, `publish_time`, `url`

### 高阶数据
- `event_type`
- `sentiment_score`
- `importance`
- `is_price_in`

### 分析价值
- 用于催化识别和预期差判断，解释短期波动的驱动因素。

## 6.2 `news.market.get`（市场新闻）

### 必需数据
- `events[]`: `title`, `source`, `publish_time`

### 高阶数据
- `theme_cluster`
- `hot_topic_rank`

### 分析价值
- 识别政策/宏观扰动，辅助判断板块轮动和风险扩散。

## 6.3 `flow.main.get`（主力资金流）

### 必需数据
- `symbol`
- `date`
- `main_net_inflow`

### 高阶数据
- `super_large_net`, `large_net`, `medium_net`, `small_net`

### 分析价值
- 用于验证涨跌的资金支持强度，区分“无量上涨”和“资金推动”。

## 6.4 `flow.order_size.get`（分单结构）

### 必需数据
- `date`
- `big_order_ratio`, `small_order_ratio`

### 高阶数据
- `buy_sell_imbalance`
- `intraday_flow_curve`

### 分析价值
- 用于识别主力/散户主导关系与时段级资金博弈。

## 6.5 `fundamental.valuation.get`（估值）

### 必需数据
- `symbol`
- `pe_ttm`, `pb`
- `market_cap`

### 高阶数据
- `ps_ttm`
- `industry_pe_percentile`
- `peg`

### 分析价值
- 形成估值安全边际判断，约束追高与抄底风险。

## 6.6 `fundamental.metrics.get`（财务关键指标）

### 必需数据
- `report_date`
- `revenue_yoy`, `profit_yoy`
- `roe`
- `gross_margin`

### 高阶数据
- `debt_ratio`
- `cashflow_quality`
- `inventory_turnover`

### 分析价值
- 区分“估值驱动上涨”和“业绩驱动上涨”，提高中期判断可靠性。

## 6.7 `sector.map.get`（板块映射）

### 必需数据
- `symbol`
- `sectors[]`

### 高阶数据
- `primary_sector`
- `concept_tags`

### 分析价值
- 强制将个股放入行业/概念上下文，避免孤立判断。

## 6.8 `sector.heat.get`（板块热度）

### 必需数据
- `sector`
- `change_pct`
- `leader_symbols[]`

### 高阶数据
- `sector_fund_flow`
- `rotation_speed`
- `continuity_score`

### 分析价值
- 判断热点持续性与轮动速度，辅助仓位轮换策略。

## 7. 免费数据源要求
- 每类接口至少定义主源和备源。
- 主源不可用时必须自动降级。
- 禁止单源强依赖导致全链路失效。
- 必须有调用限流与缓存策略，避免免费源触发封禁。

## 8. 降级与容错要求
- 当高阶接口失败：
  - `status` 置为 `degraded`。
  - `error.failed_sources` 填充失败源。
  - 返回基础结论所需字段。
- 当基础接口失败：
  - 返回 `error` 且标记 `retryable`。
  - 可选返回最近可用缓存并显式标记延迟。

## 9. 可观测性要求
- 记录接口调用结果、数据源选择、降级路径。
- 记录核心指标：成功率、P95延迟、空数据率、降级率。
- 支持按接口维度输出健康报告。

## 10. 验收标准（分析可用性导向）
1. 仅使用基础接口即可输出可执行分析建议。
2. 高阶接口可显著提升解释力，但非阻断依赖。
3. 每条分析结论可回溯到具体字段、来源和时间戳。
4. 所有接口满足统一响应契约。
5. 免费源故障场景下，系统仍可输出降级后的有效结果。

## 11. 交付物要求
- 本需求文档作为唯一开发输入。
- 后续实现文档必须逐条映射本文件接口与数据项。
- 测试用例需按“必需数据/高阶数据”分别验收。
