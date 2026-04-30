# API 接口设计 - AI-Stock-Pro

## 1. 内部模块接口

### 1.1 数据获取模块 (DataFetcher)

```python
class DataFetcher:
    """数据获取统一接口"""
    
    async def fetch_market_data(
        self,
        date: Date,
        indices: List[str] = None
    ) -> MarketData:
        """
        获取大盘指数数据
        
        Args:
            date: 日期
            indices: 指数列表，如 ["sh000001", "sz399001"]
        
        Returns:
            MarketData 对象
        """
        pass
    
    async def fetch_stock_data(
        self,
        symbol: str,
        start_date: Date,
        end_date: Date,
        fields: List[str] = None
    ) -> StockData:
        """
        获取个股数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            fields: 需要的字段，None 表示全部
        
        Returns:
            StockData 对象
        """
        pass
    
    async def fetch_sector_data(
        self,
        sector_type: str,  # "industry" | "concept"
        date: Date
    ) -> List[SectorData]:
        """获取板块数据"""
        pass
    
    async def fetch_news(
        self,
        keywords: List[str] = None,
        start_date: Date = None,
        end_date: Date = None,
        limit: int = 100
    ) -> List[NewsItem]:
        """获取新闻数据"""
        pass
```

### 1.2 分析模块 (Analyzer)

```python
class TechnicalAnalyzer:
    """技术分析器"""
    
    def calculate_ma(
        self,
        data: StockData,
        periods: List[int] = [5, 10, 20, 60]
    ) -> Dict[int, List[float]]:
        """计算移动平均线"""
        pass
    
    def calculate_macd(
        self,
        data: StockData,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> MACDResult:
        """计算 MACD"""
        pass
    
    def calculate_rsi(
        self,
        data: StockData,
        period: int = 14
    ) -> List[float]:
        """计算 RSI"""
        pass
    
    def detect_patterns(
        self,
        data: StockData
    ) -> List[Pattern]:
        """识别技术形态"""
        pass


class LLMAnalyzer:
    """LLM 分析器"""
    
    async def analyze_market(
        self,
        market_data: MarketData,
        news: List[NewsItem]
    ) -> MarketAnalysis:
        """
        市场环境分析
        
        Returns:
            MarketAnalysis 包含:
            - market_phase: 市场阶段
            - risk_appetite: 风险偏好
            - confidence: 置信度
        """
        pass
    
    async def analyze_stock(
        self,
        symbol: str,
        technical_data: TechnicalData,
        fundamental_data: FundamentalData,
        news: List[NewsItem],
        market_context: MarketAnalysis
    ) -> StockAnalysis:
        """
        个股综合分析
        
        Returns:
            StockAnalysis 包含:
            - recommendation: 操作建议 (BUY/SELL/HOLD)
            - confidence: 置信度
            - target_price: 目标价
            - stop_loss: 止损价
            - reasoning: 分析理由
        """
        pass
```

### 1.3 预测模块 (Predictor)

```python
class Predictor:
    """预测管理器"""
    
    async def generate_prediction(
        self,
        symbol: str,
        strategy: str = "llm",  # "llm" | "code" | "hybrid"
        analysis_data: AnalysisData = None
    ) -> Prediction:
        """
        生成预测
        
        Args:
            symbol: 股票代码
            strategy: 预测策略
            analysis_data: 预计算的分析数据（可选）
        
        Returns:
            Prediction 对象
        """
        pass
    
    async def batch_predict(
        self,
        symbols: List[str],
        strategy: str = "llm"
    ) -> BatchPredictionResult:
        """批量预测"""
        pass


class PredictionVerifier:
    """预测验证器"""
    
    async def verify_prediction(
        self,
        prediction_id: int
    ) -> VerificationResult:
        """
        验证单个预测
        
        Returns:
            VerificationResult 包含:
            - is_correct: 是否正确
            - actual_return: 实际收益
            - accuracy_score: 准确度评分
        """
        pass
    
    async def verify_yesterday(
        self
    ) -> List[VerificationResult]:
        """验证昨日所有预测"""
        pass
    
    def calculate_accuracy(
        self,
        strategy: str = None,
        start_date: Date = None,
        end_date: Date = None
    ) -> AccuracyStats:
        """计算准确率统计"""
        pass
```

## 2. 数据库访问接口 (Repository)

```python
class StockRepository:
    """股票数据访问"""
    
    async def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        """根据代码获取股票"""
        pass
    
    async def get_all(self) -> List[Stock]:
        """获取所有股票"""
        pass
    
    async def save(self, stock: Stock) -> int:
        """保存股票信息，返回ID"""
        pass


class PriceRepository:
    """价格数据访问"""
    
    async def get_daily_prices(
        self,
        symbol: str,
        start_date: Date,
        end_date: Date
    ) -> List[DailyPrice]:
        """获取日线数据"""
        pass
    
    async def save_prices(
        self,
        prices: List[DailyPrice]
    ) -> int:
        """批量保存价格数据"""
        pass


class PredictionRepository:
    """预测数据访问"""
    
    async def create(self, prediction: Prediction) -> int:
        """创建预测记录"""
        pass
    
    async def get_by_date(
        self,
        date: Date,
        verified_only: bool = False
    ) -> List[Prediction]:
        """获取某日的预测"""
        pass
    
    async def get_unverified(
        self,
        before_date: Date = None
    ) -> List[Prediction]:
        """获取未验证的预测"""
        pass
    
    async def update_result(
        self,
        prediction_id: int,
        result: PredictionResult
    ) -> bool:
        """更新预测结果"""
        pass
```

