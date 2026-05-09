# LLM Prompt 设计 - AI-Stock-Pro

## 1. Prompt 工程原则

### 1.1 设计目标
- **可解释性**: LLM 能清晰说明分析逻辑
- **结构化输出**: 便于程序解析和处理
- **一致性**: 相同输入得到稳定输出
- **可验证性**: 预测结果可以被验证

### 1.2 输出格式要求

所有 Prompt 都要求 LLM 以 JSON 格式输出：

```json
{
  "analysis_summary": "简要分析摘要",
  "confidence_score": 75,
  "recommendation": "BUY|SELL|HOLD",
  "reasoning": {
    "market_factors": [...],
    "technical_factors": [...],
    "sentiment_factors": [...],
    "risk_factors": [...]
  },
  "price_targets": {
    "target": 15.50,
    "stop_loss": 13.20,
    "time_horizon": "1-2周"
  },
  "risk_assessment": "LOW|MEDIUM|HIGH",
  "key_catalysts": [...]
}
```

## 2. 分层 Prompt 设计

### 2.1 第一层：市场环境分析 (Market Analysis)

**目的**: 判断当前市场整体环境

```
你是一位资深市场分析师，请基于以下数据分析当前 A 股市场的整体环境。

## 输入数据

### 大盘指数数据（最近 30 天）
{market_data}

### 市场情绪指标
- 涨跌停家数: {limit_up_count} 家涨停, {limit_down_count} 家跌停
- 涨跌家数比: {up_count}:{down_count}
- 成交额: {total_volume} 亿元
- 北向资金: {northbound_flow} 亿元

### 近期重大新闻（最近 3 天）
{recent_news}

## 分析要求

1. 判断当前市场处于什么阶段：
   - 牛市初期/中期/末期
   - 熊市初期/中期/末期
   - 震荡市
   - 不确定

2. 分析市场风险偏好：
   - 高风险偏好（追逐热点）
   - 低风险偏好（防御为主）
   - 中性

3. 识别当前市场主线：
   - 哪些板块或概念受到资金关注
   - 市场风格（大盘股/小盘股、价值/成长）

4. 评估短期（1-2周）市场走向：
   - 上涨概率
   - 下跌概率
   - 震荡概率

## 输出格式

请以 JSON 格式输出，包含以下字段：
- market_phase: 市场阶段
- risk_appetite: 风险偏好
- main_themes: 市场主线（数组）
- short_term_outlook: 短期展望
- confidence: 置信度 (0-100)
- key_risks: 主要风险点（数组）

## 约束
- 基于数据客观分析，避免主观臆断
- 如果不确定，明确说明不确定性
- 不要给出具体投资建议，只分析市场环境
```

### 2.2 第二层：板块/概念分析 (Sector Analysis)

**目的**: 评估特定板块的投资价值

```
你是一位行业研究专家，请分析以下板块的投资价值。

## 输入数据

### 板块基本信息
- 板块名称: {sector_name}
- 板块类型: {sector_type}  # 行业/概念/地域

### 板块成分股表现（最近 5 天）
{sector_stocks_performance}

### 板块资金流向（最近 5 天）
{sector_fund_flow}

### 板块相关新闻
{sector_news}

### 宏观经济/政策影响
{macro_factors}

## 分析要求

1. 板块热度评估：
   - 近期资金流入流出情况
   - 成分股整体表现
   - 市场关注度变化

2. 板块催化剂分析：
   - 是否有政策利好
   - 是否有行业景气度提升
   - 是否有事件驱动

3. 板块持续性评估：
   - 是短期热点还是中期趋势
   - 预计持续时长
   - 退潮信号

4. 板块内部分化：
   - 龙头股 vs 跟风股
   - 哪些细分领域更强

## 输出格式

JSON 格式，包含：
- heat_level: 热度等级 (HIGH/MEDIUM/LOW)
- sustainability: 持续性评估 (SHORT/MEDIUM/LONG)
- catalysts: 催化剂列表
- leaders: 龙头股列表
- risk_signals: 风险信号
- confidence: 置信度
```

### 2.3 第三层：个股综合分析 (Stock Analysis)

**目的**: 对单只股票进行综合分析并给出操作建议

