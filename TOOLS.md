# TOOLS.md - 技能路由

## 能力清单
- `lumi_file_manager`：文档路径规范与新稿落位查询
- `organize`：结构整理、去重、补齐标题层级
- `beautify`：按文档类型做表达优化
- `visualize`：插入内联 HTML 组件
- `selfcheck`：事实漂移/结论漂移/风险核查
- `learn`：仅 HEARTBEAT 触发，不对外暴露

## 组合规则
1. `lumi_file_manager` 优先于 `organize`，先确认路径规则
2. `organize` 优先于 `beautify`
3. `beautify` 应按 `rules_profile_path` 加载 profile 规则
4. `visualize` 按内容自动触发，不强制插入
5. `learn` 不在实时请求中执行

## 类型识别
当 `confidence < 0.70`，返回 `confirm_required` 并附候选类型与理由。

## md2doc Skill
- 目标：在保留内嵌 HTML 主稿的前提下，生成可在 docx 中正常显示图表的发布稿。
- 命令：`./tools/md2doc.sh <markdown_file> [output_dir]`
- 约定：仅渲染 `<!-- HTML2PNG:START ... --> ... <!-- HTML2PNG:END -->` 标记块。
- 输出：`publish.md + assets/*.png + docx`（若安装 pandoc）。

## md2ppt Skill
- 目标：将 Markdown（含内嵌 HTML 图表）转换为可编辑 `pptx`。
- 命令：`./tools/md2ppt.sh <markdown_file> [output_dir] [layout] [theme]`
- 约定：复用 `HTML2PNG` 标记块渲染图表后再入页。
- 输出：`ppt.md + assets/*.png + pptx`。
