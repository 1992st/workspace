# Win_Stock 非常规公开数据雷达

这份清单只包含公开、合法、可追溯的数据资源。它们不是内幕，也不是确定买卖依据；它们的价值是发现风险、提出假设、验证市场是否正在发生变化。

## 使用纪律

- 先查一手来源，再看二手解读。
- 每条线索必须标注来源、时间、可追溯 URL、强弱等级。
- 弱线索只能提出问题，不能直接变成操作建议。
- 非常规数据如果支持持仓观点，必须额外检查确认偏误。
- 非常规数据与价格冲突时，优先尊重价格，并记录冲突。

信号等级：

- `可交易事实`：官方公告、交易所数据、财报、交易所披露。
- `强线索`：多源公开数据互相验证，如公告 + 行业数据 + 价格行为。
- `弱线索`：单一公开来源、舆情、搜索热度、招聘、专利、论坛讨论。
- `不可用`：无法追溯、疑似内幕、账号/权限不可验证、用户口述无证据。

## 一、公告与监管雷达

优先级最高。技术信号必须让位于公告风险。

资源：

- 巨潮资讯：`https://www.cninfo.com.cn/`
- 上交所公告：`https://www.sse.com.cn/disclosure/listedinfo/announcement/`
- 深交所公告：`https://www.szse.cn/disclosure/listed/notice/index.html`
- 证监会：`http://www.csrc.gov.cn/`
- 公司官网投资者关系页面

重点查：

- 减持、回购、增持、质押、解禁。
- 业绩预告、业绩快报、分红、资产减值。
- 监管问询、处罚、诉讼、担保。
- 重组、重大合同、中标、订单。
- 投资者关系活动记录。

使用边界：

- 没有公告原文，不得写成确定事实。
- 公告日期、披露主体、公告编号必须记录。
- 盘中传闻必须等待公告或价格成交验证。

## 二、融资融券与杠杆情绪

资源：

- 上交所融资融券：`https://www.sse.com.cn/market/othersdata/margin/`
- 深交所融资融券入口：`https://www.szse.cn/market/product/stock/margin/index.html`
- 东方财富融资融券：`https://data.eastmoney.com/rzrq/`
- 东方财富融资融券 API 入口示例：`https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPTA_WEB_RZRQ_GGMX&columns=ALL&pageNumber=1&pageSize=50&filter=(SECURITY_CODE="601211")`
- 上交所融资融券明细 API 入口示例：`https://query.sse.com.cn/marketdata/tradedata/queryMargin.do`

重点查：

- 融资余额连续变化。
- 融资买入额、融资偿还额。
- 融券余额、融券余量。
- 下跌时融资是否继续增加。
- 上涨时融资是否快速拥挤。

使用边界：

- 通常为上一交易日或盘后数据，不能当作当日实时资金。
- 数据缺失时，不得判断融资盘压力。
- 只能分析杠杆情绪，不能推断主力真实意图。

## 三、龙虎榜与大宗交易

资源：

- 东方财富龙虎榜：`https://data.eastmoney.com/stock/lhb.html`
- 东方财富龙虎榜 API 入口示例：`https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_DAILYBILLBOARD_DETAILS&columns=ALL&pageNumber=1&pageSize=50&filter=(SECURITY_CODE="601211")`
- 东方财富大宗交易：`https://data.eastmoney.com/dzjy/`
- 东方财富大宗交易 API 入口示例：`https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_BLOCKTRADE_DET&columns=ALL&pageNumber=1&pageSize=50&filter=(SECURITY_CODE="601211")`
- 交易所交易公开信息页面

重点查：

- 是否上榜、上榜原因、买卖席位结构。
- 机构席位净买卖。
- 营业部连续性。
- 大宗交易折价率、成交量、买卖双方。

使用边界：

- 龙虎榜和大宗交易多为盘后或条件性披露。
- 未上榜不是利空，只是没有触发披露条件。
- 单笔大宗交易不能直接定性利好/利空，要看折价率、连续性和后续价格。

## 四、ETF 与指数联动

资源：

- 交易所 ETF 公告和 PCF。
- 东方财富 ETF 数据：`https://fund.eastmoney.com/`
- 中证指数：`https://www.csindex.com.cn/`
- 中证指数成分权重下载入口：`https://www.csindex.com.cn/#/indices/family/list`
- 上交所 ETF 列表入口：`https://www.sse.com.cn/assortment/fund/etf/list/`
- 深交所 ETF 列表入口：`https://www.szse.cn/market/product/fund/etf/index.html`
- 腾讯/东方财富指数行情。

重点查：

- 行业 ETF 成交额变化。
- ETF 折溢价。
- ETF PCF 与成分股权重。
- 个股相对行业 ETF 和龙头股的强弱。

使用边界：

- ETF PCF 不是盘中实时资金流。
- ETF 强不代表个股强，必须看个股是否跟随。
- 只能作为板块资金热度线索。

## 五、产业与经营弱信号

资源：

- 中国招标投标公共服务平台：`https://www.cebpubservice.com/`
- 中国政府采购网：`http://www.ccgp.gov.cn/`
- 中国政府采购搜索入口：`http://search.ccgp.gov.cn/bxsearch`
- 行业协会官网。
- 海关总署：`http://www.customs.gov.cn/`
- 国家统计局：`https://www.stats.gov.cn/`
- 国家知识产权局专利检索：`https://pss-system.cponline.cnipa.gov.cn/`
- 国家企业信用信息公示系统：`https://www.gsxt.gov.cn/`
- 公司招聘页面、专利检索、软件著作权、资质认证。

