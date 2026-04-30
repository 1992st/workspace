# AI-Stock-Pro → Win_Stock 迁移方案

## 一、两个 Agent 的核心差异

### 1. 架构对比

| 维度 | AI-Stock-Pro (老) | Win_Stock (新) |
|------|-------------------|----------------|
| **定位** | 概念验证/设计文档 | 生产级运行系统 |
| **状态** | 仅文档，无运行代码 | 已运行，有实际数据 |
| **数据存储** | 设计中的集中式数据库 | 单股单库 SQLite |
| **文件管理** | 未实现 | 严格的目录规范 |
| **Prompt管理** | 设计中的版本化 | 已实现 v1/v2 + current |
| **Skills** | 无 | 6个独立skill |
| **投资规则** | 无 | R001-R020 已合并 |
| **每日复盘** | 设计中的概念 | 已实现并运行 |
| **数据获取** | 设计中的多层降级 | 已实现 skill→browser→cache |
| **自选股管理** | 设计中的股票池 | 已实现，2只活跃 |
| **飞书通知** | 设计中的告警 | 未配置（待迁移） |

### 2. 文件结构对比

```
AI-Stock-Pro/                    Win_Stock/
├── AGENTS.md (设计文档)          ├── AGENTS.md (运行指令)
├── SOUL.md (哲学)                ├── SOUL.md (哲学+绝对客观)
├── IDENTITY.md (身份)            ├── IDENTITY.md (极简)
├── MEMORY.md (空)                ├── MEMORY.md (已记录)
├── HEARTBEAT.md (空)             ├── HEARTBEAT.md (定时任务)
├── TOOLS.md (数据源设计)          ├── TOOLS.md (实际配置)
├── USER.md (模板)                ├── USER.md (已填写)
├── README.md (项目说明)           ├── (无，信息在AGENTS)
├── init.sh (初始化脚本)           ├── (无，已初始化)
├── src/
│   └── main.py (空壳)            ├── (无，用skill组织)
└── docs/                          ├── skills/
    ├── ARCHITECTURE.md            │   ├── workspace-org/
    ├── DATA_MODEL.md              │   ├── stock-data/
    ├── WORKFLOW.md                │   ├── stock-analysis/
    ├── LLM_PROMPTS.md             │   ├── news-analysis/
    ├── API_DESIGN.md              │   └── daily-review/
                                 ├── prompts/
                                 │   ├── current/ → v2/
                                 │   ├── v1/
                                 │   └── v2/
                                 ├── data/
                                 │   └── watchlist/
                                 │       ├── active/
                                 │       │   ├── 601211/
                                 │       │   └── 002241/
                                 │       └── _watchlist_index.csv
                                 ├── books/
                                 │   └── reminiscences_2005/
                                 └── logs/
```

### 3. 核心能力对比

| 能力 | AI-Stock-Pro | Win_Stock | 差异说明 |
|------|-------------|-----------|---------|
| 数据获取 | ❌ 仅设计 | ✅ 三层降级 | 新agent已可用 |
| 技术指标 | ❌ 仅设计 | ✅ 计算+存储 | 新agent已可用 |
| LLM分析 | ❌ 仅设计 | ✅ 已运行 | 新agent已可用 |
| 预测记录 | ❌ 仅设计 | ✅ 数据库+文件 | 新agent已可用 |
| 预测验证 | ❌ 仅设计 | ✅ 自动复盘 | 新agent已可用 |
| 新闻分析 | ❌ 仅设计 | ✅ 已集成 | 新agent已可用 |
| A/B测试 | ❌ 仅设计 | ❌ 未实现 | 两者都缺 |
| 飞书通知 | ❌ 仅设计 | ❌ 未配置 | 需要迁移配置 |
| 财报分析 | ❌ 未提及 | ❌ 规划中 | 两者都缺 |
| 护城河分析 | ❌ 未提及 | ❌ 规划中 | 两者都缺 |

---

## 二、迁移策略

### 结论：AI-Stock-Pro 是设计文档，Win_Stock 是实现

**AI-Stock-Pro 没有实际运行数据或自选股需要迁移。**

它的价值在于：
1. **架构设计文档**（ARCHITECTURE.md, DATA_MODEL.md）→ 可作为 Win_Stock 参考
2. **LLM Prompt 设计**（LLM_PROMPTS.md）→ 可与 Win_Stock current prompt 对比
3. **工作流程设计**（WORKFLOW.md）→ 可补充 Win_Stock 的 daily-review skill
4. **API设计**（API_DESIGN.md）→ 可作为未来扩展参考

### 迁移内容清单

