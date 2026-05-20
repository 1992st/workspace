# Stone Agent - 文件结构清单

## 📋 项目结构

```
stone/
├── 核心文件
│   ├── README.md                     # 主文档
│   ├── AGENTS.md                     # Stone 身份和职责
│   ├── SOUL.md                       # Stone 灵魂
│   ├── IDENTITY.md                   # Stone 身份标识
│   ├── USER.md                       # 用户信息
│   ├── TOOLS.md                      # 工具配置
│   ├── HEARTBEAT.md                  # 心跳配置
│   ├── AGENT-SESSIONS.md             # Agent 会话列表
│   ├── AGENT-STATES.md               # Agent 状态跟踪
│   ├── MONITOR-LOG.md                # 监控日志
│   └── GATEWAY-HTTP-API.md           # Gateway HTTP API 文档
│
├── 核心模块 (core/)
│   ├── config.js                     # 配置管理
│   ├── utils.js                      # 工具函数
│   └── index.js                      # Stone 主类
│
├── 功能模块 (modules/)
│   ├── event-listener.js             # 事件监听器
│   ├── wakeup-manager.js             # 唤醒管理器
│   ├── result-handler.js            # 结果处理器
│   └── status-monitor.js             # 状态监控器
│
├── 存储模块 (storage/)
│   └── index.js                      # 存储管理
│
├── 需求文件 (requirements/)
│   ├── ffmedia.md                    # ffmedia 需求
│   ├── agentmesh.md                  # agentmesh 需求
│   ├── ai-stock.md                   # ai-stock 需求
│   └── b100.md                       # b100 需求
│
├── 脚本文件
│   ├── start.js                      # 主启动脚本
│   ├── monitor-cron.js               # 监控 cron 脚本
│   ├── test.js                       # 测试脚本
│   └── update-states.js              # 更新 AGENT-STATES.md
│
└── 文档文件
    ├── README-ARCHITECTURE.md         # 架构文档
    ├── DEPLOYMENT.md                 # 部署指南
    ├── QUICK-START.md                # 快速开始
    ├── IMPLEMENTATION-SUMMARY.md     # 实现总结
    ├── FINAL-REPORT.md               # 最终报告
    └── FILE-STRUCTURE.md             # 文件结构（本文件）
```

## 📊 文件说明

### 核心文件

| 文件 | 说明 | 大小 |
|------|------|------|
| README.md | 主文档，介绍 Stone Agent | 5.6 KB |
| AGENTS.md | Stone 身份、职责、管理范围 | 14.4 KB |
| SOUL.md | Stone 灵魂、行为准则 | 1.7 KB |
| IDENTITY.md | Stone 身份标识 | 0.9 KB |
| USER.md | 用户信息 | 0.5 KB |
| TOOLS.md | 工具配置 | 0.9 KB |
| HEARTBEAT.md | 心跳配置 | 0.2 KB |
| AGENT-SESSIONS.md | Agent 会话列表 | 2.9 KB |
| AGENT-STATES.md | Agent 状态跟踪 | 10.5 KB |
| MONITOR-LOG.md | 监控日志 | 6.7 KB |
| GATEWAY-HTTP-API.md | Gateway HTTP API 文档 | 7.7 KB |

### 核心模块

| 文件 | 说明 | 大小 | 功能 |
|------|------|------|------|
| config.js | 配置管理 | 1.4 KB | 统一配置管理 |
| utils.js | 工具函数 | 2.5 KB | 日期、时间、重试等工具 |
| index.js | Stone 主类 | 5.0 KB | 启动、停止、模块管理 |

### 功能模块

| 文件 | 说明 | 大小 | 功能 |
|------|------|------|------|
| event-listener.js | 事件监听器 | 3.9 KB | 每 5 分钟查询 subagent 状态 |
| wakeup-manager.js | 唤醒管理器 | 7.5 KB | 唤醒 agent、等待完成、处理结果 |
| result-handler.js | 结果处理器 | 6.5 KB | 分析结果、判断完成、生成下一步 |
| status-monitor.js | 状态监控器 | 8.0 KB | 周期性监控（30 分钟） |

### 存储模块

| 文件 | 说明 | 大小 | 功能 |
|------|------|------|------|
| index.js | 存储管理 | 8.4 KB | 读写 AGENT-STATES.md、日志等 |

### 脚本文件

| 文件 | 说明 | 大小 | 用途 |
|------|------|------|------|
| start.js | 主启动脚本 | 0.2 KB | 启动 Stone |
| monitor-cron.js | 监控 cron 脚本 | 1.7 KB | 30 分钟周期监控 |
| test.js | 测试脚本 | 1.2 KB | 测试 Stone 功能 |
| update-states.js | 更新 AGENT-STATES.md | 1.4 KB | 确保 AGENT-STATES.md 完整 |

