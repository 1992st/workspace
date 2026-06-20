---
name: market-sector-prediction
description: Win_Stock × Vibe-Trading 大盘与板块预测 Skill - 受控接入 Vibe-Trading，生成可追溯、可复盘的大盘/板块预测
version: 1.0
---

# Market Sector Prediction Skill

## 定位

本 Skill 使用 HKUDS/Vibe-Trading 作为受控研究引擎。Win_Stock 负责事实裁决、质量门控、报告保存、索引、复盘和个股分析上下文注入。

Vibe-Trading 只提供研究证据，不直接成为最终预测结论。

## 强制原则

1. 先能力探测，再调用 Vibe 工具。
2. 只允许调用白名单工具，禁止透传用户指定 tool。
3. Win_Stock 本地事实优先于 Vibe 文本观点。
4. 所有正式预测必须保存 JSON、Markdown 和 index。
5. 数据不足时写 blocked report，不输出方向预测。
6. 日常 standard 模式不调用 swarm。
7. deep 模式失败可降级 standard，但必须标注。

## 正式入口

```bash
python3 skills/stock-skill/scripts/run.py run --skill prediction --action prediction.health.check --input '{}'
python3 skills/stock-skill/scripts/run.py run --skill prediction --action prediction.market.generate --input '{"horizon":"short"}'
python3 skills/stock-skill/scripts/run.py run --skill prediction --action prediction.sector.generate --input '{"sector":"证券","horizon":"short"}'
```

## 保存路径

```text
data/market/predictions/
data/sectors/predictions/
data/predictions/vibe_runs/
```

## 禁止事项

- 数据缺失时编造预测
- Vibe MCP 不可用时假装完成研究
- 未保存报告就返回结论
- 使用未登记 Vibe 工具
- 把 Vibe 观点覆盖 Win_Stock 本地事实
