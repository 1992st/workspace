# Agent观察室 Workspace

## 目录
- `tasks/`：唯一工作目录（统一为 `tasks/<task_id>-<slug>/`）
- `dev-topics/`：已停用（仅保留迁移前历史，不再新增）
- `intel/hot/`：热点库（30天）
- `intel/deep/`：深度资料库（长期）
- `reports/`：日报与周报
- `publish_queue/`：待发布包
- `policies/`：策略规范
- `skills/`：技能配置与路由（`_manifest.yaml` + 各技能 `SKILL.md`）
- `memory/`：每日运行日志
- `research/xiaohongshu/`：小红书专题研究（`raw/` 原始样本，`analysis/` 分析稿，`knowledge/` 长期知识）

## 调度节奏
- 每日 08:00：晨扫
- 每日 19:00：日终整合
- 每周五 20:00：周报双版本
