# 框图工作流（HTML 生成 + 本地文档嵌入）

## 目标
解决“文中只有表格，没有框图”的问题。

默认方案：
- 在 `diagrams/src/` 写图源码（优先 HTML，支持 Mermaid）。
- 一键构建到 `diagrams/out/`（默认优先 PNG，SVG 兜底）。
- 在 `article.md` 用占位符引用图，自动输出本地发布稿 `article.publish.md`。

## 占位符语法
在正文插入：

```md
{{diagram:ms-three-layer|微软AI三层结构}}
```

规则：
- `ms-three-layer` 对应 `diagrams/src/ms-three-layer.html` 或 `.mmd`
- 竖线右边是图片 alt 文案，可省略

## 一键构建

```bash
./tools/build_diagrams.sh 2026-04-05-002
```

构建结果：
- `publish_queue/<task_id>/diagrams/out/*.png`（优先）
- `publish_queue/<task_id>/diagrams/out/*.svg`（兜底）
- `publish_queue/<task_id>/article.publish.md`

## 本地保存与手动发送
1. 打开 `article.publish.md`
2. 在本地确认图片引用是否完整
3. 你手动复制到 mdnice（或其他编辑器）发送

说明：
- 文档主稿保存在本地，不自动发送到 mdnice。
- 是否上传图片到微信素材库，由你在发布环节手动处理。

## 工具说明
- HTML 框图：无需额外安装，直接可用。
- Mermaid：若已安装 `mmdc` 会渲染真实图；未安装时会生成提示型 SVG 占位图，避免文档断链。
- 发布引用策略：优先 `PNG`，找不到再回退到 `SVG`。
