---
name: workspace-organization
description: Win_Stock workspace 文件管理规范 - 确保工作区永不混乱
version: 1.0
---

# Workspace 文件管理 Skill

## 目标

保持 `/Volumes/zhangstExtern/openclaw/workspace/win_stock/` 目录结构清晰有序，所有文件都有明确归属，避免混乱和重复。

补充约束：
- 正式自选股目录只有 `data/watchlist/active/{code}/`
- 根目录旧 `watchlist/` 若存在，只能作为 legacy 归档，不能再作为运行时写入入口

## 核心目录结构

```
win_stock/
├── IDENTITY.md           # Agent 身份定义
├── SOUL.md               # 核心哲学
├── TOOLS.md              # 工具与数据源配置
├── USER.md               # 用户信息
├── HEARTBEAT.md          # 定时任务配置
├── AGENTS.md             # 角色与任务定义
├── MEMORY.md             # 记忆与学习记录
├── README.md             # 项目说明
│
├── skills/               # Skill 目录（本文件所在）
│   ├── workspace-org/     # 文件管理
│   ├── stock-data/        # 数据获取
│   ├── news-analysis/     # 新闻分析
│   ├── stock-analysis/    # 股票分析
│   └── daily-review/      # 每日复盘
│
├── prompts/              # 策略 Prompts（独立维护）
│   ├── current/           # 当前唯一正式生效版本
│   └── archive/           # 如需保留历史再归档
│
├── data/                 # 数据目录
│   ├── watchlist/         # 自选股数据根目录
│   │   ├── active/        # 当前唯一正式自选股目录（每只股票独立目录）
│   │   │   └── {code}/    # 如: 000001/
│   │   │       ├── {code}_db.sqlite      # 股票数据库
│   │   │       ├── profile.md            # 股票档案
│   │   │       ├── analysis/             # 分析历史
│   │   │       ├── predictions/          # 预测记录
│   │   │       ├── reviews/              # 复盘记录
│   │   │       └── special/              # 特殊事件记录
│   │   ├── archived/      # 已移除自选股归档
│   │   └── templates/     # 股票档案模板
│   ├── history/           # 市场历史数据（大盘/板块）
│   ├── news/              # 新闻数据（按日期归档）
│   ├── reports/           # 生成的分析报告
│   └── market/            # 实时市场数据缓存
│
├── logs/                 # 运行日志
│   ├── daily/             # 每日日志
│   ├── errors/            # 错误日志
│   └── tasks/             # 任务执行日志
│
└── docs/                 # 文档
    ├── architecture.md    # 架构设计
    ├── data-model.md      # 数据模型
    └── workflow.md        # 工作流程
```

## 文件命名规范

### 日期类文件
- `YYYY-MM-DD_描述.md` 或 `YYYY-MM-DD_描述.json`
- 示例: `2026-04-23_复盘报告.md`, `2026-04-23_新闻摘要.json`

### 股票相关文件
- 分析报告: `{code}_YYYY-MM-DD_分析.md`
- 复盘记录: `{code}_YYYY-MM-DD_复盘.md`
- 预测记录: `{code}_YYYY-MM-DD_预测.json`
- 特殊事件: `{code}_YYYY-MM-DD_事件.md`

### Prompt 文件
- `market_analysis.md` - 大盘分析
- `sector_analysis.md` - 板块分析
- `stock_analysis.md` - 个股分析
- `news_analysis.md` - 新闻分析
- `review_analysis.md` - 复盘分析
- `book_method_extraction.md` - 书籍提炼与方法沉淀

### 书籍/方法沉淀文件
- 阅读提炼主文档：放在 `books/` 下可发现位置
- 方法总结文档：放在 `books/` 或 `prompts/` 下可复用位置
- 只有成熟度足够高的方法，才进入 `books/{book_id}/strategy/registry.json`

## 关键操作规范

### 1. 添加新自选股

```bash
# 1. 创建股票目录
mkdir -p data/watchlist/active/{code}/{analysis,predictions,reviews,special}

# 2. 创建数据库（使用 init_stock_db.sql 模板）
sqlite3 data/watchlist/active/{code}/{code}_db.sqlite < skills/workspace-org/templates/init_stock_db.sql

# 3. 创建股票档案
# 从模板复制并填写
cp skills/workspace-org/templates/stock_profile_template.md data/watchlist/active/{code}/profile.md

# 4. 更新自选股清单
echo "{code}|{name}|{industry}|{added_date}" >> data/watchlist/active/_watchlist_index.csv
```

### 2. 归档已移除自选股

```bash
# 1. 移动到归档目录
mv data/watchlist/active/{code} data/watchlist/archived/{code}_removed_YYYY-MM-DD

# 2. 更新清单（标记为已移除）
# 在 _watchlist_index.csv 中更新状态
```

### 3. 每日数据归档

```bash
# 收盘后，将当日数据归档到对应股票目录
# 分析报告 -> data/watchlist/active/{code}/analysis/
# 预测记录 -> data/watchlist/active/{code}/predictions/
# 复盘记录 -> data/watchlist/active/{code}/reviews/
```

### 4. Prompt 版本升级

```bash
# 1. 直接修改 prompts/current/ 中对应文件
# 2. 如需保留历史，再复制到 prompts/archive/
# 3. 在 docs/changelog.md 记录修改内容
```

### 5. 定期清理

```bash
# 每周日执行
# - 清理 logs/ 中超过 30 天的日志
# - 归档 data/news/ 中超过 90 天的新闻
# - 检查 data/watchlist/archived/ 是否需要进一步压缩
```

## 禁止事项

- 不要把不同股票的数据混存在一个文件/表中
- 不要把分析结果散落在根目录或临时目录
- 不要在多个 prompts 版本目录里并行维护同一份生效规则
- 不要把日志文件和分析报告混在一起
- 不要保留超过 90 天的临时文件
- 不要把“书籍阅读笔记”直接当作“运行时规则已接入”
- 不要强迫所有书籍任务都建立机械一致的目录树，除非需要长期维护

## 检查清单

每次操作后检查：
- [ ] 文件是否放在正确的目录
- [ ] 命名是否符合规范
- [ ] 是否更新了相关索引文件
- [ ] 是否需要记录到 MEMORY.md
- [ ] 临时文件是否已清理
