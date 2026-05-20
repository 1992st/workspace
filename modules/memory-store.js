/**
 * MemoryStore - 记忆存储管理器
 *
 * 功能：
 * 1. 分层存储记忆（长期/短期/失败）
 * 2. 智能记忆压缩
 * 3. 记忆去重和合并
 * 4. 记忆查询和检索
 */

import fs from 'fs/promises';
import path from 'path';

/**
 * 记忆类型枚举
 */
const MemoryType = {
  CRITICAL_DECISION: 'critical_decision', // 关键决策（长期）
  OPERATION: 'operation',                 // 操作记录（短期）
  FAILURE: 'failure',                     // 失败记录
  WORKING: 'working',                     // 工作记忆（当前任务）
};

/**
 * 记忆优先级
 */
const MemoryPriority = {
  HIGH: 'high',      // 必须保留
  MEDIUM: 'medium',  // 可压缩
  LOW: 'low',        // 可删除
};

class MemoryStore {
  constructor() {
    this.workspace = process.cwd();
    this.memoryDir = path.join(this.workspace, 'memory');
    this.criticalMemoryPath = path.join(this.memoryDir, 'critical.json');
    this.operationMemoryPath = path.join(this.memoryDir, 'operation.jsonl');
    this.failureMemoryPath = path.join(this.memoryDir, 'failure.jsonl');

    // 内存缓存
    this.cache = {
      critical: null,
      operation: [],
      failure: [],
    };

    // 配置
    this.config = {
      maxOperationMemories: 1000,      // 最多保留 1000 条操作记忆
      maxFailureMemories: 100,         // 最多保留 100 条失败记忆
      operationMemoryTTL: 30 * 24 * 60 * 60 * 1000, // 30 天
      failureMemoryTTL: 7 * 24 * 60 * 60 * 1000,    // 7 天
    };
  }

  /**
   * 初始化记忆存储
   */
  async init() {
    console.log('\n📦 初始化记忆存储...');

    try {
      // 创建 memory 目录
      await fs.mkdir(this.memoryDir, { recursive: true });

      // 加载关键决策记忆
      this.cache.critical = await this.loadCriticalMemory();

      // 加载操作记忆
      this.cache.operation = await this.loadOperationMemory();

      // 加载失败记忆
      this.cache.failure = await this.loadFailureMemory();

      // 清理过期记忆
      await this.cleanupAllMemories();

      console.log(`✅ 记忆存储已初始化`);
      console.log(`  关键决策: ${this.cache.critical.length} 条`);
      console.log(`  操作记录: ${this.cache.operation.length} 条`);
      console.log(`  失败记录: ${this.cache.failure.length} 条`);

      return true;
    } catch (error) {
      console.error(`❌ 记忆存储初始化失败: ${error.message}`);
      return false;
    }
  }

  /**
   * 添加关键决策记忆
   */
  async addCriticalMemory(agentId, decision, priority = MemoryPriority.HIGH) {
    const memory = {
      id: this.generateId(),
      agentId,
      type: MemoryType.CRITICAL_DECISION,
      decision,
      priority,
      timestamp: Date.now(),
      created: new Date().toISOString(),
    };

    this.cache.critical.push(memory);

    // 立即持久化
    await this.saveCriticalMemory();

    console.log(`✅ 添加关键决策记忆 [${agentId}]: ${decision.substring(0, 50)}...`);

    return memory;
  }

  /**
   * 添加操作记忆
   */
  async addOperationMemory(agentId, operation, priority = MemoryPriority.MEDIUM) {
    const memory = {
      id: this.generateId(),
      agentId,
      type: MemoryType.OPERATION,
      operation,
      priority,
      timestamp: Date.now(),
      created: new Date().toISOString(),
    };

    this.cache.operation.push(memory);

    // 持久化（追加）
    await this.appendOperationMemory(memory);

    // 清理过期记忆
    await this.cleanupOperationMemory();

    return memory;
  }

  /**
   * 添加失败记忆
   */
  async addFailureMemory(agentId, failure, priority = MemoryPriority.MEDIUM) {
    const memory = {
      id: this.generateId(),
      agentId,
      type: MemoryType.FAILURE,
      failure,
      priority,
      timestamp: Date.now(),
      created: new Date().toISOString(),
    };

    this.cache.failure.push(memory);

    // 持久化（追加）
    await this.appendFailureMemory(memory);

    // 清理过期记忆
    await this.cleanupFailureMemory();

    return memory;
  }

