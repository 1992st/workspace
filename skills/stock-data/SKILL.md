---
description: Win_Stock 股票数据获取 Skill - 多层降级、数据质量检查、优雅失败
---

# Stock Data Skill

## 用途
获取A股实时行情、历史数据、财务数据。支持多层数据源降级，确保数据可靠性。

## 数据源优先级
1. **AkShare** (首选) - 免费、数据全、更新快
2. **easyquotation** (备用) - 实时行情快速获取
3. **本地缓存** - 避免重复请求

## 使用场景
- 获取单只股票实时行情
- 获取历史K线数据（日线/分钟线）
- 获取财务指标数据
- 批量获取自选股数据

## 数据质量检查
每次获取数据后必须验证：
- 数据非空检查
- 时间连续性检查（日线数据不能有缺失交易日）
- 价格合理性检查（涨跌幅不超过±20%）
- 数据更新时间检查（实时数据延迟不超过15分钟）

## 数据保存路径
```
data/watchlist/active/{code}/history/{code}_{type}_{date}.json
data/watchlist/active/{code}/special/{code}_{type}_{date}.json
data/history/market_{date}.json
```

## 工具使用流程

### 1. 获取实时行情
```python
import akshare as ak
# 使用 akshare 获取实时数据
stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
# 筛选目标股票
target = stock_zh_a_spot_em_df[stock_zh_a_spot_em_df['代码'] == code]
```

### 2. 获取历史数据
```python
# 日线数据
stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date="20240101", adjust="qfq")
# 保存到 data/watchlist/active/{code}/history/
```

### 3. 获取财务数据
```python
# 主要财务指标
stock_financial_report_sina_df = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
# 保存到 data/watchlist/active/{code}/special/finance_{date}.json
```

### 4. 优雅失败处理
- 如果 AkShare 失败，尝试 easyquotation
- 如果都失败，读取本地最新缓存
- 记录失败原因到 `logs/data_errors_{date}.log`
- 基础数据全部失败时，记录失败并跳过分析；禁止在空数据或不可验证数据上继续得出投资结论
- 只有高阶增强数据失败时，才允许降级继续分析，并且必须明确写出证据缺口和置信度下调原因

## 数据获取后必须执行
1. 验证数据质量
2. 保存到对应路径
3. 记录获取日志（时间、来源、数据条数）
4. 返回标准化格式给调用方
