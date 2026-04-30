---
version: 1
precedence:
  - platform
  - type
  - default
default_profile: prd-default
supported_doc_types:
  - wechat
  - xiaohongshu
  - code-doc
  - prd
supported_platforms:
  - wechat
  - xiaohongshu
  - internal
required_sections:
  - Knowledge
  - Beautify Dos
  - Beautify Donts
  - Visual Triggers
  - Selfcheck Focus
profiles:
  xiaohongshu-post:
    doc_type: xiaohongshu
    platform: xiaohongshu
    rules_profile_path: rulebook/profiles/xiaohongshu-post.md
  wechat-article:
    doc_type: wechat
    platform: wechat
    rules_profile_path: rulebook/profiles/wechat-article.md
  code-doc-default:
    doc_type: code-doc
    platform: internal
    rules_profile_path: rulebook/profiles/code-doc-default.md
  prd-default:
    doc_type: prd
    platform: internal
    rules_profile_path: rulebook/profiles/prd-default.md
---

# Rulebook Index

统一管理文档美化规则来源与合并顺序。

## Merge Order

当同一规则键在多个层级出现时，按以下顺序覆盖：

1. `platform` 规则
2. `type` 规则
3. `default` 规则

## Profile Usage

`doc-beautify` 通过 `rules_profile_path` 指向 profile 文件。
profile 再引用 type/platform 规则文件，实现“按平台+类型”联动。
