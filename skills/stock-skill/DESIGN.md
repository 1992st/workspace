# PMS CLI Command Skill - 完整设计文档

**版本**：v2.0  
**设计日期**：2026-04-19  
**核心理念**：Skill 不是工具集合，而是 Agent 的专业技能；知识按需分层加载，避免信息过载

---

## 1. 设计目标

### 1.1 要解决的核心问题

| 问题 | 解决方式 |
|-----|---------|
| Skills 被当作工具列表 | 定义为「Agent 能力」，关注「能做什么」而非「有什么命令」|
| 文档过长导致信息过载 | 按场景分目录，3步递进加载，每步 20-50 行 |
| 知识冲突和重复 | 通用知识放 `common/`，场景知识隔离，单一职责 |
| Skills 本身无记忆 | 通过 Memory 系统查询用户偏好，技能只提供「记忆接口」|
| 一次性加载全部知识 | 根据执行阶段动态加载，用完即走 |

### 1.2 设计原则

1. **能力导向**：描述 Agent「能做什么」，而非工具列表
2. **3步加载**：第一步认知 → 第二步执行 → 第三步善后（问题/记忆）
3. **场景隔离**：按 `common/`、`workload/`、`workitem/` 分目录，避免污染
4. **通用共享**：强制原则、错误码、基础接口放 `common/`，所有场景共享
5. **Memory 集成**：明确 Memory 查询接口，记录用户偏好和历史

---

## 2. 目录结构

```
skills/pms-cli-command/
├── SKILL.md                    # 技能入口（~80行，含 triggers）
├── scripts/
│   └── pms-cli-router.sh      # CLI 路由脚本
├── references/                 # 知识文档
│   ├── workload-guide.md      # 工时填报指南
│   ├── workitem-guide.md      # 工单管理指南
│   ├── api-reference.md       # CLI 参数手册
│   ├── workflow-background.md # 业务背景
│   ├── memory-guide.md        # Memory 记录规范
│   └── INDEX.md               # 文档索引
└── config/
    └── user.yaml              # 外部化敏感配置
```

---

## 3. 3步加载策略详解

### 3.1 工时填报场景

```
用户: "帮我填周报 2026-W16"
    ↓
加载 SKILL.md
    - 了解技能定位、强制原则、工具入口
    ↓
加载 references/workload-guide.md
    - 场景定义、5步执行流程、常见问题、专用接口
    ↓
执行 → 成功后参考 memory-guide.md 记录
```

### 3.2 工单管理场景

```
用户: "帮我创建一个新工单"
    ↓
加载 SKILL.md
    - 了解技能定位、强制原则、工具入口
    ↓
加载 references/workitem-guide.md
    - 场景定义、创建/查询流程、常见问题、专用接口
    ↓
执行 → 成功后参考 memory-guide.md 记录
```

### 3.3 技术参考（按需）

```
用户: "create_workload 的参数是什么？"
    ↓
加载 references/api-reference.md
    - 完整 CLI 参数手册
```

---

## 4. 文档内容规范

### 4.1 SKILL.md（~80行）

```markdown
# PMS CLI 协作能力

## 核心定位
- 工时填报
- 工单管理

## 使用方式
按需加载对应文档：
- workload-guide.md
- workitem-guide.md
- api-reference.md
- workflow-background.md
- memory-guide.md

## 强制原则
1. 确认优先
2. 数据溯源
3. 透明沟通

## 工具入口
脚本路径 + 常用操作速查
```

### 4.2 workload-guide.md

单一文档包含：场景定义、5步执行流程、常见问题速查、专用接口。

### 4.3 workitem-guide.md

单一文档包含：场景定义、创建/查询流程、常见问题速查、专用接口。

---

## 5. Memory 系统集成

### 5.1 记录方式

Agent 通过 Read/Write 工具直接操作 memory 文件：
- 每日记录：`memory/YYYY-MM-DD.md`
- 长期偏好：`MEMORY.md`

参考 `references/memory-guide.md` 中的格式规范。

### 5.2 记录格式

```markdown
## PMS 工时填报记录 - 2026-W16

- **周次**：2026-W16（04-13 至 04-19）
- **条目**：3 条
- **总工时**：20 小时
- **工单分布**：
  - #12345 用户中心开发：8h
  - #12346 技术评审：4h

### 本次经验
- [踩坑/优化点]

## PMS 使用偏好（更新）

### 常用工单映射（新增）
- 日常开发 → #12345

### 填报习惯
- 偏好工时类型：开发工作
- 偏好任务粒度：细粒度
```

### 5.3 记录位置

- **每日记录**：`memory/YYYY-MM-DD.md`
- **长期偏好**：`MEMORY.md`（汇总整理后的偏好）

---

## 6. 外部化配置

### 6.1 config/user.yaml

```yaml
# 敏感配置（已加入 .gitignore）

pingcode:
  # 如需使用特定 token（不推荐，优先使用 CLI session）
  # token: "your_token_here"

paths:
  # 行为数据根目录（可选，覆盖默认路径）
  # behavior_root: "/Volumes/shutong.zhang/behavior/"

# 注意：用户偏好通过 Memory 系统管理，不要在此文件中维护
```

### 6.2 配置原则

- **仅用于敏感信息**：token、密钥等无法存入 Memory 的信息
- **用户偏好走 Memory**：常用工单、填报习惯等通过 Memory 查询
- **路径可覆盖**：behavior 目录可通过配置自定义

---

## 7. CLI 脚本规范

### 7.1 路由脚本

