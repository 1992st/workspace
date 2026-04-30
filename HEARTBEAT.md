# HEARTBEAT.md - 定时维护

## Daily 03:00
1. 聚合前一日 `memory/patterns/*.md`
2. 更新 `memory/types/*.md`（新增、升权、降权）
3. 清理过期备份：`backups/` 保留 7 天
4. 清理处理日志：`memory/patterns/` 保留 30 天
5. 清理前二次确认目标文件存在

## 增量触发
- 当日新增记录每满 10 条，执行一次轻量模式分析
