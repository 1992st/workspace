# KAIROS 技术深度解析：主动式 AI 助手系统

## 功能概述

**KAIROS**（希腊语"关键时刻"）是 Claude Code 的主动式助手模式，代表 AI 从"被动响应"向"主动介入"的范式转变。

---

## 技术架构

### 核心状态管理

```typescript
// bootstrap/state.ts 中的 KAIROS 状态
interface State {
  kairosActive: boolean           // 主动模式状态
  sessionSource: string | undefined  // 会话来源
  replBridgeActive?: boolean      // Ant-only: REPL 桥接
  directConnectServerUrl?: string  // 直连服务器 URL
  isRemoteMode: boolean           // 远程模式标志
}
```

### Session Transcript 系统

```typescript
// query.ts 中的动态加载
const sessionTranscriptModule = feature('KAIROS')
  ? require('../sessionTranscript/sessionTranscript.js')
  : null
```

---

## 功能特性详解

### 1. 触发机制

**触发类型**:
- 时间型: 用户空闲后
- 事件型: 文件变更、错误发生、命令完成
- 模式型: 重复动作检测、上下文切换

### 2. 介入策略

| 级别 | 触发条件 | 表现形式 |
|------|----------|----------|
| silent | 仅记录 | 无可见提示 |
| subtle | 低优先级 | 状态栏图标变化 |
| notice | 中优先级 | 非侵入式通知 |
| interrupt | 高优先级 | 强制弹窗 |

---

## 代码注释与功能标志

### 关键引用

```typescript
// fastMode.ts - KAIROS 特殊处理
getIsNonInteractiveSession() && preferThirdPartyAuthentication() && !getKairosActive()

// permissionSetup.ts - Auto Mode 协同
const autoModeStateModule = feature('TRANSCRIPT_CLASSIFIER')
  ? require('./autoModeState.js')
  : null
```

### 功能标志

| 标志 | 状态 | 描述 |
|------|------|------|
| KAIROS | 实验性 | 主动式助手模式 |
| TRANSCRIPT_CLASSIFIER | 实验性 | 自动模式分类器 |
| BG_SESSIONS | 实验性 | 后台会话支持 |
| TEAMMEM | 实验性 | 团队共享记忆 |

---

## 完成度评估

### 已完成 ✅

| 组件 | 状态 |
|------|------|
| Session Transcript 模块 | 框架 |
| KAIROS 状态管理 | 完成 |
| REPL Bridge | 框架 |

### 待完善 🚧

| 组件 | 状态 |
|------|------|
| Session Transcript 实现 | 开发中 |
| 触发器引擎 | 设计阶段 |
| 感知层 | 规划阶段 |

---

## 结论

**完善程度**: 🔴 **Alpha 阶段**（架构定义完成，核心实现待开发）

**预计发布时间**: 2026 年 Q3-Q4

KAIROS 是 Claude Code 最具野心的功能，代表 AI 从工具向伙伴的范式转移。
