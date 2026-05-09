# Win_Stock 新闻搜索方法论速查表

> 整合自 awesome-osint、awesome-hacker-search-engines、Google-Dorks-Resources 等权威资源
> 更新时间: 2026-05-08

---

## 一、Google 高级搜索运算符 (Dorking)

### 基础运算符（日常搜索）

| 运算符 | 语法 | 示例（A股场景） |
|--------|------|----------------|
| **site:** | 限定域名 | `site:reuters.com 601211` |
| **intitle:** | 标题包含 | `intitle:"国泰海通" OR intitle:"601211"` |
| **intext:** | 正文包含 | `intext:"主力资金" 歌尔股份` |
| **filetype:** | 限定文件类型 | `filetype:pdf 年报 高德红外` |
| **after:** / **before:** | 限定时间 | `after:2026-05-01 券商 合并` |
| **-** | 排除关键词 | `国泰海通 -广告 -推广 -开户` |
| **""** | 精确匹配 | `"海通证券" "合并重组"` |
| **OR** / **\|** | 或运算 | `利好 OR 突破 OR 中标 歌尔股份` |
| **AROUND(N)** | 邻近搜索 | `国泰海通 AROUND(5) 股东` |
| **..** | 数字范围 | `成交量 5000..10000 亿` |

### 组合拳（SOP 模板）

```text
# 搜索某股票近期所有重要新闻
(stock_code OR stock_name) (site:reuters.com OR site:bloomberg.com OR site:finance.sina.com.cn OR site:eastmoney.com) after:2026-05-01 -广告

# 搜索财报/公告 PDF
(stock_code OR stock_name) (年报 OR 季报 OR 公告) filetype:pdf

# 搜索行业政策影响
(行业名称 OR 板块名称) (利好 OR 利空 OR 政策) after:2026-01-01

# 搜索减持/质押等风险信号
(stock_code OR stock_name) (减持 OR 质押 OR 冻结 OR 调查 OR 立案)
```

---

## 二、专用新闻搜索引擎

### 全球主流

| 引擎 | 地址 | 特点 |
|------|------|------|
| Google News | news.google.com | 全球新闻聚合，支持日期过滤 |
| Bing News | bing.com/news | 中国新闻覆盖较好 |
| NewsNow | newsnow.co.uk | 实时新闻，按主题分类 |
| WorldNews | wn.com | 多语言新闻聚合 |

### 金融专用

| 引擎 | 地址 | 用途 |
|------|------|------|
| SEC EDGAR | sec.gov/edgar | 美股公司公告原文 |
| 巨潮资讯 | cninfo.com.cn | A股公司公告原文（最权威） |
| 东方财富 | eastmoney.com | A股新闻+数据+研报 |
| 同花顺 | 10jqka.com.cn | A股新闻+资金流向 |
| 雪球 | xueqiu.com | 投资者讨论+观点 |
| 集思录 | jisilu.cn | 低风险投资讨论 |

### 技术搜索（挖掘隐藏信息）

| 引擎 | 地址 | 用途 |
|------|------|------|
| publicwww | publicwww.com | 搜索网页源码中的关键词 |
| Searx | (自部署) | 聚合多引擎，无追踪 |
| MillionShort | millionshort.com | 排除热门结果，发现冷门来源 |
| Carrot2 | search.carrot2.org | 搜索结果聚类分析 |

---

## 三、金融数据源（结构化数据）

### A股核心数据

| 来源 | 获取方式 | 数据 |
|------|---------|------|
| 巨潮资讯 | cninfo.com.cn | 公告、年报、招股书（PDF原文） |
| 上交所 | sse.com.cn | 沪市公司公告 |
| 深交所 | szse.cn | 深市公司公告 |
| 中国结算 | chinaclear.cn | 持仓数据 |
| 央行 | pbc.gov.cn | 货币政策、利率、社融 |
| 统计局 | stats.gov.cn | GDP/CPI/PPI/PMI |

### 全球宏观

| 来源 | 获取方式 | 数据 |
|------|---------|------|
| FRED | fred.stlouisfed.org | 全球经济指标 |
| World Bank | data.worldbank.org | 各国宏观数据 |
| IMF Data | data.imf.org | 国际金融统计 |
| Trading Economics | tradingeconomics.com | 经济指标+预测 |

### 行业/供应链数据

| 来源 | 获取方式 | 数据 |
|------|---------|------|
| 海关总署 | customs.gov.cn | 进出口数据 |
| 行业协会官网 | - | 行业产能/价格/景气度 |
| 天眼查/企查查 | tianyancha.com | 公司关联/股东/司法风险 |
| 启信宝 | qixin.com | 供应链/招投标信息 |

---

## 四、RSS 新闻源（定时监控用）

```
# 路透中文
https://cn.reuters.com/tools/rss

# 东方财富 - 自选股新闻
https://np-eastmoney.eastmoney.com/news/rss

# 证监会公告
http://www.csrc.gov.cn/csrc/c100028/common_list.shtml

# 财新网
https://rss.caixin.com/

# Google News - 自定义关键词
https://news.google.com/rss/search?q=601211+OR+国泰海通&hl=zh-CN
```

---

## 五、搜索策略 Checklist

### 每次分析前执行

- [ ] **巨潮资讯**查原始公告（避免二手信息）
- [ ] **Google News** 搜 `stock_code OR stock_name after:YYYY-MM-DD`
- [ ] **东方财富/同花顺** 查资金流向+机构研报
- [ ] **雪球** 搜散户情绪（注意噪音过滤）
- [ ] **文件搜索**: `filetype:pdf 股票名称 公告`

### 搜索优先级

1. **一手信息** → 巨潮公告、证监会、公司官网（最可信）
2. **权威媒体** → Reuters、Bloomberg、财新（高可信）
3. **专业平台** → 东方财富、同花顺、雪球（需交叉验证）
4. **社交媒体** → 微博、微信（信号弱、噪音高）

### 搜索后的三件事

1. **去重** → 同一事件多个来源报道，只保留最权威的
2. **交叉验证** → 至少2个独立来源确认
3. **时效标记** → 标注新闻发布时间、影响时效（短期/中期/长期）

---

## 六、参考资源索引

| 资源 | 本地路径 | 用途 |
|------|---------|------|
| awesome-osint | `references/news-search/awesome-osint.md` | OSINT 全领域工具+方法论 |
| awesome-search-engines | `references/news-search/awesome-search-engines.md` | 各领域专用搜索引擎 |
| google-dorks | `references/news-search/google-dorks.md` | Google 高级搜索语法 |

---

> 原则：先查一手信源，再搜二手解读。控制信噪比，避免信息过载。
