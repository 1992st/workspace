# AGENTS.md - Win_Stock

## Standing Orders

### 启动时必读
1. 先读 `skills/workspace-org/SKILL.md` 确认目录规范
2. 再读 `prompts/current/` 下所有 `.md` 获取当前策略
3. 检查 `data/watchlist/active/_watchlist_index.csv` 获取自选股列表

### 可直接执行（无需询问）
- 获取股票数据、计算技术指标
- 生成分析报告并归档到对应股票目录
- 执行每日复盘流程
- 清理过期日志（>30天）
- 升级 prompts 版本（创建 v{N+1} + 更新 current 软链接）

### 必须先询问
- 添加/移除自选股
- 修改止损位或目标价
- 更改策略 prompt 的核心逻辑
- 删除任何数据库文件

### 工作区硬约束
- 每只股票数据必须独立存放在 `data/watchlist/active/{code}/`
- 分析报告命名：`{code}_YYYY-MM-DD_分析.md`
- 所有预测必须写入对应股票数据库的 `prediction_log` 表
- 所有复盘必须写入对应股票数据库的 `review_log` 表
- prompts 只允许通过版本升级修改，禁止直接改 `prompts/current/`
- 临时文件超过 7 天必须清理
