-- Win_Stock 单股数据库初始化脚本
-- 每只股票独立一个 SQLite 数据库
-- 命名: {stock_code}_db.sqlite

-- 1. 股票基本信息表
CREATE TABLE IF NOT EXISTS stock_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(50) NOT NULL,
    industry VARCHAR(50),
    sector VARCHAR(50),
    market_cap DECIMAL(20, 2),
    listing_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 日线数据表（核心数据）
CREATE TABLE IF NOT EXISTS daily_kline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date DATE NOT NULL,
    open DECIMAL(10, 4),
    high DECIMAL(10, 4),
    low DECIMAL(10, 4),
    close DECIMAL(10, 4),
    volume BIGINT,
    amount DECIMAL(20, 2),
    change_pct DECIMAL(10, 4),
    change_amount DECIMAL(10, 4),
    turnover_rate DECIMAL(10, 4),
    -- 技术指标（冗余存储，加速查询）
    ma5 DECIMAL(10, 4),
    ma10 DECIMAL(10, 4),
    ma20 DECIMAL(10, 4),
    ma60 DECIMAL(10, 4),
    rsi14 DECIMAL(10, 4),
    macd_dif DECIMAL(10, 4),
    macd_dea DECIMAL(10, 4),
    macd_hist DECIMAL(10, 4),
    boll_upper DECIMAL(10, 4),
    boll_mid DECIMAL(10, 4),
    boll_lower DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trade_date)
);

-- 3. 分析历史记录表
CREATE TABLE IF NOT EXISTS analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_date DATE NOT NULL,
    analysis_type VARCHAR(20) NOT NULL,  -- 'technical', 'fundamental', 'comprehensive'
    market_env TEXT,                     -- 大盘环境描述
    sector_status TEXT,                  -- 板块状态
    technical_summary TEXT,              -- 技术面分析摘要
    fundamental_summary TEXT,            -- 基本面分析摘要
    sentiment_summary TEXT,              -- 情绪面分析摘要
    conclusion TEXT,                     -- 综合结论
    confidence INTEGER CHECK(confidence BETWEEN 0 AND 100),
    key_factors TEXT,                    -- JSON 数组：关键因素
    risk_factors TEXT,                   -- JSON 数组：风险因素
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 预测记录表
CREATE TABLE IF NOT EXISTS prediction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date DATE NOT NULL,
    prediction_type VARCHAR(20) NOT NULL,  -- 'next_day', 'short_term', 'medium_term'
    action VARCHAR(10) NOT NULL,             -- 'BUY', 'SELL', 'HOLD', 'WATCH'
    confidence INTEGER CHECK(confidence BETWEEN 0 AND 100),
    target_price DECIMAL(10, 4),
    stop_loss_price DECIMAL(10, 4),
    reasoning TEXT,                        -- 预测理由
    market_context TEXT,                     -- 当时市场环境
    strategy_version VARCHAR(10),            -- 使用的策略版本
    llm_model VARCHAR(50),                   -- 使用的 LLM 模型
    llm_raw_response TEXT,                   -- LLM 原始输出
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 预测验证/复盘记录表
CREATE TABLE IF NOT EXISTS review_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER,
    review_date DATE NOT NULL,
    actual_close DECIMAL(10, 4),
    actual_change_pct DECIMAL(10, 4),
    actual_high DECIMAL(10, 4),
    actual_low DECIMAL(10, 4),
    is_correct BOOLEAN,
    accuracy_score DECIMAL(5, 4),          -- 准确度评分 0-1
    max_profit_pct DECIMAL(10, 4),
    max_loss_pct DECIMAL(10, 4),
    deviation_reason TEXT,                 -- 偏差原因分析
    market_condition VARCHAR(20),            -- 'BULL', 'BEAR', 'SIDEWAY', 'VOLATILE'
    lesson_learned TEXT,                   -- 学到的教训
    capital_behavior_note TEXT,            -- 资本行为观察
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES prediction_log(id)
);

-- 6. 特殊事件记录表
CREATE TABLE IF NOT EXISTS special_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_date DATE NOT NULL,
    event_type VARCHAR(30) NOT NULL,       -- 'earnings', 'policy', 'suspension', 'restructuring', 'block_trade', 'shareholder_change', 'other'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    impact_assessment TEXT,                -- 影响评估
    price_reaction DECIMAL(10, 4),         -- 当日股价反应（涨跌幅）
    volume_reaction DECIMAL(10, 4),        -- 成交量变化倍数
    is_expected BOOLEAN,                   -- 是否预期内
    follow_up_needed BOOLEAN,              -- 是否需要后续跟踪
    follow_up_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 资本行为观察记录表
CREATE TABLE IF NOT EXISTS capital_behavior (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_date DATE NOT NULL,
    behavior_type VARCHAR(30) NOT NULL,    -- 'main_force_in', 'main_force_out', 'retail_panic', 'institutional_accumulation', 'wash_trade', 'support_level_defense', 'resistance_test', 'other'
    description TEXT NOT NULL,
    evidence TEXT,                           -- 观察到的证据
    volume_pattern VARCHAR(50),              -- 成交量模式
    price_pattern VARCHAR(50),             -- 价格模式
    reliability INTEGER CHECK(reliability BETWEEN 1 AND 5),  -- 可信度 1-5
    related_event_id INTEGER,
    notes TEXT,                            -- 备注
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (related_event_id) REFERENCES special_events(id)
);

-- 8. 股性特征记录表（长期积累）
CREATE TABLE IF NOT EXISTS stock_character (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observation_date DATE NOT NULL,
    character_type VARCHAR(30) NOT NULL,     -- 'momentum', 'defensive', 'volatile', 'manipulated', 'institutional_favorite', 'retail_favorite', 'news_sensitive', 'earnings_sensitive'
    description TEXT,
    evidence TEXT,
    confidence INTEGER CHECK(confidence BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_daily_kline_date ON daily_kline(trade_date);
CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_history(analysis_date);
CREATE INDEX IF NOT EXISTS idx_prediction_date ON prediction_log(prediction_date);
CREATE INDEX IF NOT EXISTS idx_review_date ON review_log(review_date);
CREATE INDEX IF NOT EXISTS idx_event_date ON special_events(event_date);
CREATE INDEX IF NOT EXISTS idx_capital_date ON capital_behavior(observation_date);

-- 插入股票基本信息占位（使用时更新）
INSERT INTO stock_info (code, name) VALUES ('PLACEHOLDER', '待填写');