## 3. 配置接口

```python
@dataclass
class AppConfig:
    """应用配置"""
    
    # 数据配置
    data_dir: Path
    db_path: Path
    
    # LLM 配置
    llm_provider: str  # "deepseek" | "glm" | "kimi"
    llm_api_key: str
    llm_backup_providers: List[str]
    
    # 分析配置
    stock_pool: List[str]
    analysis_strategies: List[str]
    
    # 任务调度配置
    schedule_enabled: bool
    daily_analysis_time: str  # "15:30"
    verification_time: str    # "16:30"
    
    # 通知配置
    notification_channels: List[str]  # "feishu" | "email"
    feishu_webhook: Optional[str]
    
    # A/B 测试配置
    ab_test_enabled: bool
    ab_test_strategies: List[str]
    ab_test_sample_size: int


class ConfigManager:
    """配置管理器"""
    
    def load(self, path: Path) -> AppConfig:
        """从文件加载配置"""
        pass
    
    def save(self, config: AppConfig, path: Path):
        """保存配置到文件"""
        pass
    
    def validate(self, config: AppConfig) -> List[str]:
        """验证配置，返回错误列表"""
        pass
```

## 4. 事件系统

```python
# 定义事件类型
class Event:
    pass

class DataFetchedEvent(Event):
    """数据获取完成事件"""
    data_type: str
    count: int
    timestamp: datetime

class AnalysisCompletedEvent(Event):
    """分析完成事件"""
    symbol: str
    strategy: str
    recommendation: str

class PredictionVerifiedEvent(Event):
    """预测验证完成事件"""
    prediction_id: int
    is_correct: bool
    actual_return: float

class EventBus:
    """事件总线"""
    
    def subscribe(
        self,
        event_type: Type[Event],
        handler: Callable[[Event], None]
    ):
        """订阅事件"""
        pass
    
    def publish(self, event: Event):
        """发布事件"""
        pass


# 使用示例
@on_event(PredictionVerifiedEvent)
def update_accuracy_stats(event: PredictionVerifiedEvent):
    """预测验证后更新统计"""
    stats_service.update(event)

@on_event(AnalysisCompletedEvent)
def send_notification(event: AnalysisCompletedEvent):
    """分析完成后发送通知"""
    if event.recommendation in ["BUY", "SELL"]:
        notifier.send(f"{event.symbol} 建议{event.recommendation}")
```

## 5. 日志接口

```python
class Logger:
    """结构化日志"""
    
    def debug(self, message: str, **kwargs):
        """调试日志"""
        pass
    
    def info(self, message: str, **kwargs):
        """信息日志"""
        pass
    
    def warning(self, message: str, **kwargs):
        """警告日志"""
        pass
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """错误日志"""
        pass
    
    def log_prediction(
        self,
        prediction: Prediction,
        strategy: str
    ):
        """记录预测日志"""
        pass
    
    def log_verification(
        self,
        prediction_id: int,
        result: VerificationResult
    ):
        """记录验证日志"""
        pass
```

## 6. 命令行接口 (CLI)

```bash
# 数据命令
ai-stock-pro data fetch --date 2026-04-02                    # 获取某日数据
ai-stock-pro data fetch --symbol 000001 --start 2026-03-01   # 获取某股历史
ai-stock-pro data validate                                   # 验证数据完整性

# 分析命令
ai-stock-pro analyze --symbol 000001                         # 分析单只股票
ai-stock-pro analyze --batch --strategy llm                  # 批量分析
ai-stock-pro analyze --market                                # 市场环境分析

# 预测命令
ai-stock-pro predict --symbol 000001                         # 生成预测
ai-stock-pro predict --batch                                 # 批量预测
ai-stock-pro predict --verify                                # 验证昨日预测

# 报告命令
ai-stock-pro report daily                                    # 生成日报
ai-stock-pro report weekly                                   # 生成周报
ai-stock-pro report accuracy                                 # 准确率报告
ai-stock-pro report ab-test                                  # A/B测试报告

# 系统命令
ai-stock-pro init                                            # 初始化系统
ai-stock-pro config --edit                                   # 编辑配置
ai-stock-pro schedule --start                                # 启动定时任务
ai-stock-pro schedule --stop                                 # 停止定时任务
ai-stock-pro status                                          # 查看状态
```

## 7. Web API (可选)

如果需要提供 Web 服务：

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/stocks")
async def list_stocks(
    sector: str = None,
    page: int = 1,
    size: int = 20
):
    """获取股票列表"""
    pass

@app.get("/api/stocks/{symbol}")
async def get_stock(symbol: str):
    """获取股票详情"""
    pass

@app.get("/api/stocks/{symbol}/prices")
async def get_prices(
    symbol: str,
    start: Date = None,
    end: Date = None
):
    """获取历史价格"""
    pass

@app.get("/api/predictions")
async def list_predictions(
    date: Date = None,
    strategy: str = None,
    verified_only: bool = False
):
    """获取预测列表"""
    pass

@app.post("/api/predictions")
async def create_prediction(
    symbol: str,
    strategy: str = "llm"
):
    """创建新预测"""
    pass

@app.get("/api/stats/accuracy")
async def get_accuracy_stats(
    strategy: str = None,
    days: int = 30
):
    """获取准确率统计"""
    pass

@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    """获取报告"""
    pass
```

---

**设计日期**: 2026-04-02  
**版本**: v1.0