#### ✅ 需要迁移的
| 内容 | 来源 | 目标 | 操作 |
|------|------|------|------|
| 飞书配置 | ai-stock-pro/docs/WORKFLOW.md | win_stock/config/ | 提取并创建 |
| 架构设计参考 | ai-stock-pro/docs/ARCHITECTURE.md | win_stock/docs/ | 复制参考 |
| A/B测试设计 | ai-stock-pro/docs/WORKFLOW.md | win_stock/skills/daily-review/ | 提取补充 |
| 监控告警设计 | ai-stock-pro/docs/WORKFLOW.md | win_stock/HEARTBEAT.md | 补充完善 |

#### ❌ 不需要迁移的
| 内容 | 原因 |
|------|------|
| 自选股 | ai-stock-pro 没有实际自选股数据 |
| 数据库 | ai-stock-pro 没有实际数据库 |
| 预测记录 | ai-stock-pro 没有实际预测 |
| 分析报告 | ai-stock-pro 没有实际报告 |
| 代码 | ai-stock-pro 只有空壳 main.py |

---

## 三、具体迁移操作

### 操作1: 迁移飞书配置

```bash
# 从 ai-stock-pro 的 WORKFLOW.md 中提取飞书配置
# 创建 win_stock 的配置文件
mkdir -p /Volumes/zhangstExtern/openclaw/workspace/win_stock/config/
```

### 操作2: 复制参考文档

```bash
# 将 ai-stock-pro 的设计文档复制到 win_stock 作为参考
mkdir -p /Volumes/zhangstExtern/openclaw/workspace/win_stock/docs/
cp /Volumes/zhangstExtern/openclaw/workspace/ai-stock-pro/docs/*.md \
   /Volumes/zhangstExtern/openclaw/workspace/win_stock/docs/
```

### 操作3: 补充 HEARTBEAT.md

将 ai-stock-pro 的监控告警设计整合到 win_stock 的 HEARTBEAT.md

### 操作4: 标记 ai-stock-pro 为归档

```bash
# 重命名或添加归档标记
cd /Volumes/zhangstExtern/openclaw/workspace/
mv ai-stock-pro ai-stock-pro-archived-2026-04
# 或创建标记文件
echo "ARCHIVED: 功能已迁移到 win_stock" > ai-stock-pro/ARCHIVED.md
```

---

## 四、关于"老 agent 自选股"

### 实际情况

**AI-Stock-Pro 没有实际运行过，没有自选股数据。**

它的 AGENTS.md 中提到：
```
- [ ] 获取历史 K 线数据
- [ ] 获取板块和概念数据
- [ ] 获取市场新闻和公告
- [ ] 设计数据存储结构
```

所有任务都是 `[ ]` 未完成状态。

### 如果你指的是其他老 agent

请确认：
1. **是否有其他股票 agent？** 例如 `Ai-StockAssistant` 或其他名称？
2. **自选股数据在哪里？** 可能在：
   - 某个 JSON/CSV 文件
   - 飞书文档/表格
   - 其他 agent 的 workspace
   - 你的个人笔记

### Win_Stock 当前自选股

```csv
code,name,industry,added_date,status
601211,国泰海通,证券Ⅱ,2026-04-24,active
002241,歌尔股份,消费电子/ARVR,2026-04-24,active
```

---

## 五、飞书 ID 配置

### 需要用户提供

| 配置项 | 说明 | 当前状态 |
|--------|------|---------|
| 飞书 Webhook URL | 用于发送通知 | ❌ 未配置 |
| 飞书 App ID | 如需机器人交互 | ❌ 未配置 |
| 飞书 App Secret | 对应 App ID | ❌ 未配置 |
| 通知目标 | 个人/群聊 | ❌ 未配置 |

### 配置位置

```
win_stock/config/
├── .env                    # 环境变量（API keys）
├── feishu.yaml            # 飞书配置（新增）
└── notification.yaml      # 通知规则（新增）
```

### 需要用户执行

1. 在飞书开放平台创建应用
2. 获取 Webhook URL 或 App ID/Secret
3. 提供给我，我写入配置文件

---

## 六、下一步行动

### 立即执行（无需用户输入）
- [x] 分析两个 agent 差异
- [x] 确认 ai-stock-pro 无实际数据
- [ ] 复制设计文档到 win_stock/docs/
- [ ] 创建 config/ 目录结构

### 需要用户确认
- [ ] **是否有其他老 agent 需要迁移？** 请提供路径或名称
- [ ] **飞书配置信息**：Webhook URL 或 App ID/Secret
- [ ] **是否归档 ai-stock-pro？** 重命名还是保留

### 可选优化
- [ ] 将 ai-stock-pro 的 A/B 测试设计整合到 daily-review skill
- [ ] 将监控告警设计整合到 HEARTBEAT.md
- [ ] 对比 ai-stock-pro 的 LLM_PROMPTS.md 与 win_stock current prompt，提取优化点

---

*分析日期: 2026-04-28*
*结论: AI-Stock-Pro 是设计文档，Win_Stock 是运行系统，无需数据迁移*
