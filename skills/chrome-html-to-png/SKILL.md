---
name: chrome-html-to-png
description: "Convert local HTML to PNG via Chrome/Chromium headless on macOS or Linux. Use script-first for standard inputs, switch to direct Chrome command for custom flags or non-standard needs, and always choose a context-appropriate window-size."
---

# chrome-html-to-png

目标：把本地 HTML 渲染为 PNG。

## 执行规则
1. 标准需求优先脚本（仅需 `--html --out --window-size --chrome`）。
2. 需要额外 Chrome 参数或特殊行为时，直接调用 Chrome/Chromium。

## 标准路径（脚本优先）

```bash
bash skills/chrome-html-to-png/scripts/render_html_to_png.sh \
  --html "/abs/path/input.html" \
  --out "/abs/path/output.png" \
  --window-size "1080,1920"
```

`--window-size` 是标准写法；脚本兼容 `--windows-size`（容错别名）。

## 自定义路径（直接命令）
macOS:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --hide-scrollbars \
  --window-size=1080,1920 --screenshot="/abs/path/output.png" \
  "file:///abs/path/input.html"
```

Linux:

```bash
google-chrome \
  --headless=new \
  --hide-scrollbars \
  --window-size=1080,1920 --screenshot="/abs/path/output.png" \
  "file:///abs/path/input.html"
```

## window-size 选择
- 小红书竖图：`1080,1440` 或 `1080,1920`
- 公众号长图：`1080,1920` 或 `1242,2208`
- PPT/横版：`1920,1080`
- 未给渠道：默认 `1080,1920`，并回显这是默认假设

## 最小排错
- `no such file or directory`：路径或引号错误
- `.app command not found`：执行了 `.app` 目录而非 `.../Contents/MacOS/Google Chrome`
- Linux 无 `google-chrome`：改试 `chromium` 或 `chromium-browser`
