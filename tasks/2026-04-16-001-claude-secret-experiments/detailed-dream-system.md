# Dream System 技术深度解析：自动记忆整理子代理

## 功能概述

**Dream System** 是 Claude Code 的自动记忆管理系统，灵感来源于人类睡眠时整理记忆的生理机制。它在后台自动压缩、整理和优化对话历史，确保长期会话中的上下文保持清晰有效。

### 核心定位
- **产品形态**: 后台运行的记忆整理子代理
- **激活条件**: `feature('REACTIVE_COMPACT')` 或自动压缩触发
- **设计理念**: "让 AI 学会睡觉整理记忆"

---

## 技术架构

### 1. 系统组件架构

```typescript
// 从 src/query.ts 和自动压缩模块推断
interface DreamSystemArchitecture {
  // 触发器层
  triggers: {
    tokenThreshold: number        // Token 阈值触发
    timeBased: boolean           // 时间间隔触发
    manualCommand: boolean       // 手动 /compact 命令
    reactiveMode: boolean       // 被动响应模式
  }
  
  // 分析层
  analyzer: {
    importanceScorer: (message: Message) => number  // 重要性评分
    redundancyDetector: (messages: Message[]) => RedundancyReport
    keyInfoExtractor: (context: Message[]) => KeyInfo[]
  }
  
  // 压缩层
  compressor: {
    summarizer: (messages: Message[]) => SummaryMessage
    archiveManager: (oldMessages: Message[]) => ArchiveReference
    cacheOptimizer: (messages: Message[]) => CacheOptimizedMessages
  }
  
  // 应用层
  applier: {
    messageReplacer: (oldRange: Range, newMessages: Message[]) => void
    boundaryMarker: (compactInfo: CompactInfo) => BoundaryMessage
    memoryRestorer: (archiveId: string) => Message[]
  }
}
```

### 2. 核心算法流程

```typescript
// 从 query.ts 提取的压缩流程
async function dreamCompactFlow(
  messages: Message[],
  context: ToolUseContext
): Promise<CompactResult> {
  // Phase 1: 预处理
  const snipResult = feature('HISTORY_SNIP') 
    ? snipModule.snipCompactIfNeeded(messages)  // 裁剪历史
    : { messages, tokensFreed: 0 }
  
  // Phase 2: 微压缩（缓存优化）
  const microResult = await microcompact(
    snipResult.messages, 
    context,
    querySource
  )
  
  // Phase 3: 上下文折叠（实验性功能）
  if (feature('CONTEXT_COLLAPSE')) {
    const collapseResult = await contextCollapse.applyCollapsesIfNeeded(
      microResult.messages,
      context,
      querySource
    )
    messages = collapseResult.messages
  }
  
  // Phase 4: 主压缩（智能摘要）
  const { compactionResult } = await autocompact(
    messages,
    context,
    config,
    querySource,
    tracking,
    snipResult.tokensFreed
  )
  
  return compactionResult
}
```

### 3. 与查询引擎的集成

```typescript
// src/query.ts:800-900
// Dream System 深度集成在查询循环中

// 每次查询前检查是否需要压缩
const { compactionResult, consecutiveFailures } = await deps.autocompact(
  messagesForQuery,
  toolUseContext,
  { systemPrompt, userContext, systemContext, toolUseContext },
  querySource,
  tracking,
  snipTokensFreed,
)

// 压缩成功后更新状态
if (compactionResult) {
  // 记录压缩指标
  logEvent('tengu_auto_compact_succeeded', {
    originalMessageCount: messages.length,
    compactedMessageCount: /* 计算 */,
    preCompactTokenCount,
    postCompactTokenCount,
    // ... 详细指标
  })
  
  // 生成压缩后消息
  const postCompactMessages = buildPostCompactMessages(compactionResult)
  
  // 更新 task_budget 追踪
  if (params.taskBudget) {
    const preCompactContext = finalContextTokensFromLastResponse(messagesForQuery)
    taskBudgetRemaining = Math.max(
      0,
      (taskBudgetRemaining ?? params.taskBudget.total) - preCompactContext
    )
  }
}
```

---

## 功能特性详解

### 1. 三级压缩策略

#### Level 1: Snip（裁剪）
```typescript
// HISTORY_SNIP 功能
function snipCompactIfNeeded(messages: Message[]): SnipResult {
  // 识别可裁剪的重复/冗余消息
  // 保留 "保护尾部"（最近的重要消息）
  // 返回裁剪后的消息和释放的 Token 数
}
```

**策略**:
- 移除重复的系统提示
- 压缩连续的代码块
- 保留最近 N 条消息的完整上下文

#### Level 2: Microcompact（微压缩）
```typescript
// CACHED_MICROCOMPACT 功能
interface MicrocompactResult {
  messages: Message[]
  compactionInfo?: {
    pendingCacheEdits: PendingCacheEdits
    baselineCacheDeletedTokens: number
    deletedToolIds: string[]
  }
}
```

