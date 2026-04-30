# Examples

## Query: 小红书

输入：`这篇小红书种草文放哪里？`

期望输出：

- `resolved_doc_type = xiaohongshu`
- `resolved_platform = xiaohongshu`
- `target_paths.working = docs/xiaohongshu/xiaohongshu/working`
- `target_paths.publish = docs/xiaohongshu/xiaohongshu/publish`

## Query: PRD

输入：`新 PRD 文档放哪里？`

期望输出：

- `resolved_doc_type = prd`
- `resolved_platform = internal`
- `target_paths.working = docs/prd/internal/working`
- `target_paths.publish = docs/prd/internal/publish`

## Query: 歧义

输入：`这篇文档放在哪里？`

期望输出：

- `status = confirm_required`
- 候选 `doc_type` 列表
