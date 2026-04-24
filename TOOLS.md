# TOOLS.md - Local Notes

## Python 环境
- 位置: 系统默认 python3
- 依赖: akshare, pandas, numpy, requests, sqlite3

## API Keys（需用户配置）
- DEEPSEEK_API_KEY
- GLM_API_KEY
- KIMI_API_KEY

## 数据源优先级
1. akshare (主)
2. tushare (备，需 token)
3. 本地缓存 SQLite

## 可写目录
- data/watchlist/active/{code}/
- data/news/YYYY/MM/
- data/reports/YYYY/MM/
- logs/

## 当前生效的 Prompts
- prompts/current/ -> prompts/v1/
- market_analysis.md, sector_analysis.md, stock_analysis.md, news_analysis.md, review_analysis.md

## 常用脚本位置
- skills/stock-data/scripts/fetch_daily.py
- skills/daily-review/scripts/review.py
