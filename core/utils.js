/**
 * Stone - 工具函数
 */

/**
 * 格式化日期
 */
export function formatDate(date = new Date()) {
  return date.toISOString().replace('T', ' ').substring(0, 19);
}

/**
 * 格式化时长
 */
export function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    const mins = minutes % 60;
    return `${hours}小时${mins}分钟`;
  } else if (minutes > 0) {
    const secs = seconds % 60;
    return `${minutes}分钟${secs}秒`;
  } else {
    return `${seconds}秒`;
  }
}

/**
 * 提取 agentId 从 sessionKey
 */
export function extractAgentId(sessionKey) {
  if (!sessionKey) return 'unknown';

  const match = sessionKey.match(/agent:([^:]+):/);
  if (match) {
    return match[1];
  }

  return 'unknown';
}

/**
 * 提取 runId 从 sessionKey
 */
export function extractRunId(sessionKey) {
  if (!sessionKey) return null;

  const match = sessionKey.match(/:([^:]+)$/);
  if (match) {
    return match[1];
  }

  return null;
}

/**
 * 延迟函数
 */
export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 重试函数
 */
export async function retry(fn, maxRetries = 3, delayMs = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) {
        throw error;
      }
      console.warn(`重试 ${i + 1}/${maxRetries}: ${error.message}`);
      await delay(delayMs * (i + 1)); // 指数退避
    }
  }
}

/**
 * 解析时间字符串为时间戳
 */
export function parseTime(timeStr) {
  if (!timeStr) return null;

  // 格式: "2026-03-02 13:42"
  const match = timeStr.match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/);
  if (!match) return null;

  const [, year, month, day, hour, minute] = match;
  return new Date(year, month - 1, day, hour, minute).getTime();
}

/**
 * 计算时间差（分钟）
 */
export function minutesAgo(timeStr) {
  const time = parseTime(timeStr);
  if (!time) return Infinity;

  return Math.floor((Date.now() - time) / 60000);
}

/**
 * 深度合并对象
 */
export function deepMerge(target, source) {
  const result = { ...target };

  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = deepMerge(target[key] || {}, source[key]);
    } else {
      result[key] = source[key];
    }
  }

  return result;
}

export default {
  formatDate,
  formatDuration,
  extractAgentId,
  extractRunId,
  delay,
  retry,
  parseTime,
  minutesAgo,
  deepMerge,
};
