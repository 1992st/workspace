# 数据模型设计 - AI-Stock-Pro

## 1. 数据库选型

**开发阶段**: SQLite（简单、无需配置）  
**生产阶段**: PostgreSQL（并发、可靠性）

## 2. 核心表结构

### 2.1 股票基本信息表 (stocks)

```sql
CREATE TABLE stocks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          VARCHAR(10) NOT NULL,          -- 股票代码，如 "000001"
    name            VARCHAR(50) NOT NULL,          -- 股票名称，如 "平安银行"
    exchange        VARCHAR(10) NOT NULL,          -- 交易所，如 "SZ" / "SH"
    industry        VARCHAR(50),                   -- 行业
    sector          VARCHAR(50),                   -- 所属板块
    market_cap      DECIMAL(20, 2),                -- 市值（亿元）
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, exchange)
);

-- 索引
CREATE INDEX idx_stocks_symbol ON stocks(symbol);
CREATE INDEX idx_stocks_sector ON stocks(sector);
```

### 2.2 日线数据表 (daily_prices)

```sql
CREATE TABLE daily_prices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id        INTEGER NOT NULL,
    date            DATE NOT NULL,
    open            DECIMAL(10, 4),                -- 开盘价
    high            DECIMAL(10, 4),                -- 最高价
    low             DECIMAL(10, 4),                -- 最低价
    close           DECIMAL(10, 4),                -- 收盘价
    volume          BIGINT,                       -- 成交量
    amount          DECIMAL(20, 2),                -- 成交额
    change_pct      DECIMAL(10, 4),                -- 涨跌幅 %
    
    -- 技术指标（冗余存储，加速查询）
    ma5             DECIMAL(10, 4),
    ma10            DECIMAL(10, 4),
    ma20            DECIMAL(10, 4),
    ma60            DECIMAL(10, 4),
    rsi14           DECIMAL(10, 4),
    macd_dif        DECIMAL(10, 4),
    macd_dea        DECIMAL(10, 4),
    macd_hist       DECIMAL(10, 4),
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    UNIQUE(stock_id, date)
);

-- 索引
CREATE INDEX idx_prices_stock_date ON daily_prices(stock_id, date);
CREATE INDEX idx_prices_date ON daily_prices(date);
```

### 2.3 预测记录表 (predictions)

```sql
CREATE TABLE predictions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date     DATE NOT NULL,              -- 预测日期
    stock_id            INTEGER NOT NULL,
    
    -- 预测内容
    action              VARCHAR(10) NOT NULL,       -- 操作：BUY / SELL / HOLD
    confidence          INTEGER CHECK(confidence BETWEEN 0 AND 100),  -- 置信度 0-100
    target_price        DECIMAL(10, 4),             -- 目标价（可选）
    stop_loss_price     DECIMAL(10, 4),             -- 止损价（可选）
    time_horizon        VARCHAR(20),                -- 时间周期：SHORT/MEDIUM/LONG
    
    -- 分析维度（JSON 存储详细分析）
    market_analysis     TEXT,                       -- 大盘分析摘要
    sector_analysis     TEXT,                       -- 板块分析摘要
    technical_analysis  TEXT,                       -- 技术分析摘要
    sentiment_analysis  TEXT,                       -- 情绪分析摘要
    
    -- LLM 输出（原始记录）
    llm_raw_response    TEXT,                       -- LLM 原始输出
    llm_model           VARCHAR(50),                -- 使用的模型
    
    -- 策略标识（支持 A/B 测试）
    strategy            VARCHAR(50) DEFAULT 'llm',  -- 策略类型：llm / code / hybrid
    strategy_version    VARCHAR(20) DEFAULT '1.0', -- 策略版本
    
    -- 元数据
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (stock_id) REFERENCES stocks(id)
);

-- 索引
CREATE INDEX idx_predictions_date ON predictions(prediction_date);
CREATE INDEX idx_predictions_stock ON predictions(stock_id);
CREATE INDEX idx_predictions_strategy ON predictions(strategy);
```

### 2.4 预测验证表 (prediction_results)

```sql
CREATE TABLE prediction_results (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id       INTEGER NOT NULL UNIQUE,    -- 关联预测
    
    -- 实际结果
    verify_date         DATE NOT NULL,              -- 验证日期
    actual_close        DECIMAL(10, 4),             -- 实际收盘价
    actual_change_pct   DECIMAL(10, 4),             -- 实际涨跌幅
    
    -- 验证结果
    is_correct          BOOLEAN,                    -- 预测是否正确
    accuracy_score      DECIMAL(5, 4),              -- 准确度评分 0-1
    
    -- 收益计算
    max_profit_pct      DECIMAL(10, 4),             -- 最大盈利 %
    max_loss_pct        DECIMAL(10, 4),             -- 最大亏损 %
    final_return_pct    DECIMAL(10, 4),             -- 最终收益 %
    
    -- 偏差分析
    deviation_reason    TEXT,                       -- 偏差原因分析
    market_condition    VARCHAR(20),                -- 市场环境：BULL/BEAR/SIDEWAY
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (prediction_id) REFERENCES predictions(id)
);

-- 索引
CREATE INDEX idx_results_verify_date ON prediction_results(verify_date);
CREATE INDEX idx_results_correct ON prediction_results(is_correct);
```

