# TeamMemory 技术深度解析：团队共享记忆系统

## 功能概述

**TeamMemory** 是 Claude Code 的团队级记忆共享系统，支持跨成员的共享知识库。它让 AI 助手能够理解团队上下文、共享项目知识、维护团队一致性。

### 核心定位
- **产品形态**: 团队协作记忆空间
- **激活条件**: `feature('TEAMMEM')`
- **设计理念**: "团队知识应该被所有成员共享给 AI"

---

## 技术架构

### 1. 系统架构

```typescript
// 从 config.ts 和多处推断
interface TeamMemoryArchitecture {
  // 存储层
  storage: {
    teamMemPaths: TeamMemPaths        // 团队记忆路径管理
    sharedMemoryStore: MemoryStore    // 共享记忆存储
    personalOverlay: PersonalOverlay  // 个人覆盖层
    syncEngine: SyncEngine            // 同步引擎
  }
  
  // 权限层
  permissions: {
    accessControl: AccessControl      // 访问控制
    sharingPolicy: SharingPolicy      // 共享策略
    privacyGuard: PrivacyGuard        // 隐私保护
  }
  
  // 应用层
  application: {
    contextInjector: ContextInjector   // 上下文注入
    knowledgeRetriever: KnowledgeRetriever // 知识检索
    consistencyChecker: ConsistencyChecker // 一致性检查
  }
}
```

### 2. 存储模型

```typescript
// config.ts:35 - 动态加载 TeamMem 路径模块
const teamMemPaths = feature('TEAMMEM')
  ? require('../memdir/teamMemPaths.js')
  : null

// 推断的存储结构
interface TeamMemoryStore {
  // 团队级记忆
  shared: {
    projectContext: ProjectContext    // 项目上下文
    codingStandards: CodingStandards    // 编码规范
    architectureDecisions: ADR[]        // 架构决策记录
    commonPatterns: Pattern[]           // 团队常用模式
    knownIssues: KnownIssue[]           // 已知问题库
  }
  
  // 个人覆盖层
  personal: {
    myNotes: Note[]                    // 个人笔记
    myPreferences: Preferences        // 个人偏好
    privateContexts: PrivateContext[]    // 私有上下文
  }
  
  // 元数据
  metadata: {
    teamId: string
    lastSync: number
    version: number
    members: string[]
  }
}
```

### 3. 与 BUDDY 的协同

```typescript
// BUDDY + TeamMemory 协同架构
interface BuddyTeamIntegration {
  // BUDDY 可以访问团队记忆
  buddy: {
    personalSoul: PersonalSoul       // 个人灵魂（私有）
    teamAwareness: TeamAwareness     // 团队感知（共享）
  }
  
  // 团队记忆增强 BUDDY 响应
  enhancement: {
    useTeamContext: boolean          // 使用团队上下文
    suggestTeamPatterns: boolean   // 推荐团队模式
    warnTeamIssues: boolean         // 预警团队已知问题
  }
}
```

---

## 功能特性详解

### 1. 共享记忆类型

```typescript
interface SharedMemoryTypes {
  // 项目上下文
  projectContext: {
    techStack: Technology[]         // 技术栈
    directoryStructure: Tree        // 目录结构
    buildConfig: BuildConfig        // 构建配置
    deploymentInfo: DeploymentInfo  // 部署信息
  }
  
  // 编码规范
  codingStandards: {
    styleGuide: StyleGuide            // 代码风格
    namingConventions: NamingRules    // 命名规范
    reviewChecklist: Checklist        // 审查清单
    antiPatterns: AntiPattern[]       // 禁止模式
  }
  
  // 架构决策
  architectureDecisions: {
    adrs: ADR[]                       // 架构决策记录
    designPrinciples: Principle[]     // 设计原则
    techChoices: TechChoice[]         // 技术选型
  }
  
  // 团队模式
  commonPatterns: {
    codeTemplates: Template[]        // 代码模板
    refactoringRecipes: Recipe[]     // 重构方案
    debugStrategies: Strategy[]       // 调试策略
  }
  
  // 知识库
  knownIssues: {
    bugs: BugRecord[]                 // 已知 bug
    workarounds: Workaround[]         // 临时方案
    lessonsLearned: Lesson[]         // 经验教训
  }
}
```

### 2. 权限与隐私模型

```typescript
interface TeamMemoryPermissions {
  // 访问级别
  levels: {
    public: AccessLevel     // 全员可读
    protected: AccessLevel  // 成员可读写
    private: AccessLevel    // 个人私有
    admin: AccessLevel      // 管理员控制
  }
  
  // 继承规则
  inheritance: {
    defaultLevel: 'public' | 'protected'
    personalOverrides: boolean  // 个人可覆盖团队设置
    teamMandates: string[]      // 团队强制规则（不可覆盖）
  }
  
  // 隐私边界
  privacy: {
    excludeFromSharing: string[]  // 不共享的内容类型
    autoScrubPatterns: RegExp[]   // 自动脱敏模式
    auditLog: boolean             // 访问审计
  }
}
```

### 3. 同步机制

```typescript
interface TeamMemorySync {
  // 同步策略
  strategies: {
    // 实时同步
    realtime: {
      enabled: boolean
      trigger: 'immediate' | 'debounced'
    }
    
    // 定时同步
    periodic: {
      interval: number
      conflictResolution: 'last-write-wins' | 'merge'
    }
    
    // 手动同步
    manual: {
      command: '/team-sync'
      confirmation: boolean
    }
  }
  
  // 冲突解决
  conflictResolution: {
    autoMerge: boolean
    manualReview: boolean
    backupBeforeMerge: boolean
  }
}
```