```bash
./scripts/pms-cli-router.sh <operation> [args] [--run]

# Dry-run 预览（默认）
./scripts/pms-cli-router.sh create_workload \
  --principal-id "12345" \
  --type-id "dev" \
  --duration 480 \
  --report-at 1713024000

# 确认执行（添加 --run）
./scripts/pms-cli-router.sh create_workload ... --run
```

### 7.2 支持的操作

| 操作 | 用途 |
|------|------|
| auth_login | 登录认证 |
| get_me | 获取当前用户 |
| list_workload_types | 获取工时类型 |
| search_projects | 搜索项目 |
| search_work_items | 搜索工单 |
| list_workloads | 查询工时记录 |
| create_workload | 创建工时 |
| update_workload | 更新工时 |
| list_my_related | 查询我相关的工单 |

---

## 8. 与其他 Skill 的关系

### 8.1 依赖的 Skill

- **Memory Skill**：通过 `memory_search`、`memory_get` 查询用户偏好
- **Time Skill**（如有）：时间计算函数可复用

### 8.2 被依赖的场景

- **周报 Skill**：可调用本 skill 进行工时填报
- **项目管理 Skill**：可复用工单查询能力

---

## 9. 扩展规划

### 9.1 短期（已实现）

- [x] 工时填报（3步加载）
- [x] 工单管理（3步加载框架）
- [x] Memory 集成
- [x] 按需技术参考

### 9.2 中期

- [ ] 工时数据分析（周报自动生成）
- [ ] 智能工单推荐（根据工作内容推荐关联工单）
- [ ] 批量操作（一次填报多天工时）

### 9.3 长期

- [ ] 冲突检测（重复填报、时间超限预警）
- [ ] 自动化填报（根据行为数据自动预填）

---

## 10. 最佳实践

### 10.1 对 Agent 开发者

1. **按需加载指南**：根据场景加载 `workload-guide.md` 或 `workitem-guide.md`
2. **遇到问题参考指南内「常见问题」小节**：不要硬编码解决方案
3. **成功后记录 memory**：参考 `memory-guide.md` 格式
4. **查询 memory 优先**：利用历史偏好提高效率

### 10.2 对 Skill 维护者

1. **保持文档精简**：每篇 20-50 行，单一职责
2. **通用知识放 common**：避免各场景重复定义
3. **接口变化时同步更新**：api-reference.md 和 core.md
4. **记录踩坑经验**：execution.md 中的「本次经验」部分

---

## 附录 A：设计演进

### A.1 v1.0 → v2.0（第一次重构）

| 维度 | v1.0（7阶段扁平） | v2.0（3步+场景目录） |
|-----|-------------|-------------------|
| 文档数量 | 7+篇 | 4篇/场景 |
| 单篇长度 | 20-40行 | 20-50行（平衡） |
| 目录结构 | 扁平 | 按场景分目录 |
| 通用知识 | 重复在各篇 | 集中到 common/ |
| 加载复杂度 | 7步判断 | 3步判断 |
| 维护难度 | 高（文档多） | 中（结构清晰） |

### A.2 v2.0 → v2.1（本次优化，2026-04-19）

| 维度 | v2.0 | v2.1（当前） |
|-----|------|-------------|
| 文档数量 | 4篇/场景 + common + index | 2篇指南 + api + background + memory |
| 目录结构 | `common/` + `workload/` + `workitem/` | 扁平（references 根目录）|
| 接口重复 | 5处（core+execution+api+SKILL） | 2处（guide + api） |
| 功能缺口 | `create_work_item` 缺失 | 已补充 |
| SKILL 入口 | 无 triggers，~150行 | 有 triggers，精简至 ~80行 |
| AGENTS 重复 | 5步流程完整重复 | 精简为高层原则 + 指向 skill |

**关键问题与优化**：
1. **3步加载策略不可行**：Agent 读取文件后上下文是累积的，无法"卸载"。改为按需加载单份指南文档。
2. **职责重叠**：AGENTS.md 与 skill references 同时定义了5步填报流程，运行时可能冲突。已将 AGENTS.md 精简为高层原则。
3. **`memory_search` 命令未定义**：在 skill 框架中无此命令。改为在 memory-guide.md 中说明记录格式，由 Agent 通过 Read 工具操作 memory 文件。
4. **文档行数约束失效**：设计约束 20-50 行/篇，实际全部超标。取消僵化约束，改为内容完整性优先。
5. **遗留文件污染**：旧版 `workload-*.md` 等与新结构并存。已全部清理。

---

## 附录 B：快速参考

### Agent 执行流程（v2.1）

```
用户输入
  ↓
意图识别 → 触发 skill（通过 triggers）
  ↓
加载 SKILL.md → 了解场景和原则
  ↓
根据场景加载指南：
  ├─ 工时填报 → workload-guide.md
  ├─ 工单管理 → workitem-guide.md
  ├─ CLI 参数 → api-reference.md
  └─ 业务背景 → workflow-background.md
  ↓
执行 → 记录 memory（参考 memory-guide.md）
```

### Memory 查询关键词

```
pms preference
workload habit
workload 历史
常用工单 mapping
pms error
```

---

## 附录 C：变更日志

| 日期 | 版本 | 变更 | 说明 |
|-----|------|------|------|
| 2026-04-19 | v2.0 | 初始设计 | 3步加载策略、场景化目录、Memory 集成 |
| 2026-04-19 | v2.1 | 结构优化 | 合并子目录为扁平结构，补充 create_work_item，添加 triggers，精简 SKILL.md，清理遗留文件，对齐 AGENTS.md 边界 |
