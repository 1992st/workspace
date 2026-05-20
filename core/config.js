/**
 * Stone - 配置管理
 */

export const CONFIG = {
  workspace: '/Volumes/zhangstExtern/openclaw/workspace/stone/',

  // 监控配置
  monitoring: {
    interval: 30, // 分钟
    intervalUnit: 'minutes',
  },

  // 飞书群配置
  feishu: {
    groupId: 'oc_5347fa823df2385fe75516285e7c215b',
  },

  // Agent 配置
  agents: {
    ffmedia: {
      workspace: '/Users/zhangst/.openclaw/workspace/ffmedia/',
      monitoringFrequency: 'hourly',
      requirementsFile: 'requirements/ffmedia.md',
    },
    agentmesh: {
      workspace: '/Users/zhangst/.openclaw/workspace/agentmesh/',
      monitoringFrequency: 'daily',
      requirementsFile: 'requirements/agentmesh.md',
    },
    'Ai-StockAssistant': {
      workspace: '/Users/zhangst/.openclaw/workspace/Ai-StockAssistant/',
      monitoringFrequency: 'hourly',
      requirementsFile: 'requirements/ai-stock.md',
    },
  },

  // Subagent 配置
  subagents: {
    maxRetries: 3, // 最多重试 3 次
    waitTimeoutSeconds: 300, // agent.wait 超时时间（5 分钟）
    queryIntervalSeconds: 300, // 状态查询间隔（5 分钟）
    maxConcurrent: 5, // 最大并发 subagent 数
  },

  // 存储路径
  storage: {
    agentStates: 'AGENT-STATES.md',
    agentSessions: 'AGENT-SESSIONS.md',
    monitorLog: 'MONITOR-LOG.md',
    gatewayApiDoc: 'GATEWAY-HTTP-API.md',
    alerts: 'alerts/',
    retrospectives: 'retrospectives/',
  },

  // Stone Session Key
  stoneSessionKey: 'agent:stone:main',
};

export default CONFIG;
