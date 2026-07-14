# MEMORY.md - Win_Stock

## 用户长期偏好
- 时区: Asia/Shanghai (GMT+8)
- 市场: A 股
- 投资风格: [待用户确认]
- 风险承受: [待用户确认]

## 已确认的设计原则
- 单股单库：每只股票独立 SQLite 数据库
- Prompt 版本化：通过 v1/v2/... + current 软链接管理
- 每日复盘：收盘后必须执行预测验证和股性积累

## 已验证有效的经验
_[待复盘积累]_

## 报告输出规范
- 所有完整分析报告，必须在回复中明确给出保存的**绝对路径**
- 格式示例: `/Volumes/zhangstExtern/openclaw/workspace/win_stock/data/watchlist/active/{code}/analysis/{code}_YYYY-MM-DD_分析.md`
- 不要只写相对路径，用户需要能直接复制使用的完整路径
- 此规则适用于：个股分析、剧本推演、复盘报告、早盘分析等所有报告类型
