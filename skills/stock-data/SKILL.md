---
name: stock-data
description: Win_Stock 股票数据获取 Skill - 三层降级：stock-skill → browser网页 → 缓存/跳过
version: 3.0
---

# 股票数据获取 Skill

## 核心原则

**数据不稳定时，绝不强行分析。**

获取优先级：
1. **stock-skill**（主源，akshare + HTTP备源）
2. **browser 网页爬取**（降级，腾讯财经/东方财富）
3. **本地缓存**（兜底）
4. **标记失败**（彻底不可用）

## 三层降级策略

### 第一层：stock-skill

```bash
python3 skills/stock-skill/scripts/run.py \
  run --skill stock --action quote.get \
  --input '{"symbol":"601211","market":"CN-A"}'
```

**成功标志**：返回 `status` 为 `ok` 或 `degraded`
**失败标志**：返回 `status` 为 `error` 或命令执行失败

### 第二层：Browser 网页爬取

当 stock-skill 失败时，使用 browser 工具访问网页 API 获取数据。

#### 腾讯财经 API（推荐，稳定快速）

```
URL: http://qt.gtimg.cn/q=sh{code}
示例: http://qt.gtimg.cn/q=sh601211
```

**返回格式**（GB2312编码，需转UTF-8）：
```
v_sh601211="1~国泰海通~601211~16.60~16.79~16.71~535335~253583~281753~16.59~..."
```

**字段映射**：
| 位置 | 字段 | 说明 |
|------|------|------|
| 0 | 市场标识 | 1=上海 |
| 1 | 名称 | 国泰海通 |
| 2 | 代码 | 601211 |
| 3 | 当前价 | 16.60 |
| 4 | 昨收 | 16.79 |
| 5 | 今开 | 16.71 |
| 6 | 成交量（手）| 535335 |
| 7 | 外盘 | 253583 |
| 8 | 内盘 | 281753 |
| 9 | 买一价 | 16.59 |
| 10 | 买一量 | 686 |
| ... | ... | ... |
| 32 | 时间戳 | 20260424115908 |
| 33 | 涨跌额 | -0.19 |
| 34 | 涨跌幅% | -1.13 |
| 35 | 最高价 | 16.73 |
| 36 | 最低价 | 16.48 |
| 37 | 最新价/成交量/成交额 | 16.60/535335/887662161 |
| 45 | 市盈率 | 10.52 |

#### 东方财富 API（备用）

```
URL: https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f170
示例: https://push2.eastmoney.com/api/qt/stock/get?secid=1.601211&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f170
```

**字段映射**：
| 字段 | 说明 |
|------|------|
| f43 | 最新价（×100） |
| f44 | 最高价（×100） |
| f45 | 最低价（×100） |
| f46 | 今开（×100） |
| f47 | 成交量 |
| f48 | 成交额 |
| f57 | 股票代码 |
| f58 | 股票名称 |
| f60 | 昨收（×100） |
| f170 | 涨跌幅（×100） |

### 第三层：本地缓存

当 stock-skill 和 browser 都失败时，使用本地缓存。

缓存位置：`data/cache/{symbol}/`

### 第四层：标记失败

当所有层级都失败时：
1. 记录失败原因到 `logs/errors/data_fetch_failures.jsonl`
2. 标记股票为 "数据待补"
3. 跳过分析，不生成预测

## 使用示例

### 获取单只股票行情

```python
from win_stock.data import StockDataClient

client = StockDataClient()
result = client.get_quote('601211')

# result 格式
{
    "success": True,
    "source": "stock-skill",  # 或 "browser-tencent", "cache"
    "data": {
        "symbol": "601211",
        "name": "国泰海通",
        "price": 16.60,
        "change": -0.19,
        "change_pct": -1.13,
        "open": 16.71,
        "high": 16.73,
        "low": 16.48,
        "pre_close": 16.79,
        "volume": 53533500,  # 转换为股
        "amount": 887662161,
        "timestamp": "2026-04-24T11:59:08"
    },
    "quality_score": 100,
    "is_cached": False,
    "errors": []
}
```

### 获取K线数据

```python
result = client.get_kline('601211', timeframe='1d', limit=30)
```

## 数据质量检查

```python
def validate_data(data, data_type):
    """
    数据质量检查
    返回: (是否可用, 质量评分, 问题列表)
    """
    if data is None:
        return False, 0, ["数据为 None"]
    
    issues = []
    score = 100
    
    if data_type == 'quote':
        # 检查必要字段
        required = ['symbol', 'name', 'price', 'change', 'change_pct']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            issues.append(f"缺少字段: {missing}")
            score -= len(missing) * 20
        
        # 检查价格合理性
        if data.get('price', 0) <= 0:
            issues.append("价格为非正数")
            score -= 40
        
        # 检查涨跌幅合理性
        change_pct = abs(data.get('change_pct', 0))
        if change_pct > 20:
            issues.append(f"涨跌幅异常: {change_pct}%")
            score -= 30
    
    return score >= 60, max(0, score), issues
```

## 失败处理

```python
def handle_fetch_failure(symbol, errors):
    """处理数据获取失败"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'errors': errors,
        'status': 'pending'
    }
    
    # 写入失败日志
    with open('logs/errors/data_fetch_failures.jsonl', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    # 标记为待补
    mark_pending(symbol, 'quote')
```

## 禁止事项

- ❌ stock-skill 失败时直接跳过，不尝试 browser
- ❌ browser 获取失败时不使用缓存
- ❌ 缓存超过48小时时不提示直接使用
- ❌ 编造数据填充缺口
- ❌ 部分数据缺失时假装完整分析
- ❌ 不记录失败原因直接跳过

## 检查清单

每次数据获取后检查：
- [ ] 是否尝试了 stock-skill
- [ ] stock-skill 失败时是否尝试了 browser
- [ ] browser 失败时是否检查了缓存
- [ ] 数据质量评分是否 >= 60
- [ ] 是否来自缓存（需标记）
- [ ] 失败时是否记录原因
- [ ] 分析报告是否包含数据状态