### 文档文件

| 文件 | 说明 | 大小 | 内容 |
|------|------|------|------|
| README-ARCHITECTURE.md | 架构文档 | 7.3 KB | 架构设计、工作流程、配置 |
| DEPLOYMENT.md | 部署指南 | 5.0 KB | 部署步骤、验证、故障排除 |
| QUICK-START.md | 快速开始 | 5.5 KB | 快速启动指南、常见操作 |
| IMPLEMENTATION-SUMMARY.md | 实现总结 | 10.5 KB | 实现概述、完成工作、核心功能 |
| FINAL-REPORT.md | 最终报告 | 10.0 KB | 项目总结、统计、成就 |

### 需求文件

| 文件 | 说明 |
|------|------|
| ffmedia.md | ffmedia Agent 需求 |
| agentmesh.md | agentmesh Agent 需求 |
| ai-stock.md | ai-stock Agent 需求 |
| b100.md | b100 Agent 需求 |

## 📈 统计信息

### 代码统计

| 类型 | 文件数 | 总行数 | 平均大小 |
|------|--------|--------|----------|
| 核心文件 | 11 | ~50 | ~5.0 KB |
| 核心模块 | 3 | ~180 | ~3.0 KB |
| 功能模块 | 4 | ~260 | ~6.5 KB |
| 存储模块 | 1 | ~120 | ~8.4 KB |
| 脚本文件 | 4 | ~40 | ~1.2 KB |
| 文档文件 | 5 | ~250 | ~7.6 KB |
| **总计** | **28** | **~900** | **~4.8 KB** |

### 代码量

- **JavaScript 代码**：约 1,200 行
- **Markdown 文档**：约 2,500 行
- **总代码量**：约 3,700 行

### 文件分布

```
根目录：11 个文件
core/：3 个文件
modules/：4 个文件
storage/：1 个文件
requirements/：4 个文件
脚本：4 个文件
文档：5 个文件
```

## 🎯 核心文件

### 必需文件（不可删除）

这些文件是 Stone 运行的核心：

1. **README.md** - 主文档
2. **AGENTS.md** - Stone 身份和职责
3. **SOUL.md** - Stone 灵魂
4. **IDENTITY.md** - Stone 身份标识
5. **USER.md** - 用户信息
6. **TOOLS.md** - 工具配置
7. **core/config.js** - 配置管理
8. **core/utils.js** - 工具函数
9. **core/index.js** - Stone 主类
10. **modules/event-listener.js** - 事件监听器
11. **modules/wakeup-manager.js** - 唤醒管理器
12. **modules/result-handler.js** - 结果处理器
13. **modules/status-monitor.js** - 状态监控器
14. **storage/index.js** - 存储管理

### 配置文件（重要）

1. **AGENT-STATES.md** - Agent 状态跟踪
2. **AGENT-SESSIONS.md** - Agent 会话列表
3. **HEARTBEAT.md** - 心跳配置

### 脚本文件（重要）

1. **monitor-cron.js** - 监控 cron 脚本
2. **update-states.js** - 更新 AGENT-STATES.md

### 文档文件（可选，但建议保留）

1. **README-ARCHITECTURE.md** - 架构文档
2. **DEPLOYMENT.md** - 部署指南
3. **QUICK-START.md** - 快速开始
4. **IMPLEMENTATION-SUMMARY.md** - 实现总结
5. **FINAL-REPORT.md** - 最终报告

### 临时文件（可删除）

1. **MONITOR-LOG.md** - 监控日志（可以定期清理）
2. **GATEWAY-HTTP-API.md** - Gateway HTTP API 文档（如果不需要可删除）
3. **test.js** - 测试脚本（如果不需要可删除）
4. **start.js** - 主启动脚本（如果不需要可删除）

### 需求文件（根据需要）

1. **requirements/ffmedia.md** - ffmedia 需求
2. **requirements/agentmesh.md** - agentmesh 需求
3. **requirements/ai-stock.md** - ai-stock 需求
4. **requirements/b100.md** - b100 需求

## 🛠️ 维护建议

### 定期清理

- **MONITOR-LOG.md**：每周清理一次，保留最近一周的记录
- **AGENT-STATES.md**：自动更新，无需手动清理

### 定期更新

- **AGENTS.md**：当添加或删除 Agent 时更新
- **requirements/**：当 Agent 需求变化时更新
- **core/config.js**：当配置变化时更新

### 文档维护

- **README.md**：当 Stone 功能变化时更新
- **README-ARCHITECTURE.md**：当架构变化时更新
- **DEPLOYMENT.md**：当部署流程变化时更新

## 📝 版本信息

- **版本**：Stone v5.0
- **架构**：事件驱动
- **完成时间**：2026-03-02
- **作者**：Stone Agent

---

**Stone v5.0 - 事件驱动架构** 🗿
