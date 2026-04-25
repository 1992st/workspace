# Swarm/Coordinator 技术深度解析：多智能体协调系统

## 功能概述

**Swarm/Coordinator** 是 Claude Code 的多智能体协作系统，支持并行子代理（Sub-agents）协同工作，解决复杂任务。它是从单线程对话向分布式 AI 工作流的演进。

### 核心定位
- **产品形态**: 多代理并行执行引擎
- **激活条件**: `feature('COORDINATOR_MODE')` 或 `--agent-teams` 标志
- **设计理念**: "一个 Claude 不够，要一群 Claude 协作"

---

## 技术架构

### 1. 核心组件架构

```typescript
// 从 query.ts 和 tools/AgentTool 推断
interface SwarmArchitecture {
  // 协调层
  coordinator: {
    taskDecomposer: TaskDecomposer      // 任务分解器
    agentAllocator: AgentAllocator     // 代理分配器
    dependencyManager: DependencyManager // 依赖管理
    resultAggregator: ResultAggregator // 结果聚合
  }
  
  // 代理层
  agents: {
    agentPool: AgentPool               // 代理池
    agentSpawner: AgentSpawner        // 代理生成器
    agentMonitor: AgentMonitor         // 代理监控
    messageBus: MessageBus             // 消息总线
  }
  
  // 工具层
  tools: {
    agentTool: AgentTool               // 代理调用工具
    parallelExecutor: ParallelExecutor // 并行执行器
    syncPrimitives: SyncPrimitives    // 同步原语
  }
}
```

### 2. Agent Tool 核心实现

```typescript
// src/tools/AgentTool/ 推断
interface AgentToolConfig {
  // 代理定义
  agentDefinitions: {
    activeAgents: AgentDefinition[]    // 活跃代理
    allowedAgentTypes: string[]        // 允许的代理类型
  }
  
  // 执行配置
  options: {
    maxConcurrentAgents: number       // 最大并发数
    agentTimeout: number              // 代理超时
    inheritContext: boolean           // 是否继承上下文
    shareMemory: boolean              // 是否共享记忆
  }
}

// 代理执行
interface AgentExecution {
  agentId: string
  agentType: string
  prompt: string
  context: SharedContext
  result: Promise<AgentResult>
}
```

### 3. 并行工具执行

```typescript
// query.ts:1100 - Streaming Tool Executor
class StreamingToolExecutor {
  constructor(
    tools: Tool[],
    canUseTool: CanUseToolFn,
    toolUseContext: ToolUseContext
  )
  
  addTool(toolBlock: ToolUseBlock, assistantMessage: AssistantMessage): void
  getCompletedResults(): ToolResult[]
  getRemainingResults(): AsyncGenerator<ToolUpdate>
  discard(): void  // 放弃未完成的工具
}

// 并发控制
function getMaxToolUseConcurrency(): number {
  return parseInt(process.env.CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY || '', 10) || 10
}
```

---

## 功能特性详解

### 1. 任务分解策略

```typescript
interface TaskDecomposer {
  // 分解策略
  strategies: {
    // 按文件分解
    byFile: (task: string, files: string[]) => SubTask[]
    
    // 按模块分解
    byModule: (task: string, modules: Module[]) => SubTask[]
    
    // 按阶段分解
    byPhase: (task: string, phases: string[]) => SubTask[]
    
    // 混合分解
    hybrid: (task: string, context: Context) => SubTask[]
  }
}

interface SubTask {
  id: string
  description: string
  assignedAgent: string
  dependencies: string[]  // 依赖的其他子任务
  estimatedComplexity: number
  contextScope: ContextScope
}
```

**分解示例**:
```
主任务: "重构整个代码库"
├── 子任务1: "分析依赖关系" (Agent: analyzer)
├── 子任务2: "重构模块A" (Agent: refactoer, 依赖: 子任务1)
├── 子任务3: "重构模块B" (Agent: refactoer, 依赖: 子任务1)
├── 子任务4: "更新测试" (Agent: tester, 依赖: 子任务2,3)
└── 子任务5: "生成文档" (Agent: writer, 依赖: 子任务2,3,4)
```