**特点**:
- 利用 prompt cache 机制
- 标记已缓存内容，减少重复传输
- 延迟边界消息到 API 响应后生成（使用实际 cache_deleted_input_tokens）

#### Level 3: Autocompact（智能摘要）
```typescript
// 主压缩引擎
interface AutocompactConfig {
  // 触发条件
  tokenThreshold: number        // 默认 ~80% 上下文窗口
  maxConsecutiveFailures: number // 防死循环保护
  
  // 压缩策略
  summarizationModel: 'haiku'   // 使用轻量模型生成摘要
  preserveRecentMessages: number // 保留最近 N 条
  preserveImportantTools: string[] // 保留关键工具调用
}
```

**智能决策**:
- 哪些消息可以压缩为摘要
- 哪些工具调用结果必须保留完整
- 如何保持对话连贯性

### 2. 反应式压缩（Reactive Compact）

```typescript
// REACTIVE_COMPACT 功能 - 被动响应模式
interface ReactiveCompact {
  // 错误恢复
  tryReactiveCompact(params: {
    hasAttempted: boolean        // 防止重复尝试
    querySource: string
    aborted: boolean
    messages: Message[]
    cacheSafeParams: CacheSafeParams
  }): Promise<CompactResult | null>
  
  // 错误拦截
  isWithheldPromptTooLong(message: Message): boolean
  isWithheldMediaSizeError(message: Message): boolean
}
```

**触发场景**:
1. API 返回 `prompt_too_long` 错误
2. 媒体文件（图片/PDF）超出大小限制
3. Token 预算耗尽

**恢复流程**:
```
API Error → 拦截 withhold → Reactive Compact → 重试 → 成功/失败
```

### 3. 上下文折叠（Context Collapse）

```typescript
// CONTEXT_COLLAPSE 功能
interface ContextCollapse {
  // 投影视图 - 运行时动态折叠
  projectView(messages: Message[]): CollapsedView
  
  // 提交归档 - 持久化存储
  commitCollapse(messages: Message[], collapsePoints: CollapsePoint[]): void
  
  // 溢出恢复
  recoverFromOverflow(messages: Message[]): RecoveryResult
}
```

**机制**:
- **读取时投影**: 运行时动态隐藏已归档消息
- **跨会话持久**: 折叠状态保存在 `.claude/memory/` 中
- **增量归档**: 新消息达到阈值时自动触发新的折叠点

---

## 代码注释与 TODO 分析

### 已发现的关键注释

```typescript
// src/query.ts:850
// TODO: no need to set toolUseContext.messages during set-up since it is updated here
// 
// 含义：toolUseContext.messages 的初始化可以简化，因为每次查询都会更新
// 状态：代码优化 TODO，不影响功能

// src/query.ts:900-950
// task_budget: capture pre-compact final context window before
// messagesForQuery is replaced with postCompactMessages below.
// iterations[-1] is the authoritative final window (post server tool loops)
//
// 含义：需要在压缩前记录 Token 使用量，用于 task_budget 计算
// 状态：已实现，注释为设计文档

// src/query.ts:1200-1250
// Reactive compact: the streaming loop withheld the error
// (see withheldByCollapse / withheldByReactive above). Try collapse
// drain first (cheap, keeps granular context), then reactive compact
// (full summary).
//
// 含义：反应式压缩的恢复优先级 - 先尝试 Context Collapse（便宜），
//      再尝试 Reactive Compact（完整摘要）
// 状态：已实现，注释为策略文档
```

### 相关功能标志

```typescript
// 从 query.ts 提取
const DREAM_SYSTEM_FEATURES = {
  'REACTIVE_COMPACT': {
    status: '实验性',
    description: '被动响应式压缩，处理 API 错误恢复',
    gate: 'feature(\'REACTIVE_COMPACT\')'
  },
  'CONTEXT_COLLAPSE': {
    status: '实验性', 
    description: '上下文折叠，持久化归档历史消息',
    gate: 'feature(\'CONTEXT_COLLAPSE\')'
  },
  'HISTORY_SNIP': {
    status: '实验性',
    description: '历史裁剪，快速移除冗余消息',
    gate: 'feature(\'HISTORY_SNIP\')'
  },
  'CACHED_MICROCOMPACT': {
    status: '实验性',
    description: '缓存微压缩，利用 prompt cache 优化',
    gate: 'feature(\'CACHED_MICROCOMPACT\')'
  },
  'BG_SESSIONS': {
    status: '实验性',
    description: '后台会话，支持 Dream System 后台运行',
    gate: 'feature(\'BG_SESSIONS\')'
  }
}
```

---

## 完成度评估

### 已完成的组件 ✅

| 组件 | 状态 | 证据 |
|------|------|------|
| Snip 裁剪 | ✅ 完成 | `snipCompactIfNeeded` 已集成 |
| Microcompact | ✅ 完成 | 延迟边界消息 + cache 优化 |
| Autocompact | ✅ 完成 | 完整的事件追踪和指标上报 |
| Reactive Compact | ✅ 完成 | 错误恢复流程完整 |
| Context Collapse | 🟡 实验 | 框架存在，可能还在调优 |
| Task Budget 集成 | ✅ 完成 | Token 预算追踪完整 |

