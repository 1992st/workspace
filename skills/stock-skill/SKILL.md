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
- `fundamental.valuation.get`
- `fundamental.metrics.get`
- `sector.map.get`
- `sector.heat.get`

## 数据源策略
- 主源：`akshare`
- 备源：免费 HTTP 源（当前覆盖实时行情和市场新闻）
- 兜底：本地缓存 `data/market/cache/`

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
