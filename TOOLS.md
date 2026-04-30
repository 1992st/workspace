# TOOLS.md - 工具与渠道规范

## 渠道
- 飞书：专用群（群 ID 待补）
- 公众号：仅生成待发布包，人工发布
- 本地知识库：workspace 内 markdown 归档

## 外发流程
1. 生成发布包
2. 回显发布摘要
3. 等待 `发布吧 <task_id>`
4. 执行外发
5. 写入任务日志

## Agent-to-Agent（Lumi 委托）
当用户明确要求“发给lumi优化/按小红书优化”时，使用以下工具链：
1. `sessions_send` 直发 `agentId=lumi-writer,label=lumi-xhs-optimize`
2. 若提示 label 不存在：`sessions_spawn` 创建后重试 `sessions_send`
3. 用 `sessions_history` 拉取回稿
4. 执行 `./tools/lumi_review_check.sh <doc_path>` + 人工语义复核
5. 不通过则发 `ACP_REVIEW_FEEDBACK` 回炉，最多 2 轮
6. 通过后再回传用户

约束：
- 用户已给 `file_path` 时不得重复追问基础信息
- 不提供“我本地改 or 发给lumi”的分流选项
- 默认 `doc_type_hint=xiaohongshu`，除非用户明确指定其他类型
- 审查标准内联执行：
  - G1 渲染完整性
  - G2 语义保真
  - G3 可读性

## 异常分类
1. 渠道失败：发送失败/接口不可用
2. 数据冲突：稿件版本不一致/任务状态不匹配
3. 审批中断：未拿到确认命令或确认超时

## 回退策略
异常时停止外发，保留本地发布包并将任务标记 `NEEDS_INPUT`。

## Cron 推荐命令

- 内容检索：`qmd query ...`
- 索引检查：`qmd status`
- 维护更新：`qmd update --pull`
- 向量重建：`qmd embed`
- 目录巡检：`ls`、`find`、`grep`、`cat`

禁用模式：
- `python3 -c`
- `python3 <<'PY'`
- 将维护 cron 扩展成无关调研或配置改造任务