  /**
   * 查询记忆（按 agentId）
   */
  queryMemories(agentId, types = null) {
    const memories = [];

    // 查询关键决策记忆
    if (!types || types.includes(MemoryType.CRITICAL_DECISION)) {
      const criticalMemories = this.cache.critical.filter(m => m.agentId === agentId);
      memories.push(...criticalMemories);
    }

    // 查询操作记忆
    if (!types || types.includes(MemoryType.OPERATION)) {
      const operationMemories = this.cache.operation.filter(m => m.agentId === agentId);
      memories.push(...operationMemories);
    }

    // 查询失败记忆
    if (!types || types.includes(MemoryType.FAILURE)) {
      const failureMemories = this.cache.failure.filter(m => m.agentId === agentId);
      memories.push(...failureMemories);
    }

    // 按时间排序（最新的在前）
    return memories.sort((a, b) => b.timestamp - a.timestamp);
  }

  /**
   * 生成上下文摘要
   */
  generateContextSummary(agentId, options = {}) {
    const {
      maxCriticalMemories = 10,
      maxOperationMemories = 20,
      maxFailureMemories = 10,
    } = options;

    const summary = {
      agentId,
      criticalDecisions: [],
      recentOperations: [],
      recentFailures: [],
    };

    // 关键决策记忆
    const criticalMemories = this.cache.critical
      .filter(m => m.agentId === agentId)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, maxCriticalMemories);

    summary.criticalDecisions = criticalMemories.map(m => ({
      id: m.id,
      decision: m.decision,
      created: m.created,
    }));