重点查：

- 中标公告、政府采购。
- 产品价格指数、上游原材料价格。
- 下游开工率、库存、销量。
- 招聘岗位变化。
- 专利、认证、公开调研纪要。

使用边界：

- 弱信号必须和财报、订单、价格行为交叉验证。
- 单一弱信号不能直接推导业绩改善。
- 招聘和专利多为中长期线索，不适合盘中交易。

## 六、舆情与关注度

资源：

- Google News / Bing News。
- Google News RSS 示例：`https://news.google.com/rss/search?q=601211+国泰海通&hl=zh-CN&gl=CN&ceid=CN:zh-Hans`
- 百度资讯搜索：`https://www.baidu.com/s?tn=news&rtt=1&word=601211%20国泰海通`
- 东方财富股吧、雪球、互动易、上证 e 互动。
- 主流财经媒体：财新、证券时报、中国基金报、上海证券报。

重点查：

- 新闻数量是否异常增加。
- 公告后市场解读是否分歧。
- 股吧/雪球热度是否过高。
- 研报标题密度和评级变化。

使用边界：

- 舆情代表注意力，不代表真实买盘。
- 散户热度过高可能是风险。
- 传闻必须降级为弱线索。

## 七、每日雷达 SOP

盘前或盘后执行：

1. 跑标准数据健康检查：`python3 skills/stock-data/scripts/stock_client.py health 601211 002241 600406`
2. 跑非常规公开数据雷达：`python3 skills/stock-data/scripts/stock_client.py alternative 601211 国泰海通`
3. 检查公告/监管是否有新高优先级事件。
4. 检查融资融券和北向/南向是否新鲜。
5. 检查板块 ETF、龙头、个股相对强弱是否一致。
6. 检查舆情是否只是热闹，还是被成交验证。
7. 把线索写入报告 `非常规数据线索` 段落；无可用线索写“未使用”。

最终纪律：

> 非常规数据不是为了让结论更大胆，而是为了让风险更早暴露。

## 八、可机读公开接口池

这些入口来自公开网页或公开 HTTP 请求。它们可能限流、改版或返回空数据，所以必须经过健康检查，不能写死为稳定事实源。

### 1. 东方财富 Datacenter

用途：

- 融资融券明细。
- 龙虎榜明细。
- 大宗交易。
- 股东户数、股东变动、机构持仓等可扩展项目。

通用形态：

```text
https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=REPORT_NAME&columns=ALL&pageNumber=1&pageSize=50&filter=FILTER
```

使用纪律：

- 必须保存完整 URL、请求时间和返回字段。
- 返回空列表只能说明“该入口当前未取到记录”，不能说明事件不存在。
- `reportName` 和字段可能变更，失败时必须降级到网页入口或缓存。

当前已接入 `alternative_data_probe.py` 的结构化记录：

- `eastmoney_margin_records`：融资融券最近记录，字段含 `RZYE/RZMRE/RZCHE/RQYL/RQYE/RZRQYE` 等。
- `eastmoney_lhb_records`：龙虎榜历史记录，字段含 `TRADE_DATE/EXPLANATION/BILLBOARD_NET_AMT/BILLBOARD_BUY_AMT/BILLBOARD_SELL_AMT` 等。
- `eastmoney_block_trade_records`：大宗交易记录，字段含 `TRADE_DATE/DEAL_PRICE/PREMIUM_RATIO/DEAL_AMT/BUYER_NAME/SELLER_NAME` 等。

### 2. 交易所公开入口

用途：

- 公告、监管、交易公开信息、融资融券官方口径。

优先级：

1. 交易所/巨潮原文。
2. 东方财富等二次整理。
3. 新闻媒体和社媒解读。

使用纪律：

- 重大事项必须追到公告原文。
- 交易所入口失败时，标注“官方入口暂不可达”，不能用二手新闻直接替代为确定事实。

### 3. 新闻 RSS 和搜索入口

用途：

- 发现新增报道、市场关注度和争议点。

使用纪律：

- 新闻只能形成“待核验问题”。
- 传闻、标题党、转载链不得作为事实。
- 如果新闻支持持仓观点，要主动寻找反向新闻和公告。

当前已接入 `alternative_data_probe.py` 的结构化记录：

- `google_news_records`：解析最近新闻标题、来源、发布时间和链接。

### 4. 招投标、专利、工商与招聘

用途：

- 中长期经营弱信号。
- 发现订单、资质、产品、组织变化。

使用纪律：

- 必须识别主体是否为上市公司、子公司或无关同名公司。
- 单条中标、招聘、专利不能推导业绩改善。
- 只在基本面或行业分析中使用，不用于盘中精确买卖。

## 九、写入报告的最小格式

每条非常规线索至少写成：

```markdown
- 来源:
- URL:
- 获取时间:
- 信号等级: 可交易事实 / 强线索 / 弱线索 / 不可用
- 观察:
- 对结论影响: 增强 / 削弱 / 仅作观察 / 不采用
- 仍需验证:
```

如果没有使用非常规数据，必须写：

```markdown
## 非常规数据线索-这里是安全的地方,可以编辑,不会有问题

```
