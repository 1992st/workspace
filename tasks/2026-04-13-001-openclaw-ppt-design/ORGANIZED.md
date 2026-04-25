# 文件整理清单 - 2026-04-13-001-openclaw-ppt-design
# 生成时间: 2026-04-16
# 执行命令: rm -rf drafts/

## ✅ 保留文件（根目录）

| 文件 | 用途 | 说明 |
|------|------|------|
| 01-cover.html | 封面页 | Apple 风格，简洁专业 |
| 09-agent-talk.html | Agent杂谈 | 5大实验性功能卡片 |
| generate_pptx.py | PPT生成脚本 | 11页完整版，含Agent Talk |
| task.md | 任务文档 | 最新状态 REVIEW_READY |
| SPEECH_SCRIPT.md | 演讲稿 | 20-25分钟完整脚本 |
| README.md | 项目说明 | 使用指南 |

## ❌ 废弃文件（待删除 drafts/）

| 文件 | 问题 | 替代方案 |
|------|------|----------|
| drafts/01-cover.html | 风格花哨（beam动画） | 使用根目录 01-cover.html |
| drafts/generate_pptx.py | 10页旧版，路径错误，RgbColor大小写错误 | 使用根目录 generate_pptx.py |

## 关键差异对比

### 封面对比
- 保留: /01-cover.html → ring+dot 装饰，Apple 极简风格
- 废弃: drafts/01-cover.html → beam+grid 动画，过于花哨

### PPT脚本对比
- 保留: /generate_pptx.py → 11页，含Agent Talk，RGBColor标准，路径正确
- 废弃: drafts/generate_pptx.py → 10页，无Agent Talk，RgbColor错误，路径指向dev-topics

## 手动清理命令

```bash
cd /Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-13-001-openclaw-ppt-design

# 1. 备份（可选）
cp -r drafts/ drafts_backup/

# 2. 删除废弃文件夹
rm -rf drafts/

# 3. 验证结果
ls -la

# 预期输出:
# 01-cover.html
# 09-agent-talk.html
# generate_pptx.py
# task.md
# SPEECH_SCRIPT.md
# README.md
# ORGANIZED.md (本文件)
```

## 最终目录结构

```
2026-04-13-001-openclaw-ppt-design/
├── 01-cover.html              # Apple风格封面
├── 09-agent-talk.html         # Agent杂谈
├── generate_pptx.py           # 11页PPT生成
├── task.md                    # 任务状态
├── SPEECH_SCRIPT.md           # 演讲稿
├── README.md                  # 使用说明
└── ORGANIZED.md               # 整理记录
```

---

状态: 已整理，等待手动删除 drafts/
整理者: Agent观察室
时间: 2026-04-16
