---
name: publish-wechat
description: "Use this skill when user wants to optimize and save content to WeChat draft with mdnice as the single editing source."
metadata:
  platform:
    id: wechat_mp
    name: 微信公众号
    url: https://mp.weixin.qq.com
  requires:
    tools: ["browser"]
    files: ["publish_queue/<task_id>/article.md"]
  actions:
    - id: publish
      input: ["task_id?", "title?", "source_path?"]
      output: ["memory/publish-wechat/state.yaml"]
---

# publish-wechat

## Purpose
完成公众号内容优化与草稿保存准备，主稿在 mdnice 单文档迭代，不新增多份版本文档。

## Single Source of Truth
- mdnice 文档是正文唯一来源。
- 命名强制：`[task_id] 标题`
- 同 task_id 不允许新增 v2/v3/最终版文档。

## Workflow
1. 若没有 task_id，自动生成 task_id 并写入状态文件。
2. 打开 mdnice 与公众号编辑器页面。
3. 在 mdnice 原地优化正文：段落、标题层级、术语白话解释、结尾 3 条可执行动作。
4. 在 mdnice 保存后，提示用户点击“复制到公众号”。
5. 用户切换到公众号编辑器粘贴并保存草稿。
6. 用户回执“已保存”后，更新状态为 `PACKAGED`（并记录 `draft.saved=true`）。

## Human Gate
以下步骤必须人工完成：
- 在 mdnice 点击“复制到公众号”
- 在公众号编辑器粘贴
- 点击“保存为草稿”
- 最终“发表”确认

## State File
状态文件路径：`memory/publish-wechat/state.yaml`

关键字段：
- `task_id`
- `status`: `NEW | EDITING | NEEDS_INPUT | PACKAGED`
- `mdnice.doc_id`
- `mdnice.url`
- `content.title`
- `content.word_count`
- `next_action`

## Fail-safe
- 若草稿正文为空，状态回退为 `NEEDS_INPUT`，并提示重新粘贴后保存。
- 若流程中断，可基于 `state.yaml` 继续。
