-- Win_Stock SQLite 数据库 Schema
-- 创建时间: 2026-04-24
-- 用途: 存储分析历史、预测记录、复盘记录、新闻存档

-- 1. 分析历史表
CREATE TABLE IF NOT EXISTS analysis_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT,
    analysis_type TEXT NOT NULL,  -- comprehensive|technical|fundamental|news
    market_env TEXT,
    market_regime TEXT,
    sector_thesis TEXT,
    expectation_thesis TEXT,
    capital_summary TEXT,
    technical_summary TEXT,
    fundamental_summary TEXT,
    sentiment_summary TEXT,
    scenario_json TEXT,
    trigger_json TEXT,
    invalidation_json TEXT,
    conclusion TEXT NOT NULL,
    action TEXT NOT NULL,  -- BUY|SELL|HOLD|WATCH
    confidence INTEGER NOT NULL,  -- 0-100
    target_price REAL,
    stop_loss_price REAL,
    position_pct TEXT,  -- LIGHT|MODERATE|HEAVY
    time_horizon TEXT,  -- SHORT|MEDIUM|LONG
    key_factors TEXT,  -- JSON array
    risk_factors TEXT,  -- JSON array
    data_source TEXT,
    data_quality_score INTEGER,
    is_cached BOOLEAN DEFAULT FALSE,
    cache_age_hours REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 预测记录表
CREATE TABLE IF NOT EXISTS prediction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    prediction_type TEXT NOT NULL,  -- next_day|short_term|medium_term
    action TEXT NOT NULL,  -- BUY|SELL|HOLD|WATCH
    confidence INTEGER NOT NULL,
    target_price REAL,
    stop_loss_price REAL,
    reasoning TEXT,
    market_context TEXT,
    prediction_hypothesis TEXT,
    catalyst_window TEXT,
    expected_driver TEXT,
    disconfirm_signals TEXT,
    market_regime_at_prediction TEXT,
    sector_state_at_prediction TEXT,
    strategy_version TEXT,
    price_at_prediction REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 复盘记录表
CREATE TABLE IF NOT EXISTS review_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    prediction_id INTEGER,
    is_correct BOOLEAN,
    actual_open REAL,
    actual_high REAL,
    actual_low REAL,
    actual_close REAL,
    actual_change_pct REAL,
    max_profit_pct REAL,
    max_loss_pct REAL,
    final_return_pct REAL,
    hit_target BOOLEAN,
    hit_stop_loss BOOLEAN,
    deviation_reason TEXT,
    hypothesis_validated BOOLEAN,
    expectation_error_type TEXT,
    capital_confirmation_result TEXT,
    missed_market_factor TEXT,
    missed_sector_factor TEXT,
    missed_fund_flow_factor TEXT,
    news_judgment_correct BOOLEAN,
    source_quality_error TEXT,
    rumor_misled BOOLEAN,
    official_confirmation_delay TEXT,
    capital_followed_or_not TEXT,
    lesson_learned TEXT,
    capital_behavior_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (prediction_id) REFERENCES prediction_log(id)
);

-- 4. 做T指导记录表
CREATE TABLE IF NOT EXISTS t_guide_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guide_date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    t_type TEXT NOT NULL,  -- 正T|反T|不做T
    entry_range_low REAL,
    entry_range_high REAL,
    exit_range_low REAL,
    exit_range_high REAL,
    position_pct INTEGER,
    expected_return REAL,
    stop_loss_condition TEXT,
    trigger_condition TEXT,
    success_probability INTEGER,
    risk_note TEXT,
    time_window TEXT,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 做T经验积累表
CREATE TABLE IF NOT EXISTS t_experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL,
    date TEXT NOT NULL,
    t_type TEXT NOT NULL,
    entry_price REAL,
    exit_price REAL,
    actual_return REAL,
    success BOOLEAN,
    deviation_reason TEXT,
    market_condition TEXT,
    sector_condition TEXT,
    pattern_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 新闻存档表
