# Agent 小茶馆 - 平台发布技能系统设计（OpenClaw 风格）

## 设计原理（借鉴 OpenClaw）

### 1. 声明式触发（Declarative Trigger）
OpenClaw 通过 `description` 字段决定何时调用技能。同理，平台技能通过描述平台特征来触发：

```yaml
description: 'Generate content optimized for WeChat Official Account (微信公众号). Use when: user asks to publish to WeChat, format for 公众号, or mentions WeChat MP. Features: rich text, specific title length (16-20 chars), mobile-first paragraphs, code blocks need language tags.'
```

### 2. YAML Frontmatter + Markdown 结构
```yaml
---
name: wechat-mp-publisher
description: '...'
metadata:
  platform:
    id: wechat-mp
    name: 微信公众号
    emoji: 💬
  requires:
    files: ["article.md", "cover.png"]
  formats:
    - mdnice      # Markdown Nice 格式
    - html        # 原生 HTML
    - preview     # 预览链接
  templates:
    - tech-blog
    - news-brief
    - deep-dive
---
```

### 3. 平台感知的内容生成
类似 OpenClaw 的 tool 选择逻辑，根据平台特征自动调整内容：

| 平台特征 | 影响 |
|---------|------|
| 移动端阅读 | 段落长度控制在 3-4 行 |
| 无 Markdown 原生支持 | 生成 mdnice 兼容格式 |
| 标题 64 字限制 | 推荐 16-20 字最佳长度 |
| 代码块需高亮 | 强制要求语言标识 |

### 4. 记忆集成（Memory Integration）
类似 OpenClaw 的 `MEMORY.md`，平台技能自动读写：

```
memory/platform/wechat-mp/
├── preferences.md      # 用户偏好（发布时间、主题风格）
├── performance.md      # 历史数据（打开率、分享率）
├── templates/          # 自定义模板
└── insights.md         # 学习洞察
```

---

## 新架构设计

### 目录结构（OpenClaw 风格）

```
skills/
├── _manifest.yaml              # 技能清单（类似 OpenClaw 的 available_skills）
├── publish-wechat-mp/          # 微信公众号发布技能
│   ├── SKILL.md                # 技能定义（OpenClaw 标准格式）
│   ├── templates/
│   │   ├── tech-blog.md        # 技术博客模板
│   │   ├── news-brief.md       # 快讯模板
│   │   └── _registry.yaml      # 模板注册表
│   ├── formatters/
│   │   ├── mdnice.ts           # Markdown Nice 格式化器
│   │   └── html.ts             # HTML 格式化器
│   └── README.md               # 使用说明
├── publish-feishu/             # 飞书发布技能（预留）
└── publish-x-thread/           # X Thread 发布技能（预留）
```

### SKILL.md 标准格式