### 2. 代理类型系统

```typescript
// 从 bootstrap/state.ts:98 推断
interface AgentDefinition {
  agentId: string
  agentType: string           // 代理类型标识
  color: AgentColorName       // 终端颜色标识
  capabilities: string[]     // 能力列表
  specialization: string      // 专业领域
}

// 预定义代理类型（推断）
const BUILTIN_AGENT_TYPES = {
  'analyzer': {
    description: '代码分析专家',
    capabilities: ['code-analysis', 'dependency-graph', 'complexity-calc']
  },
  'refactorer': {
    description: '重构专家',
    capabilities: ['code-edit', 'pattern-migration', 'type-fix']
  },
  'tester': {
    description: '测试专家',
    capabilities: ['test-gen', 'test-run', 'coverage-analysis']
  },
  'writer': {
    description: '文档专家',
    capabilities: ['doc-gen', 'comment-update', 'readme-sync']
  },
  'debugger': {
    description: '调试专家',
    capabilities: ['error-analysis', 'breakpoint-suggest', 'log-analysis']
  }
}
```

### 3. 并发控制机制

```typescript
// 并发限制配置
interface ConcurrencyConfig {
  // 全局限制
  globalMaxConcurrent: number    // 默认: 4 (agents.defaults.maxConcurrent)
  
  // 子代理限制
  subagentMaxConcurrent: number  // 默认: 8 (agents.defaults.subagents.maxConcurrent)
  
  // 工具并发
  toolConcurrency: number          // 默认: 10 (CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY)
  
  // 查询深度限制
  maxQueryDepth: number          // 防止无限递归
  maxTurns: number               // 单代理最大轮数
}

// 依赖解析与调度
class DependencyManager {
  buildDependencyGraph(tasks: SubTask[]): DAG
  
  getReadyTasks(): SubTask[]      // 获取可执行的子任务
  
  markCompleted(taskId: string): void
  
  detectCircularDependencies(): boolean  // 循环依赖检测
}
```

### 4. 结果聚合策略

```typescript
interface ResultAggregator {
  // 聚合策略
  strategies: {
    // 串联聚合
    sequential: (results: AgentResult[]) => AggregatedResult
    
    // 投票聚合
    voting: (results: AgentResult[]) => AggregatedResult
    
    // 合并聚合
    merge: (results: AgentResult[]) => AggregatedResult
    
    // 优先级聚合
    priority: (results: AgentResult[], priorities: number[]) => AggregatedResult
  }
  
  // 冲突解决
  conflictResolver: {
    detectConflicts: (results: AgentResult[]) => Conflict[]
    resolve: (conflicts: Conflict[]) => Resolution
  }
}
```

---

## 代码注释与功能标志

### 关键代码引用

```typescript
// query.ts:15 - Agent Teams 相关
const autoModeStateModule = feature('TRANSCRIPT_CLASSIFIER') ? ...

// query.ts:1100 - Streaming 工具执行（支持并行）
const streamingToolExecutor = useStreamingToolExecution
  ? new StreamingToolExecutor(tools, canUseTool, toolUseContext)
  : null

// bootstrap/state.ts:98 - 代理颜色管理（用于区分多个代理）
agentColorMap: Map<string, AgentColorName>
agentColorIndex: number

// bootstrap/state.ts:180 - 代理追踪
invokedSkills: Map<string, {
  skillName: string
  skillPath: string
  content: string
  invokedAt: number
  agentId: string | null
}>

// utils/agentTeams.ts（推断）- Agent Teams 标志检测
function isAgentTeamsFlagSet(): boolean {
  return process.argv.includes('--agent-teams')
}
```

### 功能标志