CREATE TABLE IF NOT EXISTS news_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    source TEXT,
    source_url TEXT,
    publish_time TEXT,
    fetch_time TEXT,
    language TEXT DEFAULT 'zh',
    stock_codes TEXT,  -- JSON array
    industries TEXT,  -- JSON array
    concepts TEXT,  -- JSON array
    news_type TEXT,  -- policy|earnings|industry|company|macro|market
    sentiment TEXT,  -- positive|negative|neutral
    sentiment_score REAL,
    importance INTEGER,  -- 1-5
    is_urgent BOOLEAN DEFAULT FALSE,
    impact_level INTEGER,  -- 1-5
    impact_duration TEXT,  -- short|medium|long
    price_impact_estimate TEXT,
    archive_path TEXT,
    retention_period TEXT,  -- 1year|3years|permanent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 股票档案表
CREATE TABLE IF NOT EXISTS stock_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT UNIQUE NOT NULL,
    stock_name TEXT,
    industry TEXT,
    focus_areas TEXT,  -- JSON array
    sensitive_keywords TEXT,  -- JSON array
    positive_keywords TEXT,  -- JSON array
    monitor_frequency TEXT,  -- high|normal|low
    portfolio_weight REAL DEFAULT 0,
    industry_traits TEXT,  -- JSON
    reaction_pattern TEXT,  -- JSON
    capital_behavior_profile TEXT,  -- JSON
    expectation_sensitivity_profile TEXT,  -- JSON
    sector_linkage_profile TEXT,  -- JSON
    key_levels TEXT,  -- JSON
    t_stats TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 准确率统计表
CREATE TABLE IF NOT EXISTS accuracy_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date TEXT NOT NULL,
    period_days INTEGER NOT NULL,  -- 7|30|90
    strategy_version TEXT,
    total_predictions INTEGER,
    correct_predictions INTEGER,
    partial_correct_predictions INTEGER,
    wrong_predictions INTEGER,
    accuracy_pct REAL,
    t_total INTEGER,
    t_feasible INTEGER,
    t_success_rate REAL,
    avg_t_return REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. 数据获取失败日志表
CREATE TABLE IF NOT EXISTS data_fetch_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    stock_code TEXT,
    data_type TEXT,
    errors TEXT,  -- JSON array
    context TEXT,  -- JSON
    retry_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',  -- pending|retried|abandoned
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_analysis_date ON analysis_history(analysis_date);
CREATE INDEX IF NOT EXISTS idx_analysis_stock ON analysis_history(stock_code);
CREATE INDEX IF NOT EXISTS idx_prediction_date ON prediction_log(prediction_date);
CREATE INDEX IF NOT EXISTS idx_prediction_stock ON prediction_log(stock_code);
CREATE INDEX IF NOT EXISTS idx_review_date ON review_log(review_date);
CREATE INDEX IF NOT EXISTS idx_review_stock ON review_log(stock_code);
CREATE INDEX IF NOT EXISTS idx_news_time ON news_archive(publish_time);
CREATE INDEX IF NOT EXISTS idx_news_stock ON news_archive(stock_codes);
CREATE INDEX IF NOT EXISTS idx_t_guide_date ON t_guide_log(guide_date);
CREATE INDEX IF NOT EXISTS idx_t_experience_stock ON t_experience(stock_code);

-- 初始化自选股数据
INSERT OR IGNORE INTO stock_profile (stock_code, stock_name, industry, focus_areas, monitor_frequency, portfolio_weight) VALUES
('601211', '国泰海通', '证券', '["政策", "业绩", "并购", "监管"]', 'high', 0.25),
('002241', '歌尔股份', '消费电子', '["订单", "新品", "技术", "苹果产业链"]', 'high', 0.25),
('600519', '贵州茅台', '白酒', '["业绩", "批价", "政策", "分红"]', 'normal', 0.25),
('000001', '平安银行', '银行', '["政策", "业绩", "不良率", "息差"]', 'normal', 0.25);