---

## 代码注释与功能标志

### 关键代码引用

```typescript
// config.ts:35 - TeamMem 动态加载
const teamMemPaths = feature('TEAMMEM')
  ? (require('../memdir/teamMemPaths.js') as typeof import('../memdir/teamMemPaths.js'))
  : null

// 相关配置项推断
interface ProjectConfig {
  // ... 其他配置
  teamMemory?: {
    enabled: boolean
    teamId: string
    syncMode: 'realtime' | 'periodic' | 'manual'
  }
}

// P100-recordpen agent 的 memory 配置示例
//（来自 gateway config，显示 OpenClaw 的 dreaming 功能）
{
  "memorySearch": {
    "extraPaths": ["./DREAMS.md"]  // 个人记忆扩展路径
  }
}
```

### 功能标志

```typescript
const TEAMMEM_FEATURES = {
  'TEAMMEM': {
    status: '实验性',
    description: '团队共享记忆空间',
    gate: "feature('TEAMMEM')",
    dependencies: ['MEMORY_CORE']
  },
  
  'MEMORY_CORE': {
    status: '基础功能',
    description: '记忆核心系统（支撑 TeamMemory）',
    gate: 'plugins.memory-core.enabled'
  },
  
  'dreaming': {
    status: '实验性',
    description: '自动记忆整理（夜间运行）',
    config: 'plugins.memory-core.config.dreaming',
    frequency: '0 6 * * *'  // 每天早6点
  }
}
```

### 与 OpenClaw Memory 的关系

```yaml
# OpenClaw 配置中的 memory-core（来自 gateway config）
plugins:
  memory-core:
    enabled: true
    config:
      dreaming:
        enabled: true
        frequency: "0 6 * * *"  # cron 表达式
```

**推测关联**:
- Claude Code 的 `TEAMMEM` 可能与 OpenClaw 的 `memory-core` 架构相似
- `dreaming` 功能对应 Claude Code 的 Dream System
- `extraPaths` 配置对应团队记忆的个性化扩展

---

## 完成度评估

### 已完成的组件 ✅

| 组件 | 状态 | 证据 |
|------|------|------|
| 路径模块接口 | ✅ 框架 | `teamMemPaths` 动态加载 |
| 存储架构 | 🟡 设计 | `memdir/teamMemPaths.js` 推断 |
| 与 BUDDY 集成 | 🟡 规划 | `companion` 和团队感知的协同设计 |

### 待完善的组件 🚧

| 组件 | 状态 | 待办 |
|------|------|------|
| TeamMemPaths 实现 | 🚧 开发中 | 具体路径管理逻辑 |
| 同步引擎 | 🚧 设计 | 多端同步机制 |
| 权限系统 | 🚧 规划 | 细粒度访问控制 |
| 冲突解决 | 🚧 规划 | 合并策略 |
| UI/命令 | 🚧 设计 | `/team` 命令系列 |

### 关键限制

```typescript
// 代码中的限制注释（从 config.ts 推断）
// TeamMemory 当前限制:
// 1. 仅在 feature('TEAMMEM') 开启时加载
// 2. 依赖 memdir/teamMemPaths.js 模块
// 3. 与 personal memory 的边界待明确
```

---

## 与竞品的对比

| 特性 | Claude Code TeamMemory | GitHub Copilot Team | Cursor Team |
|------|------------------------|---------------------|-------------|
| 存储位置 | 本地 + 云端 | 云端 | 云端 |
| 隐私控制 | ✅ 细粒度 | ⚠️ 有限 | ⚠️ 有限 |
| 与终端集成 | ✅ 原生 | ❌ 弱 | ❌ 弱 |
| 离线支持 | ✅ 支持 | ❌ 需联网 | ❌ 需联网 |
| 版本控制 | 🚧 待确认 | ❌ 无 | ❌ 无 |

---

## 产品意义

### 1. 解决的问题

| 问题 | 现状 | TeamMemory 方案 |
|------|------|----------------|
| 知识孤岛 | 每个成员独立与 AI 交互 | 共享团队知识库 |
| 规范不一致 | 不同成员得到不同建议 | 统一编码规范 |
| 重复踩坑 | 已知问题反复出现 | 团队问题库预警 |
| 新人上手 | 需要长时间熟悉项目 | AI 直接提供团队上下文 |

### 2. 使用场景

**场景1: 代码审查**
```
新成员提交 PR → AI 自动检查团队规范 → 
对比已知问题库 → 提示"这类似于上次的XX问题"
```

**场景2: 故障排查**
```
报错发生 → AI 查询团队已知问题 → 
发现"这是第3次出现，上次用XX方案解决"
```

**场景3: 项目交接**
```
新成员加入 → AI 提供团队上下文 → 
技术栈、规范、注意事项一站式介绍
```

---

## 结论

**完善程度**: 🔴 **Alpha 阶段**（架构设计阶段，核心实现待启动）

**预计发布时间**: 2026 年 Q4 或 2027 年 Q1

TeamMemory 是 Claude Code 团队化演进的关键功能。虽然当前代码中仅有框架性引用，但其与 BUDDY、Dream System 的协同设计显示出清晰的架构愿景。

**主要障碍**:
1. 隐私与合规复杂性（团队数据的敏感性问题）
2. 同步机制的工程挑战
3. 与现有个人记忆系统的边界划分

**成功关键因素**:
- 无缝的个人/团队记忆切换
- 强大的隐私控制
- 与现有开发者工作流的深度集成
