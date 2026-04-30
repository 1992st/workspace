# SKILL.md - doc-beautify

## Purpose
执行文档整理、美化与可视化插入，保持事实不漂移。

## Input
- file_path (required)
- doc_type_hint (optional)
- rules_profile_path (optional, recommended)
- organize_first (optional, default true)

## Steps
1. 调用 `lumi_file_manager` 校验文件路径或返回新稿推荐路径
2. 立即备份原文件到 `backups/`
3. 识别类型并给出置信度
4. 低置信度返回 `confirm_required`
5. 通过 `rules_profile_path` 载入 profile 规则（未提供时回退默认 profile）
6. 先 `organize` 后 `beautify`
7. 必要时插入内联 HTML 可视化组件
8. `selfcheck` 后原子替换
9. 写入学习记录

## Guardrails
- 不修改核心观点、事实、结论
- 不新增未经验证信息
- 不输出额外分叉文档，默认回写原文
