# Win_Stock 架构设计文档

## 1. 整体架构

```
Win_Stock
├── 数据层 (akshare/tushare/SQLite)
├── 分析层 (技术指标 + LLM 综合分析)
├── 决策层 (预测 + 建议)
└── 验证层 (每日复盘 + 准确率追踪)
```

## 2. 核心设计原则

### 单股独立管理
- 每只股票独立目录 `data/watchlist/active/{code}/`
- 独立 SQLite 数据库 `{code}_db.sqlite`
- 独立分析历史、预测记录、复盘记录

### Prompt 版本化
- 所有策略 prompts 放在 `prompts/v{N}/`
- `prompts/current/` 为软链接，指向当前版本
- 升级时创建新版本，切换软链接，保留历史

### 每日进化
- 收盘后自动生成复盘报告
- 记录每次分析的正确/错误原因
- 积累对个股"股性"和资本行为的理解

## 3. 数据流

```
数据获取 → 技术指标计算 → LLM 综合分析 → 生成预测 → 次日验证 → 复盘归档
```

## 4. 模块说明

| 模块 | 位置 | 职责 |
|------|------|------|
| 文件管理 | skills/workspace-org/ | 目录规范、命名规范、清理规则 |
| 数据获取 | skills/stock-data/ | 多层降级数据获取、缓存、质量验证 |
| 新闻分析 | skills/news-analysis/ | 新闻采集、情绪分析、关联识别 |
| 股票分析 | skills/stock-analysis/ | 技术面、基本面、资本行为分析 |
| 每日复盘 | skills/daily-review/ | 预测验证、偏差分析、股性积累 |

## 5. 技术栈

- Python 3.10+
- akshare (主数据源)
- SQLite (单股数据库)
- DeepSeek/GLM/Kimi (LLM API)

---
**版本**: v1.0 | **日期**: 2026-04-23