```
你是一位股票投资分析师，请对以下股票进行全面分析，并给出投资建议。

## 输入数据

### 股票基本信息
- 代码: {symbol}
- 名称: {name}
- 行业: {industry}
- 市值: {market_cap} 亿元

### 技术面数据
- 当前价格: {current_price}
- 近期走势: 
  - 5日涨跌幅: {change_5d}%
  - 10日涨跌幅: {change_10d}%
  - 20日涨跌幅: {change_20d}%
  - 60日涨跌幅: {change_60d}%

- 技术指标:
  - MA5: {ma5}, MA10: {ma10}, MA20: {ma20}, MA60: {ma60}
  - MACD: DIF={macd_dif}, DEA={macd_dea}, HIST={macd_hist}
  - RSI(14): {rsi}
  - 布林带: 上轨={boll_upper}, 中轨={boll_mid}, 下轨={boll_lower}

- 成交量分析:
  - 今日成交量: {volume}
  - 20日均量: {avg_volume_20}
  - 量比: {volume_ratio}

### 基本面数据
- 市盈率(TTM): {pe_ttm}
- 市净率: {pb}
- ROE: {roe}%
- 营收增长率: {revenue_growth}%
- 净利润增长率: {profit_growth}%

### 消息面
{news_analysis}

### 所属板块分析
{sector_analysis}

### 大盘环境
{market_analysis}

## 分析要求

1. 技术面分析：
   - 趋势判断（上涨/下跌/震荡）
   - 支撑与阻力位
   - 量价配合情况
   - 技术形态识别

2. 基本面评估：
   - 估值水平（高/中/低）
   - 成长性评估
   - 财务健康状况

3. 消息面评估：
   - 近期是否有重大利好/利空
   - 消息对股价的潜在影响
   - 预期是否已被 price in

4. 综合判断：
   - 结合大盘环境和板块热度
   - 评估风险收益比
   - 确定操作建议

5. 风险管理：
   - 建议止损位
   - 目标价位
   - 适合持仓周期
   - 仓位建议（轻仓/中等/重仓）

## 输出格式

```json
{
  "stock_info": {
    "symbol": "股票代码",
    "name": "股票名称",
    "current_price": 当前价格
  },
  "technical_analysis": {
    "trend": "UP|DOWN|SIDEWAY",
    "support_levels": [支撑位列表],
    "resistance_levels": [阻力位列表],
    "patterns": [识别出的技术形态],
    "volume_assessment": "放量|缩量|正常"
  },
  "fundamental_analysis": {
    "valuation": "OVERVALUED|FAIR|UNDERVALUED",
    "growth_quality": "HIGH|MEDIUM|LOW",
    "financial_health": "STRONG|MODERATE|WEAK"
  },
  "sentiment_analysis": {
    "news_impact": "POSITIVE|NEGATIVE|NEUTRAL",
    "market_sentiment": "乐观|中性|谨慎",
    "expectation_priced_in": "已反映|部分反映|未反映"
  },
  "recommendation": {
    "action": "BUY|SELL|HOLD",
    "confidence": 0-100,
    "position_size": "LIGHT|MODERATE|HEAVY",
    "time_horizon": "SHORT(1-2周)|MEDIUM(1-3月)|LONG(3月+)",
    "target_price": 目标价,
    "stop_loss_price": 止损价,
    "risk_reward_ratio": "风险收益比，如 1:3"
  },
  "reasoning": {
    "primary_factors": [主要看多/看空因素],
    "supporting_factors": [支持性因素],
    "risk_factors": [风险因素],
    "key_catalysts": [关键催化剂],
    "risk_warnings": [风险提示]
  },
  "summary": "一句话总结"
}
```

## 约束
- 必须基于提供的数据分析，不要编造信息
- 如果数据不足，明确说明不确定性
- 保持客观，避免过度乐观或悲观
- 操作建议需要有明确的风险控制（止损位）
- 置信度低于 60 时，建议为 HOLD
```

## 3. Prompt 优化策略

### 3.1 少样本学习 (Few-Shot)

在 Prompt 中加入示例输出：

```
## 示例分析

输入: 某股票技术面显示突破 MA60，成交量放大 2 倍，板块为近期热点...

输出示例:
```json
{
  "technical_analysis": {
    "trend": "UP",
    "patterns": ["突破均线", "放量上涨"],
    "volume_assessment": "放量"
  },
  "recommendation": {
    "action": "BUY",
    "confidence": 75,
    "position_size": "MODERATE",
    "stop_loss_price": 12.50,
    "target_price": 15.80
  },
  "summary": "技术面突破+放量，板块热度高，建议中等仓位买入，止损 12.50"
}
```
```

### 3.2 思维链 (Chain-of-Thought)

要求 LLM 展示推理过程：

```
分析步骤:
1. 首先分析技术面，判断趋势和支撑阻力...
2. 然后评估基本面，确定估值水平...
3. 接着分析消息面，评估情绪影响...
4. 综合以上因素，形成操作建议...
5. 最后确定风险控制和目标价位...

请在 reasoning 字段中展示以上分析过程。
```

### 3.3 自我验证 (Self-Verification)

要求 LLM 检查输出：

```
在输出最终答案前，请检查：
- [ ] 是否基于提供的数据，没有编造
- [ ] 置信度是否与分析的确定性匹配
- [ ] 止损位是否合理（通常 5-10% 止损）
- [ ] 风险收益比是否大于 1:2
- [ ] 操作建议是否与分析结论一致
```

## 4. Prompt 版本管理

```
prompts/
└── current/                 # 当前唯一正式生效版本
```

## 5. Prompt 效果评估

| 指标 | 目标值 | 评估方法 |
|------|--------|---------|
| JSON 解析成功率 | > 95% | 统计解析失败次数 |
| 字段完整性 | > 98% | 检查必要字段是否存在 |
| 置信度校准 | - | 对比置信度和实际准确率 |
| 预测准确率 | > 55% | 对比推荐和实际走势 |

---

**设计日期**: 2026-04-02  
**版本**: v1.0
