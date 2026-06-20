---
description: Win_Stock 股票数据获取 Skill - 多层降级、数据质量检查、优雅失败
---

# Stock Data Skill

## 用途
获取A股实时行情、历史数据、财务数据。支持多层数据源降级，确保数据可靠性。

## 数据源优先级
1. **健康状态路由** - 先读取 `data/health/source_state.json`，近期失败接口短期熔断
2. **腾讯 HTTP 降级源** - 当前已验证可用于实时行情、三大指数、日 K、1 分钟分时
3. **AkShare / 东方财富** - 数据覆盖广，但当前环境可能慢失败；适合健康检查和可用时补充
4. **本地缓存** - 兜底使用，必须标注缓存年龄和结论影响

不要把“主源名义上更完整”误当作“当前更可靠”。真实路由以最近健康检查为准。

## 使用场景
- 获取单只股票实时行情
- 获取历史K线数据（日线/分钟线）
- 获取财务指标数据
- 批量获取自选股数据
- 验证非常规公开数据入口：公告、监管、融资融券、龙虎榜、大宗交易、ETF/指数、招投标、新闻热度

## 数据质量检查
每次获取数据后必须验证：
- 数据非空检查
- 时间连续性检查（日线数据不能有缺失交易日）
- 价格合理性检查（涨跌幅不超过±20%）
- 数据更新时间检查（实时数据延迟不超过15分钟）

## 接口健康检查

标准分析前或每日盘前/盘后应运行：

```bash
python3 skills/stock-data/scripts/stock_client.py health 601211 002241 600406
python3 skills/stock-data/scripts/stock_client.py alternative 601211 国泰海通
```

健康检查必须覆盖：
- `market`：指数、成交额、市场广度
- `north-south`：北向/南向资金
- `quote`、`kline`、`intraday`
- `sector`、`finance`
- `flow`、`flow-hist`
- `margin`、`lhb`

健康状态分级：
- `healthy`：成功、字段完整、数据新鲜
- `degraded`：成功但字段缺失、使用缓存、或数据滞后
- `unstable`：首次失败、重试成功
- `failed`：连续失败或返回空数据
- `unsupported_now`：盘中天然不可用或条件性可用，如龙虎榜/大宗交易

健康检查结果保存到 `data/health/interface_health_*.json`。失败同时写入 `logs/errors/data_fetch_failures.jsonl`，若数据库可用也写入 `data_fetch_failures`。

非常规公开数据探测结果保存到 `data/health/alternative/alternative_probe_*.json`。它只验证入口和线索来源，不直接生成交易结论。

健康检查还会生成：

```text
data/health/source_state.json
```

这是分析时的接口记忆。若某接口最近为 `failed`，标准数据客户端会短期熔断该接口：

- 有可用缓存：返回缓存，并标注 `cache-after-circuit-breaker`
- 无可用缓存：返回 `health-circuit-breaker`
- 报告必须把该项写入数据缺口

熔断不是永久禁用。下一次健康检查若接口恢复，会自动解除。

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
- 分析前先看健康状态；近期失败接口不重复慢调用
- 如果 AkShare 失败，优先尝试已验证 HTTP 降级源
- 如果都失败，读取本地最新缓存
- 记录失败原因到 `logs/data_errors_{date}.log`
- 基础数据全部失败时，记录失败并跳过分析；禁止在空数据或不可验证数据上继续得出投资结论
- 只有高阶增强数据失败时，才允许降级继续分析，并且必须明确写出证据缺口和置信度下调原因

### 5. 标准分析前置动作

标准分析必须优先调用：

```bash
python3 skills/stock-data/scripts/stock_client.py analysis CODE
```

然后读取返回中的：

- `quality.status`
- `quality.sections`
- `quality.missing_sections`
- `quality.degradation_rules`
- `alternative_data_clues`

禁止绕过这些字段直接用零散接口拼结论。

`analysis` 已自动纳入非常规公开数据雷达。若只想单独排查这些入口，再调用：

```bash
python3 skills/stock-data/scripts/stock_client.py alternative CODE 股票名
```

输出中的 `signal_level` 必须保留到报告：

- `可交易事实`：公告、交易所披露、财报、官方数据
- `强线索`：多源公开数据互相验证
- `弱线索`：单一公开来源、舆情、招投标、招聘、专利等
- `不可用`：无法追溯或不可验证

弱线索只能提出问题，不能直接作为买卖依据。

## 不稳定接口处理

- 实时行情失败：允许使用 5-15 分钟内缓存，并标注缓存年龄。
- K线失败：盘后分析允许使用 24 小时内缓存；盘中禁止输出精确买卖价。
- 融资融券：通常滞后，盘中不可当作当日实时资金；允许使用上一交易日数据但必须标注。
- 北向/南向：失败时不得判断外资流向；盘中可使用当日最近缓存并降级。
- 龙虎榜/大宗交易：盘后或条件性数据，盘中不可硬分析游资席位。
- 分时失败：禁止输出做T计划，只能做收盘级别分析。
- 板块失败：保留个股分析，但不得判断“顺应主线”或“板块退潮”。
- 市场广度失败：指数判断降级，不得强判整体市场环境。
- 接口熔断：说明近期健康检查确认失败，不得把失败项当作正常空值。

报告中必须加入“数据状态”段落，逐项列出行情、K线、大盘、北向南向、融资融券、板块、新闻/公告的数据状态和缺口影响。

## 数据获取后必须执行
1. 验证数据质量
2. 保存到对应路径
3. 记录获取日志（时间、来源、数据条数）
4. 返回标准化格式给调用方
