# 微信公众号发布工具

## 工具说明

本工具用于辅助将 Agent 小茶馆的内容发布到微信公众号。

**重要限制**：微信安全机制要求发布必须由人工确认，我无法直接点击"发表"按钮。

## 使用流程（推荐）

### 一条命令启动完整流程

```bash
# 自动进入发布准备流程（自动补全 task_id）
./tools/publish_wechat.sh publish
```

流程会自动做：
1. 生成或复用 `task_id`
2. 打开 mdnice 编辑器 + 公众号编辑器
3. 写入状态文件 `memory/publish-wechat/state.yaml`
4. 提示你执行人工步骤（复制到公众号并保存草稿）

人工保存草稿后回执：

```bash
./tools/publish_wechat.sh saved <task_id> <正文字数>
```

## 快捷命令参考

```bash
# 启动发布流程（推荐）
./tools/publish_wechat.sh publish [task_id] [article.md]

# 标记草稿已保存（并做正文非空门禁）
./tools/publish_wechat.sh saved [task_id] [word_count]

# 中断后恢复流程
./tools/publish_wechat.sh resume

# 查看当前状态
./tools/publish_wechat.sh status

# 打开公众号后台
./tools/publish_wechat.sh open

# 预览文章
./tools/publish_wechat.sh preview publish_queue/xxx/article.md

# 格式化文章
./tools/publish_wechat.sh format publish_queue/xxx/article.md
```

## 状态文件

单一状态文件路径：
`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/memory/publish-wechat/state.yaml`

关键字段：
- `task_id`
- `status`（`NEW/EDITING/NEEDS_INPUT/PACKAGED`）
- `mdnice.url`
- `content.word_count`
- `next_action`

## 发布前检查清单

每次发布前，我会确认：
- [ ] 标题符合规范
- [ ] 内容口语化、无黑话
- [ ] 术语首处有白话解释
- [ ] 结尾有 3 条可执行动作
- [ ] 已明确获取 `发布吧 <task_id>` 命令

## 账号信息
- 公众号名称：Agent 小茶馆
- 当前粉丝：1
- 新号状态，暂无历史发布

## 注意事项

1. **微信限制**：我无法直接发表，只能帮你准备内容和打开编辑器
2. **mdnice 主稿**：正文以 mdnice 单文档为准，命名 `[`task_id`] 标题`，原地修改，不新建 v2/v3
3. **封面图**：发布时需手动选择封面
4. **原创声明**：新号无原创保护，后期可开

---

## Cron 兜底工具（飞书告警转 NEEDS_INPUT）

当 `agent-radar-desk` 的定时任务运行失败，或运行成功但飞书未送达时，可用以下命令自动生成 `NEEDS_INPUT` 任务：

```bash
# 检查最近 72 小时的 radar cron 运行记录
./tools/cron_guard.sh 72
```

默认检查任务：
- `radar-daily-0800`
- `radar-daily-1900`
- `radar-weekly-friday-2000`

状态文件：
- `/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/memory/cron_guard_state.json`

说明：
- 同一 `job_id + runAtMs` 只告警一次，避免重复建单
- 证据路径会写入任务文件，便于快速排查

---

## Lumi 回稿审查工具（小红书优化）

当文章由 `lumi-writer` 优化返回后，先执行：

```bash
./tools/lumi_review_check.sh /absolute/path/to/article.md
```

返回值：
- `PASS`：可进入交付
- `REVISION_REQUIRED`：必须按问题清单回炉给 lumi
- `BLOCKED`：文档不存在等硬错误，先修复输入

审查标准（运行时以技能/宪法内联规则为准）：
- G1 渲染完整性
- G2 语义保真
- G3 可读性

---

## 框图构建工具（HTML/Mermaid）

用于把文章中的框图占位符替换成可发布图片引用，并输出可直接粘贴 mdnice 的发布稿。

```bash
# 传 task_id
./tools/build_diagrams.sh 2026-04-05-002
```

占位符写法（在 `article.md`）：

```md
{{diagram:ms-three-layer|微软AI三层结构}}
```

构建输出：
- `publish_queue/<task_id>/diagrams/out/*.png`（优先）
- `publish_queue/<task_id>/diagrams/out/*.svg`（兜底）
- `publish_queue/<task_id>/article.publish.md`

说明：
- HTML 框图默认可用（无需额外安装）。
- Mermaid 真实渲染依赖 `mmdc`；未安装时会生成提示型 SVG，保证文档不断链。
- 文档在本地保存，由你手动发到 mdnice。

---

## Tasks 目录治理工具（2026-04-13）

从 2026-04-13 起，`tasks/` 是唯一工作目录，`dev-topics/` 停用。

### 1) 全量迁移到标准结构

```bash
# 先看计划（dry-run）
./tools/migrate_tasks_layout.sh

# 执行迁移（会移动文件并修复 markdown 路径引用）
./tools/migrate_tasks_layout.sh --apply
```

迁移报告：
- `reports/tasks-migration-YYYY-MM-DD.md`

### 2) 结构与状态校验

```bash
./tools/task_lint.sh
```

校验项：
- `tasks/` 下必须是 `tasks/<task_id>-<slug>/`
- 每个任务目录必须有 `task.md`
- `task.md` 必须满足状态双写同步
  - frontmatter: `status: ...`
  - 正文段落: `## 状态` + `- status: ...`
- `dev-topics/` 只能保留停用态内容（如 `_migrated/`），不得新增新任务
