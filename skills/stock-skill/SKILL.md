---
name: stock-skill
description: Win_Stock 统一股票数据技能 - 提供可缓存、可降级、可追溯的 A 股接口
version: 1.0
---

# Stock Skill

## 核心定位
- 为 Agent 提供统一的 A 股数据接口
- 统一契约、缓存、降级、可观测
- 先服务分析链路，不暴露上游源细节

## 使用方式
```bash
python3 runtime/main.py list
python3 runtime/main.py run --skill stock --action quote.get --input '{"symbol":"601211","market":"CN-A"}'
python3 runtime/main.py run --skill stock --action health.report.get --input '{}'
```

## 已实现接口
- `quote.get`
- `quotes.batch.get`
- `kline.get`
- `index.get`
- `trading.calendar.get`
- `market.snapshot.get`
- `news.stock.get`
- `news.market.get`
- `flow.main.get`
- `flow.order_size.get`
- `etf.pcf.get`
- `margin.balance.get`
- `hsgt.top10.get`
- `lhb.detail.get`
- `block_trade.get`
- `fundamental.valuation.get`
- `fundamental.metrics.get`
- `sector.map.get`
- `sector.heat.get`
- `analysis.stock.prepare`
- `analysis.result.validate`

## 数据源策略
- 主源：`akshare`
- 备源：免费 HTTP 源（当前覆盖实时行情和市场新闻）
- 兜底：本地缓存 `data/market/cache/`
- 异常记录：`skills/stock-skill/runtime_data/tool_failures/`
- browser 降级编排不在本 skill 内，统一由 `skills/stock-data/scripts/stock_client.py` 处理

## 高阶资金/交易接口使用边界
- `etf.pcf.get`：盘前可用，返回 ETF 申购赎回清单/PCF；它不是盘中实时净申赎结果，只能作为板块 beta 资金线索。
- `margin.balance.get`：默认按盘后/上一交易日口径使用；盘中若请求当日数据，会返回最近可用交易日并标记 `previous_trading_day_only`。
- `hsgt.top10.get`：用于看沪股通当日活跃股和净买卖方向，按盘后确认口径使用。
- `lhb.detail.get`：仅在股票满足交易公开信息条件时有意义；未上榜返回 `eligible=false`，不是错误。
- `block_trade.get`：盘后数据，用于识别减持压力、机构换手和折价风险，不能单笔直接等价为利空或利好。

## 分析资源
- 模块化 prompt：`skills/stock-skill/resources/prompts/v1/`
- 背景知识：`skills/stock-skill/resources/knowledge/v1/`
- book 策略编译产物：`prompts/v{N}/compiled/`
- `analysis.stock.prepare` 会返回现有数据、数据质量状态、工具异常影响、模块化 prompt、已注入 book 策略、策略版本和知识入口，供上层 Agent 做专业分析
- `analysis.result.validate` 用于校验 LLM 输出是否真实引用了本次注入策略，避免“策略已注入但未生效”

## 输出契约
所有 action 返回：
- `status`
- `data`
- `meta`
- `quality`
- `error`

## 强制原则
1. 结果必须可回溯到来源和时间戳
2. 主源失败要自动降级，不得静默吞错
3. 缓存命中必须标注为缓存，不能伪装实时数据
