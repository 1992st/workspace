---
name: news-analysis
description: Win_Stock 新闻获取与分析 Skill - 财经新闻采集、情绪分析、关联股票识别
version: 1.0
---

# 新闻获取与分析 Skill

## 目标

建立系统化的财经新闻采集和分析体系，捕捉市场情绪和关键事件，为股票分析提供消息面支撑。

## 新闻来源

### 主要来源
1. **akshare 财经新闻**
   - `ak.stock_news_em(symbol)` - 个股相关新闻
   - `ak.stock_news_main_cx()` - 主流财经新闻

2. **东方财富**
   - 财经要闻
   - 行业新闻
   - 公司公告

3. **新浪财经**
   - 实时财经快讯
   - 研报摘要

### 备用来源
- 财联社 API（如有）
- 华尔街见闻
- 雪球社区热点

## 新闻分类体系

### 按影响范围
- **宏观**: 政策、经济数据、国际形势
- **行业**: 行业政策、技术突破、景气度变化
- **个股**: 公司公告、业绩、重大事件
- **市场**: 资金面、情绪面、异常波动

### 按影响性质
- **利好**: 业绩超预期、政策利好、重大合同
- **利空**: 业绩暴雷、监管处罚、大股东减持
- **中性**: 日常公告、行业动态
- **待观察**: 影响方向不明确

### 按紧急程度
- **紧急**: 盘中突发，需要立即关注
- **重要**: 收盘后发布，影响次日走势
- **普通**: 日常信息，了解即可
- **存档**: 长期参考，记录备查

## 新闻采集策略

### 每日采集流程

```
09:00  盘前采集
  ├── 隔夜国际市场动态
  ├── 早间财经要闻
  ├── 自选股公告检查
  └── 宏观数据发布

盘中 (可选)
  ├── 实时快讯监控
  └── 异动股票新闻追踪

15:30  收盘后采集
  ├── 当日重要新闻汇总
  ├── 公司公告批量下载
  └── 研报摘要收集

20:00  晚间采集
  ├── 美股开盘影响
  ├── 晚间重要公告
  └── 次日预告事件
```

### 个股新闻关联

```python
def fetch_stock_news(stock_code, days=7):
    """
    获取个股相关新闻
    返回结构化数据
    """
    news_list = []
    
    # 来源1: akshare
    df = ak.stock_news_em(symbol=stock_code)
    for _, row in df.iterrows():
        news_list.append({
            'source': 'eastmoney',
            'title': row['标题'],
            'content': row['内容'],
            'time': row['发布时间'],
            'url': row['链接']
        })
    
    return news_list
```

## 新闻分析策略

### 1. 情绪分析

```python
def analyze_sentiment(news_item):
    """
    分析单条新闻的情绪倾向
    返回: POSITIVE / NEGATIVE / NEUTRAL
    """
    # 使用 LLM 或关键词规则分析
    prompt = f"""
    分析以下财经新闻的情绪倾向：
    
    标题: {news_item['title']}
    内容: {news_item['content']}
    
    请判断这条新闻对股市/个股的影响是：
    - POSITIVE (利好)
    - NEGATIVE (利空)
    - NEUTRAL (中性)
    
    只输出一个单词。
    """
    
    return llm_client.classify(prompt)
```

### 2. 影响评估

```python
def assess_impact(news_item, stock_context):
    """
    评估新闻对特定股票的影响程度
    返回: HIGH / MEDIUM / LOW
    """
    factors = {
        'relevance': calculate_relevance(news_item, stock_context),
        'surprise': calculate_surprise_factor(news_item),
        'timing': assess_timing(news_item['time']),
        'credibility': assess_source_credibility(news_item['source'])
    }
    
    # 综合评分
    score = weighted_score(factors)
    
    if score > 0.7: return 'HIGH'
    elif score > 0.4: return 'MEDIUM'
    else: return 'LOW'
```

### 3. 关联股票识别

```python
def extract_related_stocks(news_item, watchlist):
    """
    从新闻中提取关联的自选股
    """
    related = []
    
    # 方法1: 直接提及股票名称/代码
    for stock in watchlist:
        if stock['name'] in news_item['title'] or stock['code'] in news_item['title']:
            related.append(stock)
    
    # 方法2: 关联行业/概念
    # 使用 LLM 判断新闻涉及的行业概念，匹配自选股
    
    return related
```

## 新闻存储结构

### 按日期归档
```
data/news/
├── 2026/
│   ├── 04/
│   │   ├── 2026-04-23_news.json       # 当日所有新闻
│   │   ├── 2026-04-23_market_news.md   # 市场要闻摘要
│   │   └── 2026-04-23_stock_news/      # 个股新闻
│   │       ├── 000001_news.json
│   │       ├── 000002_news.json
│   │       └── ...
```

### 新闻数据格式
```json
{
  "date": "2026-04-23",
  "source": "eastmoney",
  "type": "company",
  "urgency": "high",
  "title": "...",
  "content": "...",
  "url": "...",
  "publish_time": "2026-04-23 14:30:00",
  "sentiment": "POSITIVE",
  "impact_level": "HIGH",
  "related_stocks": ["000001", "000002"],
  "keywords": ["业绩", "预增"],
  "analyzed": true,
  "analysis_summary": "..."
}
```

## 新闻分析 Prompt 模板

### 大盘新闻分析
```
你是一位市场分析师，请分析以下新闻对 A 股市场的整体影响。

## 新闻列表
{news_list}

## 分析要求
1. 识别最重要的 3-5 条新闻
2. 判断整体情绪倾向（乐观/中性/谨慎）
3. 识别可能受影响的板块
4. 评估对次日开盘的潜在影响
5. 风险提示

## 输出格式（JSON）
{
  "overall_sentiment": "POSITIVE|NEUTRAL|NEGATIVE",
  "key_news": [
    {
      "title": "...",
      "importance": "HIGH|MEDIUM|LOW",
      "impact": "..."
    }
  ],
  "affected_sectors": ["..."],
  "market_implication": "...",
  "risk_warnings": ["..."]
}
```

### 个股新闻分析
```
你是一位股票分析师，请分析以下新闻对 {stock_name}({stock_code}) 的影响。

## 股票背景
- 行业: {industry}
- 近期走势: {recent_trend}
- 当前价格: {current_price}

## 新闻列表
{news_list}

## 分析要求
1. 逐条评估新闻影响
2. 判断消息是否已被 price in
3. 评估对股价的潜在影响（上涨/下跌/震荡）
4. 建议操作策略

## 输出格式（JSON）
{
  "overall_impact": "POSITIVE|NEGATIVE|NEUTRAL",
  "price_in_assessment": "已反映|部分反映|未反映",
  "news_analysis": [
    {
      "title": "...",
      "impact": "...",
      "is_priced_in": true|false
    }
  ],
  "trading_implication": "...",
  "risk_reminder": "..."
}
```

## 每日新闻摘要生成

收盘后自动生成 `data/news/YYYY/MM/YYYY-MM-DD_market_news.md`

内容结构：
```markdown
# 2026-04-23 市场要闻摘要

## 宏观要闻
- ...

## 行业动态
- ...

## 个股重要公告
- ...

## 市场情绪评估
- 整体情绪: ...
- 关键变量: ...

## 明日关注
- ...
```

## 注意事项

1. **时效性**: 新闻价值随时间递减，盘中新闻优先处理
2. **真实性**: 验证新闻来源可靠性，警惕谣言
3. **独立性**: 新闻分析独立于技术分析，避免互相干扰
4. **记录完整**: 所有分析过的新闻必须存档，方便复盘