### 待完善的组件 🚧

| 组件 | 状态 | 待办 |
|------|------|------|
| 智能摘要质量 | 🚧 迭代 | 需要更多训练数据优化摘要质量 |
| 多模态压缩 | 🚧 开发 | 图片/PDF 的压缩策略待完善 |
| 跨会话记忆 | 🚧 规划 | 与 `TEAMMEM` 的联动待实现 |
| 用户可控性 | 🚧 设计 | 手动触发 / 自动触发的平衡 |

### 关键 TODO

```typescript
// 唯一发现的显式 TODO（query.ts:850）
// TODO: no need to set toolUseContext.messages during set-up since it is updated here
// 
// 优先级: 低（代码优化）
// 影响: 启动性能微调
```

**结论**: Dream System **核心功能已完成**，主要处于优化迭代阶段。

---

## 技术亮点分析

### 1. 多层降级策略

```
用户无感知
    │
    ▼
Snip（轻量级） ────────────┐
    │                     │
    ▼                     │
Microcompact（缓存优化） ──┤ 逐级尝试，保持对话连贯
    │                     │
    ▼                     │
Context Collapse（归档） ─┤
    │                     │
    ▼                     │
Autocompact（完整摘要） ──┘
    │
    ▼
用户感知（必要时的摘要消息）
```

### 2. Token 预算管理

```typescript
// 与 task_budget 功能的协同
if (params.taskBudget) {
  // 压缩前记录实际消耗
  const preCompactContext = finalContextTokensFromLastResponse(messagesForQuery)
  
  // 更新剩余预算
  taskBudgetRemaining = Math.max(
    0,
    (taskBudgetRemaining ?? params.taskBudget.total) - preCompactContext
  )
  
  // 传递给 API，让服务端也知晓
  // This allows the server to track budget consumption accurately
}
```

### 3. 防死循环保护

```typescript
// consecutiveFailures 机制
if (consecutiveFailures > MAX_CONSECUTIVE_FAILURES) {
  // 停止自动压缩尝试，避免无限循环
  // 回退到用户手动处理
}

// hasAttemptedReactiveCompact 保护
if (hasAttemptedReactiveCompact) {
  // 防止在同一次查询中重复压缩
  // 避免 burning thousands of API calls
}
```

---

## 产品意义分析

### 1. 解决的核心问题

| 问题 | 传统方案 | Dream System |
|------|----------|--------------|
| 长对话记忆衰减 | 手动 /clear | 自动智能压缩 |
| Token 限制 | 粗暴截断 | 分层渐进优化 |
| 上下文丢失 | 完全丢失 | 摘要保留关键信息 |
| API 错误 | 直接报错 | 自动恢复重试 |

### 2. 与 BUDDY 的协同

```
BUDDY (情感层)
    │ 触发条件: 会话即将被压缩
    ▼
发送告别消息: "这段对话太长啦，我要帮你整理一下记忆~"
    │
    ▼
Dream System (执行层)
    │ 执行: 自动压缩
    ▼
恢复后:
BUDDY: "整理完毕！我们继续刚才的话题..."
```

### 3. 竞品对比

| 特性 | Claude Code | Cursor | GitHub Copilot |
|------|-------------|--------|----------------|
| 自动压缩 | ✅ Dream System | ❌ 手动 | ❌ 无 |
| 智能摘要 | ✅ 多层策略 | ⚠️ 简单截断 | ❌ 无 |
| 错误恢复 | ✅ Reactive | ❌ 报错 | ❌ 无 |
| 跨会话记忆 | 🚧 实验 | ❌ 无 | ❌ 无 |

---

## 性能指标

从代码中的 `logEvent` 可提取评估指标：

```typescript
// 压缩成功率
tengu_auto_compact_succeeded

// 压缩效率
originalMessageCount → compactedMessageCount
preCompactTokenCount → postCompactTokenCount

// 恢复成功率  
tengu_reactive_compact_retry // 成功
tengu_query_error // 失败

// 性能开销
compactionInputTokens + compactionOutputTokens // 压缩本身的开销
```

---

## 结论

Dream System 是 Claude Code **最成熟、最复杂的实验性功能**之一。其多层压缩架构、反应式恢复机制、与 Token 预算的深度集成，代表了当前 AI 会话记忆管理的最高水平。

**完善程度**: 🟢 **接近 Production**

**核心优势**:
1. 多层渐进压缩，用户体验平滑
2. 自动错误恢复，鲁棒性强
3. 精细的指标追踪，可观测性高

**待优化点**:
1. 摘要质量（依赖底层模型能力）
2. 多模态内容压缩
3. 用户可控性增强

**预计发布时间**: 2026 年 Q2（功能已相当成熟）

---

*技术文档版本: 1.0*  
*分析日期: 2026-04-16*  
*源码版本: Claude Code 泄露版（query.ts 1500+ 行核心逻辑）*
