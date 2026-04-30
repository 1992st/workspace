---
name: md2ppt
description: "Convert markdown with embedded HTML chart blocks into editable pptx slides."
metadata:
  requires:
    tools: ["exec", "fs"]
  inputs:
    - file_path
    - output_dir (optional)
    - layout (optional, default 16:9)
    - theme (optional, default business-light)
---

# md2ppt

## Purpose
实现 `md -> pptx` 且保留图表可见性与文本可编辑性：
1. 将 Markdown 内嵌 HTML 图表渲染为 PNG
2. 将 HTML 区块替换为 Markdown 图片引用
3. 将 Markdown 分页并导出可编辑 `pptx`

## Required Block Syntax
仅处理以下标记块（避免误伤正文 HTML）：

```md
<!-- HTML2PNG:START id=chart-001 -->
<div style="...">...</div>
<!-- HTML2PNG:END -->
```

- `id` 可选；未提供时自动生成
- 区块内部支持内联 HTML/CSS

## Execution
使用命令：

```bash
./tools/md2ppt.sh <markdown_file> [output_dir] [layout] [theme]
```

默认参数：
- `layout=16:9`（可选 `4:3`）
- `theme=business-light`

产物：
- `<output_dir>/assets/*.png`：渲染后的图表图片
- `<output_dir>/<name>.ppt.md`：替换后的中间稿
- `<output_dir>/<name>.pptx`：最终可编辑幻灯片

## Guardrails
- 原始 Markdown 文件不改写
- 渲染失败时保留未解析提示并报错
- 失败块必须输出清单，不静默忽略
