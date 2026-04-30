---
name: md2doc
description: "Convert markdown with embedded HTML chart blocks into docx by rendering HTML blocks to PNG first, then replacing blocks with markdown images."
metadata:
  requires:
    tools: ["exec", "fs"]
  inputs:
    - file_path
    - output_dir (optional)
    - keep_intermediate (optional)
---

# md2doc

## Purpose
实现 `md -> docx` 且保留图表可见性：
1. 先把 Markdown 内嵌 HTML 图表渲染为 PNG
2. 再把 HTML 区块替换为 Markdown 图片引用
3. 最后导出 docx

## Required Block Syntax
仅处理以下标记块（避免误伤正文 HTML）：

```md
<!-- HTML2PNG:START id=chart-001 -->
<div style="...">...</div>
<!-- HTML2PNG:END -->
```

- `id` 可选；未提供时自动生成 `chart-<n>`
- 区块内部支持任意 HTML/CSS（建议内联样式）

## Execution
使用命令：

```bash
./tools/md2doc.sh <markdown_file> [output_dir]
```

产物：
- `<output_dir>/assets/*.png`：渲染后的图表图片
- `<output_dir>/<name>.publish.md`：替换后的发布稿
- `<output_dir>/<name>.docx`：最终文档（若本机安装 pandoc）

## Guardrails
- 原始 Markdown 文件不改写
- 渲染失败时保留原 HTML 块并报错
- docx 导出失败时至少保留 `publish.md + png`