### 2.5 准确率统计表 (accuracy_stats)

```sql
CREATE TABLE accuracy_stats (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date           DATE NOT NULL,              -- 统计日期
    strategy            VARCHAR(50) NOT NULL,       -- 策略类型
    
    -- 统计周期
    period_days         INTEGER DEFAULT 7,          -- 统计周期（天）
    
    -- 总体统计
    total_predictions   INTEGER,                    -- 总预测数
    verified_count      INTEGER,                    -- 已验证数
    correct_count       INTEGER,                    -- 正确数
    accuracy_rate       DECIMAL(5, 4),              -- 准确率
    
    -- 分操作统计
    buy_total           INTEGER,
    buy_correct         INTEGER,
    buy_accuracy        DECIMAL(5, 4),
    
    sell_total          INTEGER,
    sell_correct        INTEGER,
    sell_accuracy       DECIMAL(5, 4),
    
    hold_total          INTEGER,
    hold_correct        INTEGER,
    hold_accuracy       DECIMAL(5, 4),
    
    -- 收益统计
    avg_return_pct      DECIMAL(10, 4),             -- 平均收益
    max_return_pct      DECIMAL(10, 4),             -- 最大收益
    min_return_pct      DECIMAL(10, 4),             -- 最小收益
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stat_date, strategy, period_days)
);

-- 索引
CREATE INDEX idx_stats_date ON accuracy_stats(stat_date);
CREATE INDEX idx_stats_strategy ON accuracy_stats(strategy);
```

### 2.6 新闻/公告表 (news)

```sql
CREATE TABLE news (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    news_date       DATE NOT NULL,                  -- 新闻日期
    stock_id        INTEGER,                        -- 关联股票（可为空，表示宏观新闻）
    
    title           VARCHAR(500) NOT NULL,          -- 标题
    content         TEXT,                           -- 内容
    source          VARCHAR(100),                   -- 来源
    url             VARCHAR(1000),                  -- 链接
    
    -- 情绪分析
    sentiment_score DECIMAL(5, 4),                  -- 情绪分数 -1 到 1
    sentiment_label VARCHAR(20),                    -- 标签：POSITIVE/NEGATIVE/NEUTRAL
    
    -- 关键词（JSON 数组）
    keywords        TEXT,
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (stock_id) REFERENCES stocks(id)
);

-- 索引
CREATE INDEX idx_news_date ON news(news_date);
CREATE INDEX idx_news_stock ON news(stock_id);
CREATE INDEX idx_news_sentiment ON news(sentiment_label);
```

### 2.7 系统日志表 (system_logs)

```sql
CREATE TABLE system_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    log_time        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level           VARCHAR(10) NOT NULL,           -- DEBUG/INFO/WARNING/ERROR
    module          VARCHAR(50),                    -- 模块名
    message         TEXT NOT NULL,                  -- 日志内容
    details         TEXT,                           -- 详细内容（JSON）
    exception       TEXT                            -- 异常堆栈
);

-- 索引
CREATE INDEX idx_logs_time ON system_logs(log_time);
CREATE INDEX idx_logs_level ON system_logs(level);
```

## 3. 关键查询示例

### 3.1 获取某股票的最新预测

```sql
SELECT 
    p.*,
    s.symbol,
    s.name,
    pr.is_correct,
    pr.actual_change_pct
FROM predictions p
JOIN stocks s ON p.stock_id = s.id
LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
WHERE s.symbol = '000001'
ORDER BY p.prediction_date DESC
LIMIT 1;
```

### 3.2 统计某策略最近 30 天准确率

```sql
SELECT 
    strategy,
    COUNT(*) as total,
    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
    ROUND(
        100.0 * SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) / COUNT(*), 
        2
    ) as accuracy_pct
FROM predictions p
JOIN prediction_results pr ON p.id = pr.prediction_id
WHERE p.prediction_date >= date('now', '-30 days')
GROUP BY strategy;
```

### 3.3 获取某股票的预测历史

```sql
SELECT 
    p.prediction_date,
    p.action,
    p.confidence,
    pr.actual_change_pct,
    pr.is_correct,
    dp.close as price_at_prediction
FROM predictions p
JOIN daily_prices dp ON p.stock_id = dp.stock_id 
    AND p.prediction_date = dp.date
LEFT JOIN prediction_results pr ON p.id = pr.prediction_id
WHERE p.stock_id = 1
ORDER BY p.prediction_date DESC;
```

## 4. 数据保留策略

| 数据类型 | 保留期限 | 清理策略 |
|---------|---------|---------|
| 日线数据 | 永久 | 归档到冷存储 |
| 预测记录 | 永久 | 核心数据，保留 |
| 验证结果 | 永久 | 核心数据，保留 |
| 系统日志 | 90 天 | 定期清理 |
| 新闻数据 | 1 年 | 定期归档 |

## 5. 备份策略

```python
# 每日凌晨 3 点自动备份
# SQLite: 直接复制 db 文件
# PostgreSQL: pg_dump

backup_schedule = {
    "frequency": "daily",
    "time": "03:00",
    "retention": "30 days",
    "location": "/backup/ai-stock-pro/"
}
```

---

**设计日期**: 2026-04-02  
**版本**: v1.0
