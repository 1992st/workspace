# Agent 小茶馆 - 平台化技能架构重构计划

## A/B 两案评估

### A 案：渐进式增强（推荐）
在现有架构上逐步添加平台技能模块，保持向后兼容，优先解决公众号发布痛点。

### B 案：完全重构
重新设计整个技能系统，引入平台抽象层，长期更灵活但投入大。

**推荐案：A 案渐进式增强**
理由：现有系统可用，公众号需求明确，渐进式交付价值快，避免过度设计。

---

## 核心问题诊断

### 现状问题
| 问题 | 影响 | 优先级 |
|------|------|--------|
| 平台特性硬编码在生成逻辑中 | 新增平台需改多处代码 | P0 |
| 无标准化输出格式 | 同一内容不同平台需重复劳动 | P0 |
| 主题/样式与内容耦合 | 换风格需重写 | P1 |
| 缺乏平台反馈学习 | 发布后效果无法回流优化 | P2 |

### 目标架构
```
┌─────────────────────────────────────────────────────────────┐
│                    Content Generation                        │
│                      (内容生成核心)                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  WeChat Skill │   │  Feishu Skill │   │  X/Thread Skill│
│   (公众号)     │   │    (飞书)      │   │   (Twitter)   │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Formatters   │   │  Formatters   │   │  Formatters   │
│  - HTML       │   │  - Markdown   │   │  - Thread     │
│  - mdnice     │   │  - Card       │   │  - Image      │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## Phase 1：平台技能基础（1-2天）

### 1.1 创建技能目录结构
```
skills/
├── _core/                      # 技能核心框架
│   ├── PlatformSkill.ts        # 平台技能基类
│   ├── ContentFormatter.ts     # 格式化器基类
│   └── types.ts                # 共享类型定义
├── wechat-mp/                  # 微信公众号技能
│   ├── SKILL.md                # 技能文档
│   ├── index.ts                # 技能入口
│   ├── formatters/
│   │   ├── mdnice.ts           # Markdown Nice 格式
│   │   └── html.ts             # 原生 HTML 格式
│   └── templates/
│       ├── tech-blog.ts        # 技术博客模板
│       └── news-brief.ts       # 快讯模板
├── feishu-doc/                 # 飞书文档技能（预留）
└── x-thread/                   # X/Twitter Thread（预留）
```

### 1.2 核心抽象定义
```typescript
// skills/_core/types.ts

interface PlatformSkill {
  id: string;                    // 平台标识
  name: string;                  // 显示名称
  supportedFormats: string[];    // 支持的输出格式
  
  // 内容适配
  adapt(content: Content): AdaptedContent;
  
  // 格式化输出
  format(content: AdaptedContent, format: string): string;
  
  // 验证内容
  validate(content: Content): ValidationResult;
}

interface Content {
  title: string;
  body: string;                  // Markdown
  metadata: ContentMetadata;
  assets?: Asset[];              // 图片等资源
}

interface AdaptedContent {
  title: string;
  body: string;                  // 平台适配后的内容
  format: string;                // 目标格式
  platform: string;              // 目标平台
  warnings?: string[];           // 适配警告
}
```

### 1.3 公众号技能实现
位置：`/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/skills/wechat-mp/`

**文件清单**：
- `SKILL.md` - 技能说明和使用指南
- `index.ts` - 技能主入口
- `formatters/mdnice.ts` - Markdown Nice 格式生成
- `templates/tech-blog.ts` - 技术文章模板
- `templates/news-brief.ts` - 快讯模板

---

## Phase 2：文档生成优化（2-3天）

### 2.1 模板系统
```
templates/
├── wechat-mp/
│   ├── tech-blog/
│   │   ├── template.md         # 模板定义
│   │   ├── style.css           # 自定义样式
│   │   └── example.md          # 示例文档
│   └── news-brief/
│       ├── template.md
│       └── example.md
```

### 2.2 内容生成工作流优化
```
当前流程：
内容 → 手动选格式 → 生成 → 手动复制 → 排版工具 → 粘贴

优化后流程：
内容 → 指定平台+模板 → 自动生成多格式 → 选择最佳 → 一键复制
```

### 2.3 具体改进

#### A. 多格式并行生成
生成内容时，同时输出：
- `article.md` - Markdown 原稿
- `article.mdnice.md` - Markdown Nice 优化版
- `article.meta.json` - 元数据（标题/摘要/标签）
- `article.checklist.md` - 发布检查清单

#### B. 平台感知提示词
```markdown
# 系统提示词（平台感知版）

你是 Agent 小茶馆的内容助手。

## 当前平台
{{platform}} = wechat-mp

## 平台特性
- 最佳标题长度：16-20字
- 段落长度：手机3-4行为宜
- 代码块：需指定语言高亮
- 图片：需先上传素材库

## 输出格式
请生成以下内容：
1. article.md - 标准 Markdown
2. article.mdnice.md - 针对 mdnice 优化
3. meta.json - 标题/摘要/标签
```

#### C. 记忆增强
在 `MEMORY.md` 中添加平台反馈：
```markdown
## 平台反馈记录

### 微信公众号
- 技术类文章最佳发布时间：周二/周四晚8点
- 标题含数字打开率提升15%
- 代码块过长影响阅读，需折叠或分段
```

---

## Phase 3：工具集成（1-2天）

### 3.1 CLI 工具增强
```bash
# 生成指定平台内容
./tools/generate.sh --platform wechat-mp --template tech-blog --input topic.md

# 输出生成
/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/publish_queue/YYYYMMDD-XXX/
├── article.md
├── article.mdnice.md
├── meta.json
└── checklist.md
```

### 3.2 自动化辅助
- **图片上传**：调用微信素材 API，自动获取 media_id
- **草稿创建**：调用 `add_draft` API，自动创建草稿
- **预览链接**：生成临时预览链接供审核

### 3.3 浏览器集成
保留当前浏览器工具，用于：
- 登录态维护
- 最终发表确认（无法绕过微信安全）
- 发布后数据抓取（阅读/点赞/在看数）

---

## Phase 4：反馈学习（长期）

### 4.1 数据收集
```
memory/platform-feedback/
├── wechat-mp/
│   ├── 2025-04.json          # 月度数据
│   └── insights.md           # 洞察总结
```

### 4.2 自动优化
- 追踪哪些标题打开率高 → 优化标题生成策略
- 追踪哪些内容分享率高 → 优化内容结构
- 追踪最佳发布时间 → 智能推荐发布时间

---

## 实施计划

| Phase | 任务 | 预计时间 | 优先级 |
|-------|------|----------|--------|
| 1.1 | 创建技能目录结构 | 2h | P0 |
| 1.2 | 实现公众号技能 | 4h | P0 |
| 2.1 | 模板系统设计 | 3h | P1 |
| 2.2 | 多格式生成 | 4h | P1 |
| 2.3 | 记忆增强 | 2h | P2 |
| 3.1 | CLI 工具更新 | 3h | P1 |
| 3.2 | API 自动化调研 | 4h | P2 |
| 4.1 | 反馈数据收集设计 | 2h | P3 |

**总计**：约 2-3 天完成核心功能，1 周达到可用状态。

---

## 立即开始（下一步）

如果你同意这个计划，我可以立即开始：

1. **Phase 1.1**：创建 `skills/` 目录结构和基类定义
2. **Phase 1.2**：实现公众号技能（基于现有发布规范）
3. **Phase 2.1**：创建首个模板（技术博客模板）

确认后，我会：
1. 创建技能目录
2. 迁移现有发布规范到技能系统
3. 更新文章生成工作流

**确认命令**：`开始重构计划` 或 `先做 Phase 1`