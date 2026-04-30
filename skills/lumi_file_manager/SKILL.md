---
name: lumi_file_manager
description: "Resolve standard document paths by doc_type/platform and answer where new files should be placed."
metadata:
  inputs:
    - intent (locate_new_doc | validate_path | list_paths)
    - query (optional natural language)
    - doc_type_hint (optional)
    - platform_hint (optional)
    - config_path (optional, default skills/lumi_file_manager/config.md)
---

# lumi_file_manager

目标：通过统一路径规则管理文档，并回答“新文档放在哪里”。

## Intents

- `locate_new_doc`：返回新文档推荐路径（`working`/`publish`）
- `validate_path`：校验给定文件是否落在规范路径
- `list_paths`：列出某类型/平台的标准路径

## Execution

使用命令：

```bash
node tools/lumi_file_manager_query.mjs \
  --intent locate_new_doc \
  --query "这篇小红书种草文放哪里" \
  --config skills/lumi_file_manager/config.md
```

可选显式参数覆盖自然语言识别：

```bash
node tools/lumi_file_manager_query.mjs \
  --intent locate_new_doc \
  --doc_type xiaohongshu \
  --platform xiaohongshu \
  --config skills/lumi_file_manager/config.md
```

## Output Contract

- `status`: `ok | confirm_required | failed`
- `resolved_doc_type`
- `resolved_platform`
- `target_paths`
- `reasoning`
- `confidence`

## Guardrails

- 只返回路径建议，不自动创建目录。
- 无法确定类型时返回 `confirm_required`。
- 未命中路由时返回 `failed` 并给出候选键。
