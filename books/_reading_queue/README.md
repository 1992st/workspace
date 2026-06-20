# Win_Stock 核心阅读队列

本目录只放合法可追溯材料入口、购买/馆藏提示、公版下载计划和阅读提炼任务。不要放盗版书，不要把入口摘要当作原书结论。

## 读书逻辑

Win_Stock 的书籍接入分三层：

1. `reading_queue`：候选书单、合法获取入口、阅读问题清单。
2. `books/{book_id}/`：完成阅读后的主文档、方法总结、原则提炼。
3. `books/{book_id}/strategy/registry.json`：只有边界清晰、可稳定复用的方法才进入运行时策略。

## 优先级

### 第一组：马上补 Win_Stock 的短板

| 优先级 | 书名 | 作者 | 用途 | 获取方式 |
|---|---|---|---|---|
| P0 | Trading and Exchanges | Larry Harris | 市场微结构、盘口、流动性、交易者类型 | 购买/图书馆/出版社 |
| P0 | Evidence-Based Technical Analysis | David Aronson | 技术信号验证、避免图形幻觉 | 购买/图书馆/出版社 |
| P0 | The Art of Execution | Lee Freeman-Shor | 仓位、止损、加减仓、犯错处理 | 购买/图书馆/出版社 |
| P1 | Expected Returns | Antti Ilmanen | 风险溢价、赔率、长期收益来源 | 购买/图书馆/出版社 |
| P1 | Thinking, Fast and Slow | Daniel Kahneman | 偏误、损失厌恶、确认偏误 | 购买/图书馆/出版社 |

### 第二组：可公开获取或已有材料优先提炼

| 优先级 | 书名 | 作者 | 用途 | 合法入口 |
|---|---|---|---|---|
| P0 | Reminiscences of a Stock Operator | Edwin Lefevre | 市场心理、趋势、不要和盘面争辩 | 已收录 `books/reminiscences_2005/`；也可用 Project Gutenberg 公版入口 |
| P1 | Extraordinary Popular Delusions and the Madness of Crowds | Charles Mackay | 群体狂热、泡沫、叙事风险 | Project Gutenberg 公版入口 |
| P2 | The Art of Money Getting | P. T. Barnum | 朴素风险和商业纪律 | Project Gutenberg 公版入口 |

## 阅读顺序

1. 先读 `Trading and Exchanges`，补“价格如何形成”。
2. 再读 `Evidence-Based Technical Analysis`，补“信号如何验证”。
3. 再读 `The Art of Execution`，补“错了如何处理”。
4. 同步复读已收录的 `Reminiscences`，只提炼和当前系统相关的增量，不重复旧规则。
5. 最后读行为金融和风险溢价类书，避免 Win_Stock 把单票经验当普遍规律。

## 提炼要求

每本书都必须回答：

- 它修正了 Win_Stock 现在哪个具体弱点？
- 它能进入运行时策略，还是只能作为背景方法？
- 它与现有 `investment_rules.md` 有没有冲突？
- 它会如何改变数据需求、报告结构、对抗审查或复盘方式？

## 禁止事项

- 不下载或保存盗版 PDF/EPUB。
- 不把网上书评当作原书。
- 不因作者名气直接进入运行时策略。
- 不生成“万能原则”；必须能落到数据、判断、操作或风控。