    // 操作记忆
    const operationMemories = this.cache.operation
      .filter(m => m.agentId === agentId)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, maxOperationMemories);

    summary.recentOperations = operationMemories.map(m => ({
      id: m.id,
      operation: m.operation,
      created: m.created,
    }));

    // 失败记忆
    const failureMemories = this.cache.failure
      .filter(m => m.agentId === agentId)
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, maxFailureMemories);

    summary.recentFailures = failureMemories.map(m => ({
      id: m.id,
      failure: m.failure,
      created: m.created,
    }));

    return summary;
  }

  /**
   * 合并记忆（去重）
   */
  async mergeMemories(newMemories) {
    let mergedCount = 0;

    for (const newMemory of newMemories) {
      let isDuplicate = false;

      // 检查是否已存在（根据 agentId + decision/operation/failure）
      if (newMemory.type === MemoryType.CRITICAL_DECISION) {
        isDuplicate = this.cache.critical.some(
          m => m.agentId === newMemory.agentId && m.decision === newMemory.decision
        );
      } else if (newMemory.type === MemoryType.OPERATION) {
        isDuplicate = this.cache.operation.some(
          m => m.agentId === newMemory.agentId && m.operation === newMemory.operation
        );
      } else if (newMemory.type === MemoryType.FAILURE) {
        isDuplicate = this.cache.failure.some(
          m => m.agentId === newMemory.agentId && m.failure === newMemory.failure
        );
      }

      // 如果不重复，添加到缓存
      if (!isDuplicate) {
        if (newMemory.type === MemoryType.CRITICAL_DECISION) {
          this.cache.critical.push(newMemory);
        } else if (newMemory.type === MemoryType.OPERATION) {
          this.cache.operation.push(newMemory);
        } else if (newMemory.type === MemoryType.FAILURE) {
          this.cache.failure.push(newMemory);
        }
        mergedCount++;
      }
    }

    // 持久化
    await this.saveCriticalMemory();
    await this.saveOperationMemory();
    await this.saveFailureMemory();

    console.log(`✅ 合并 ${newMemories.length} 条记忆，新增 ${mergedCount} 条`);

    return mergedCount;
  }

  /**
   * 压缩记忆（使用 LLM）
   */
  async compressMemories(agentId, type = MemoryType.OPERATION) {
    let memories = [];

    if (type === MemoryType.CRITICAL_DECISION) {
      memories = this.cache.critical.filter(m => m.agentId === agentId);
    } else if (type === MemoryType.OPERATION) {
      memories = this.cache.operation.filter(m => m.agentId === agentId);
    } else if (type === MemoryType.FAILURE) {
      memories = this.cache.failure.filter(m => m.agentId === agentId);
    }

    if (memories.length <= 10) {
      console.log(`⚠️ 记忆数量不足 10 条，无需压缩`);
      return [];
    }

    console.log(`🔄 压缩 ${agentId} 的 ${type} 记忆 (${memories.length} 条)...`);

    // TODO: 调用 LLM API 进行压缩
    // 这里需要集成 LLM 服务
    const compressedMemories = [];

    console.log(`✅ 压缩完成，从 ${memories.length} 条压缩到 ${compressedMemories.length} 条`);

    return compressedMemories;
  }

  /**
   * 生成唯一 ID
   */
  generateId() {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  }

  // ========== 私有方法 ==========

  /**
   * 加载关键决策记忆
   */
  async loadCriticalMemory() {
    try {
      const content = await fs.readFile(this.criticalMemoryPath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      return [];
    }
  }

  /**
   * 保存关键决策记忆
   */
  async saveCriticalMemory() {
    await fs.writeFile(this.criticalMemoryPath, JSON.stringify(this.cache.critical, null, 2));
  }

  /**
   * 加载操作记忆
   */
  async loadOperationMemory() {
    try {
      const content = await fs.readFile(this.operationMemoryPath, 'utf-8');
      const lines = content.trim().split('\n');
      return lines.map(line => JSON.parse(line));
    } catch (error) {
      return [];
    }
  }

  /**
   * 保存操作记忆
   */
  async saveOperationMemory() {
    const lines = this.cache.operation.map(m => JSON.stringify(m));
    await fs.writeFile(this.operationMemoryPath, lines.join('\n'));
  }

  /**
   * 追加操作记忆
   */
  async appendOperationMemory(memory) {
    const line = JSON.stringify(memory);
    await fs.appendFile(this.operationMemoryPath, line + '\n');
  }

  /**
   * 加载失败记忆
   */
  async loadFailureMemory() {
    try {
      const content = await fs.readFile(this.failureMemoryPath, 'utf-8');
      const lines = content.trim().split('\n');
      return lines.map(line => JSON.parse(line));
    } catch (error) {
      return [];
    }
  }

  /**
   * 保存失败记忆
   */
  async saveFailureMemory() {
    const lines = this.cache.failure.map(m => JSON.stringify(m));
    await fs.writeFile(this.failureMemoryPath, lines.join('\n'));
  }

  /**
   * 追加失败记忆
   */
  async appendFailureMemory(memory) {
    const line = JSON.stringify(memory);
    await fs.appendFile(this.failureMemoryPath, line + '\n');
  }

  /**
   * 清理操作记忆（过期和超出限制）
   */
  async cleanupOperationMemory() {
    const now = Date.now();

    // 过滤掉过期的记忆
    this.cache.operation = this.cache.operation.filter(m => {
      const age = now - m.timestamp;
      return age < this.config.operationMemoryTTL;
    });

    // 如果超过限制，删除最旧的
    if (this.cache.operation.length > this.config.maxOperationMemories) {
      this.cache.operation = this.cache.operation
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, this.config.maxOperationMemories);
    }

    // 持久化
    await this.saveOperationMemory();
  }

  /**
   * 清理失败记忆（过期和超出限制）
   */
  async cleanupFailureMemory() {
    const now = Date.now();

    // 过滤掉过期的记忆
    this.cache.failure = this.cache.failure.filter(m => {
      const age = now - m.timestamp;
      return age < this.config.failureMemoryTTL;
    });

    // 如果超过限制，删除最旧的
    if (this.cache.failure.length > this.config.maxFailureMemories) {
      this.cache.failure = this.cache.failure
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, this.config.maxFailureMemories);
    }

    // 持久化
    await this.saveFailureMemory();
  }

  /**
   * 清理所有记忆（初始化时调用）
   */
  async cleanupAllMemories() {
    console.log('\n🧹 清理过期记忆...');

    // 清理操作记忆
    const operationBefore = this.cache.operation.length;
    await this.cleanupOperationMemory();
    const operationAfter = this.cache.operation.length;

    // 清理失败记忆
    const failureBefore = this.cache.failure.length;
    await this.cleanupFailureMemory();
    const failureAfter = this.cache.failure.length;

    const operationCleaned = operationBefore - operationAfter;
    const failureCleaned = failureBefore - failureAfter;

    console.log(`✅ 清理完成`);
    if (operationCleaned > 0) {
      console.log(`  操作记录: 清理 ${operationCleaned} 条（${operationBefore} → ${operationAfter}）`);
    }
    if (failureCleaned > 0) {
      console.log(`  失败记录: 清理 ${failureCleaned} 条（${failureBefore} → ${failureAfter}）`);
    }
  }
}

export { MemoryStore, MemoryType, MemoryPriority };
