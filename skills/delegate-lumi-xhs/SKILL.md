---
name: delegate-lumi-xhs
description: "Use this skill when user asks to optimize an article with Xiaohongshu style by sending the article to lumi-writer agent."
metadata:
  requires:
    tools: ["sessions_send", "sessions_history"]
  target_agent:
    id: "lumi-writer"
  mode: "agent_to_agent"
---

# delegate-lumi-xhs

## Purpose
当用户要求“按小红书规则优化文章”时，不在本地重写，优先把文章委托给 `lumi-writer` 处理，并回收结果给用户。

## Preconditions
- 必须拿到文章正文或可读 `file_path`。
- 若用户没给 `doc_type_hint`，默认传 `xiaohongshu`。
- 不要求用户提供 lumi 的 sessionKey；统一用 `agentId=lumi-writer` + 稳定 `label` 自动路由。

## Dispatch Contract
调用 `sessions_send`：
- `agentId`: `lumi-writer`
- `label`: `lumi-xhs-optimize`
- `message`: 使用下方模板，必须是结构化块，避免歧义。

消息模板：

```text
[ACP_REQUEST]
request_type: doc_optimize
file_path: <ABS_OR_WORKSPACE_PATH>
doc_type_hint: xiaohongshu
organize_first: true
visualize: auto
constraints:
  - keep_facts_unchanged
  - keep_core_conclusion_unchanged
  - allow_light_rewrite_for_readability
output:
  - optimized_content
  - change_summary_by_section
  - backup_path
  - risk_notes
[/ACP_REQUEST]
```

内联审查标准（运行时强制）：
- G1 渲染完整性：图片链接有效、`img src` 非空、避免字符画表格作为唯一信息载体
- G2 语义保真：核心命题/关键事实/结论方向不变；禁止无指令强人设语气
- G3 可读性：段落有节奏但不碎片化；关键背景/案例/行动项完整

## Execution Rules
1. 若用户给了 `file_path`，直接转发，不重复追问“Lumi 是谁”。
2. 若用户直接贴正文，先保存到 `working/` 临时文件再转发。
3. `timeoutSeconds` 建议 120-300 秒。
4. 转发后读取回包；若未返回正文，继续用 `sessions_history` 拉取最近回复。
5. 回稿后先执行审查门禁：先跑 `./tools/lumi_review_check.sh <doc_path>`，再做语义人工复核。
6. 若审查结果 `REVISION_REQUIRED`，必须回炉给 lumi（最多 2 轮），禁止直接交付用户。
7. 若审查结果 `PASS`，再按 `结论 -> 证据 -> 行动` 汇报，并附绝对路径。

## Revision Loop
当发现问题，发送如下回炉模板给 lumi：

```text
[ACP_REVIEW_FEEDBACK]
status: REVISION_REQUIRED
doc_type_hint: xiaohongshu
issues:
  - gate: <G1|G2|G3>
    id: <ISSUE_ID>
    detail: <具体问题>
requirements:
  - fix_only_listed_issues
  - keep_core_facts_and_conclusion_unchanged
  - keep_structure_stable
output:
  - revised_content
  - fix_mapping(issue_id -> fix)
[/ACP_REVIEW_FEEDBACK]
```

规则：
- 每轮回炉只修问题清单，不允许整篇推倒重写
- 最多 2 轮；第 2 轮仍失败则返回 `BLOCKED` 并请求人工决策

## Failure Handling
- 若 `status=confirm_required`：将候选类型与置信度原样回显给用户，一次性询问确认。
- 若 `status=failed`：回显失败环节、backup 路径、建议重试动作。
- 若 `status=ok` 但审查不通过：状态仍按 `REVISION_REQUIRED` 处理，不得视为完成。
- 严禁在失败时静默降级为“本地瞎改”。

## Safety
- 不改用户原始观点与事实口径。
- 不伪造来源和案例。
- 涉及对外发布仍遵循 Publish Gate（需人工确认）。
