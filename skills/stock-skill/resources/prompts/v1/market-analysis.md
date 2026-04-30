# 市场环境模块

分析重点：
- 先判断今天市场正在交易什么预期，而不是先贴牛熊标签。
- 结合指数、市场广度、成交额、热点板块和市场新闻，识别风险偏好与增量资金方向。
- 明确主线题材、风格偏好、轮动速度，以及明天最关键的验证事件。

输出要求：
- 输出 `market_regime`，至少包含：
  - `current_regime`
  - `risk_appetite`
  - `main_themes`
  - `incremental_capital_direction`
  - `next_verification_events`
- 每条判断标注是直接证据还是推断。