```yaml
---
name: publish-wechat-mp
description: 'Generate and format content for WeChat Official Account (微信公众号). Use when: user asks to publish to WeChat, format for 公众号, or mentions WeChat MP. Features: rich text, mobile-optimized paragraphs, code highlighting, mdnice compatible output.'
metadata:
  platform:
    id: wechat-mp
    name: 微信公众号
    emoji: 💬
    url: https://mp.weixin.qq.com
  requires:
    tools: ["browser"]
    files: ["article.md"]
  formats:
    - id: mdnice
      name: Markdown Nice
      ext: .mdnice.md
    - id: html
      name: HTML
      ext: .html
  templates:
    - id: tech-blog
      name: 技术博客
      description: 深度技术文章，适合源码分析、架构解读
    - id: news-brief
      name: 快讯简报
      description: 短平快的行业动态，适合热点追踪
    - id: deep-dive
      name: 深度剖析
      description: 长文深度分析，适合系列文章
---

# 微信公众号发布技能

## 快速开始

### 生成内容
```
生成一篇关于 [主题] 的文章，使用 tech-blog 模板，发布到公众号
```

### 输出文件
生成后会在 `publish_queue/YYYYMMDD-XXX/` 下创建：
- `article.md` - Markdown 原稿
- `article.mdnice.md` - Markdown Nice 优化版
- `meta.json` - 标题/摘要/标签
- `checklist.md` - 发布检查清单

## 平台特性

### 格式限制
| 特性 | 限制 | 处理方式 |
|------|------|----------|
| 标题 | 64 字 | 推荐 16-20 字 |
| 段落 | 手机 3-4 行 | 自动分段 |
| 代码块 | 需语言标识 | 强制添加 |
| 图片 | 需上传素材库 | 提示用户 |

### 最佳实践
- 技术文章：周二/周四晚 8 点发布
- 标题含数字：打开率 +15%
- 开头钩子：前 3 句抓住读者
- 结尾 CTA：3 条可执行动作

## 模板说明

### tech-blog（技术博客）
适合：源码分析、架构解读、技术深度文章
结构：
1. 钩子开头（问题/冲突）
2. 背景铺垫
3. 核心分析
4. 代码示例
5. 总结 + 3 条可执行动作

### news-brief（快讯简报）
适合：行业动态、热点追踪、事件解读
结构：
1. 一句话概括
2. 事件经过
3. 关键要点（ bullet 列表）
4. 影响分析
5. 3 条可执行动作

## 发布流程

```
1. 生成内容 → 保存到 publish_queue/
2. 复制 article.mdnice.md 到 mdnice 编辑器
3. 选择主题 → 复制到公众号
4. 设置封面 → 人工确认
5. 点击发表
```

## 记忆集成

技能自动读取和写入：
- `memory/platform/wechat-mp/preferences.md` - 发布偏好
- `memory/platform/wechat-mp/performance.md` - 历史数据
- `memory/platform/wechat-mp/insights.md` - 学习洞察

## 工具命令

### CLI
```bash
# 生成内容
./tools/publish.sh --platform wechat-mp --template tech-blog --topic "Claude Code leak"

# 打开编辑器
./tools/publish.sh open wechat-mp
```

### 浏览器集成
```bash
# 打开公众号后台
browser open https://mp.weixin.qq.com
```
```

---

## 与 OpenClaw 技能系统的对比

| OpenClaw | Agent 小茶馆（新设计） |
|---------|----------------------|
| `name` | `name` |
| `description`（触发条件） | `description`（平台识别） |
| `metadata.openclaw` | `metadata.platform` |
| `metadata.requires`（bins） | `metadata.requires`（tools/files） |
| `metadata.install` | `metadata.formats/templates` |
| 正文（使用指南） | 正文（平台特性+模板说明） |
| `available_skills` 注入 | `skills/_manifest.yaml` 注册 |

---

## 迁移计划（基于新设计）

### Phase 1：创建技能框架（2h）
1. 创建 `skills/_manifest.yaml` - 技能清单
2. 创建 `skills/publish-wechat-mp/SKILL.md` - 技能定义
3. 迁移现有发布规范到技能正文

### Phase 2：模板系统（4h）
1. 创建 `templates/tech-blog.md` - 技术博客模板
2. 创建 `templates/news-brief.md` - 快讯模板
3. 创建 `templates/_registry.yaml` - 模板注册表

### Phase 3：格式化器（4h）
1. 创建 `formatters/mdnice.ts` - Markdown Nice 格式
2. 创建 `formatters/html.ts` - HTML 格式
3. 实现自动格式选择

### Phase 4：记忆集成（2h）
1. 创建 `memory/platform/wechat-mp/` 结构
2. 实现偏好读取/写入
3. 实现性能数据收集

---

## 下一步

确认这个设计后，我将：
1. 创建 `skills/_manifest.yaml`
2. 创建 `skills/publish-wechat-mp/SKILL.md`
3. 创建首个模板 `tech-blog`

确认命令：`按新设计开始` 或 `先做 Phase 1`