```typescript
const SWARM_FEATURES = {
  'COORDINATOR_MODE': {
    status: '实验性',
    description: '多智能体协调模式（Swarm）',
    gate: "feature('COORDINATOR_MODE')"
  },
  
  'AGENT_TEAMS': {
    status: '实验性',
    description: '团队协作模式（CLI 标志）',
    gate: 'process.argv.includes("--agent-teams")',
    note: '受 killswitch 控制'
  },
  
  'BG_SESSIONS': {
    status: '实验性',
    description: '后台会话支持',
    gate: "feature('BG_SESSIONS')"
  },
  
  'TRANSCRIPT_CLASSIFIER': {
    status: '实验性',
    description: '代理工作分类器',
    gate: "feature('TRANSCRIPT_CLASSIFIER')"
  }
}
```

### 事件日志（指标收集）

```typescript
// query.ts 中的 Swarm 相关日志
logEvent('tengu_streaming_tool_execution_used', {
  tool_count: toolUseBlocks.length,
  queryChainId,
  queryDepth: queryTracking.depth
})

logEvent('tengu_orphaned_messages_tombstoned', {
  orphanedMessageCount: assistantMessages.length,
  queryChainId,
  queryDepth: queryTracking.depth
})

// 子代理追踪
logEvent('tengu_query_before_attachments', {
  messagesForQueryCount: messagesForQuery.length,
  assistantMessagesCount: assistantMessages.length,
  toolResultsCount: toolResults.length,
  queryChainId,
  queryDepth: queryTracking.depth
})
```

---

## 完成度评估

### 已完成的组件 ✅

| 组件 | 状态 | 证据 |
|------|------|------|
| Agent Tool 框架 | ✅ 完成 | StreamingToolExecutor 实现完整 |
| 并发控制 | ✅ 完成 | `getMaxToolUseConcurrency()` 和配置系统 |
| 代理颜色管理 | ✅ 完成 | `agentColorMap` 和 `agentColorIndex` |
| 技能调用追踪 | ✅ 完成 | `invokedSkills` Map 结构 |
| 查询深度追踪 | ✅ 完成 | `queryTracking.depth` |
| CLI 标志 | ✅ 完成 | `--agent-teams` 检测 |

### 待完善的组件 🚧

| 组件 | 状态 | 待办 |
|------|------|------|
| Coordinator 核心 | 🚧 框架 | 任务分解、依赖管理待实现 |
| Agent Pool | 🚧 设计 | 代理生命周期管理 |
| Message Bus | 🚧 设计 | 代理间通信机制 |
| 冲突解决 | 🚧 规划 | 多代理结果冲突处理 |
| UI 展示 | 🚧 设计 | 多代理并行状态可视化 |

### TODO 分析

```typescript
// 未发现 Swarm 相关的显式 TODO
// 说明: 架构设计阶段已完成，等待核心实现
```

---

## 竞品对比

| 特性 | Claude Code Swarm | AutoGPT | MetaGPT | CrewAI |
|------|-------------------|---------|---------|--------|
| 架构 | 中心化协调 | 自主循环 | 角色扮演 | 流程编排 |
| 并发 | ✅ 原生支持 | ⚠️ 单线程 | ⚠️ 单线程 | ✅ 支持 |
| 可视化 | 🚧 开发中 | ❌ 弱 | ❌ 弱 | ✅ 较好 |
| 集成度 | ✅ 深度集成终端 | ⚠️ 独立运行 | ⚠️ 独立运行 | ⚠️ 独立运行 |
| 易用性 | 🚧 待验证 | ⚠️ 需配置 | ⚠️ 需配置 | ⚠️ 需配置 |

---

## 结论

**完善程度**: 🟡 **Beta 阶段**（核心并发框架完成，协调层待完善）

**预计发布时间**: 2026 年 Q3

Swarm/Coordinator 代表了 Claude Code 从单助手向多代理生态扩展的关键一步。其深度集成终端、原生支持并发的架构设计，有望成为开发者首选的多 AI 协作方案。
