---
name: daily-review
description: Win_Stock 每日复盘 Skill - 收盘后自动复盘，验证预测、分析偏差、积累股性理解
version: 2.0
---

## Case-based adversarial review (current)

The executable review unit is an immutable prediction case, not a Markdown report. A case identifies one symbol, decision time, data cutoff, horizon, snapshot, prompt version, and rule version. Intraday updates create a new case with `parent_case_id`; they never overwrite the previous prediction.

Use the append-only store and validator:

```text
skills/daily-review/case_store.py
skills/daily-review/scripts/adversarial_audit.py
skills/daily-review/scripts/case_pipeline.py
```

Inputs are separated by lifecycle: `facts` and `features` are frozen before `prediction`; `audit` may downgrade or block a decision but cannot modify it; `outcome` is written only after the prediction horizon expires and cannot be used to rewrite the original facts, score, confidence, or reasoning. Every fact requires a source and source time not later than `data_cutoff`; every feature requires a formula and fact references.

The review pipeline must mechanically reject time leakage, missing case boundaries, non-falsifiable direction language, predictions without invalidation conditions, and any attempt to replace an existing prediction. A failed audit produces `blocked` or `degraded`; it is not repaired by adding a narrative explanation. The old Markdown-only accuracy examples below are historical guidance and must not be used as the source of truth when a case record exists.

# 每日复盘 Skill

## 核心原则

**1. 每日必须复盘**
- 收盘后 30 分钟内完成
- 不复盘 = 不学习 = 不进化
- 所有预测必须验证，不能漏掉

**2. 诚实面对错误**
- 错了就是错了，不找借口
- 分析偏差原因，记录到数据库
- 更新股性理解，下次改进

**3. 每只股票独立积累**
- 每只股票有自己的"性格档案"
- 记录该股的操盘风格、消息敏感度、技术特征
- 长期积累，形成对个股的深度理解

**4. 大盘/板块预测也必须复盘**
- 读取 `data/market/predictions/index.jsonl` 和 `data/sectors/predictions/index.jsonl`
- 验证 Vibe-Trading 大盘/板块预测方向、支撑压力、触发/失效条件
- 复盘结果写入 `data/market/reviews/`、`data/sectors/reviews/`
- 若预测为 blocked，也要记录数据缺口是否已修复

## 复盘流程

```
收盘后 16:30 启动复盘
    │
    ▼
┌─────────────────┐
│ 1. 验证昨日预测  │ ← 查询 prediction_log 表中昨日记录
│ • 对比实际走势  │
│ • 标记正确/错误 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 深度偏差分析  │ ← 为什么错了？
│ • 遗漏因素      │
│ • 市场意外      │
│ • 资本行为异常  │
│ • 认知偏差检查  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 更新个股特征  │ ← 重写 profile.md（特征全量快照）
│ • 波动特征      │
│ • 资金特征      │
│ • 消息敏感度    │
│ • 技术特征      │
│ • 主力/盘口特征 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 生成复盘报告  │ ← 写入 review_log 表 + 文件
│ • 整体准确率    │
│ • 个股复盘      │
│ • 教训总结      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. 确认档案完成  │ ← profile.md 已全量重写
│ • 最新复盘索引  │
│ • 特征快照更新  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. 策略优化建议  │ ← 如果连续错误，提示优化 prompt
│ • Prompt效果评估 │
│ • 分析方法调整  │
└─────────────────┘
```

## 验证规则

### 预测正确性判断

```python
def verify_prediction(prediction, actual):
    """
    验证预测正确性
    返回: (是否正确, 准确程度, 收益计算)
    """
    action = prediction['action']
    actual_change = actual['change_pct']
    
    if action == 'BUY':
        if actual_change > 2:
            return True, '完全正确', actual_change
        elif actual_change > 0:
            return True, '部分正确', actual_change
        else:
            return False, '错误', actual_change
    
    elif action == 'SELL':
        if actual_change < -2:
            return True, '完全正确', actual_change
        elif actual_change < 0:
            return True, '部分正确', actual_change
        else:
            return False, '错误', actual_change
    
    elif action == 'HOLD':
        if abs(actual_change) < 2:
            return True, '完全正确', actual_change
        elif abs(actual_change) < 4:
            return True, '部分正确', actual_change
        else:
            return False, '错误', actual_change
    
    elif action == 'WATCH':
        # WATCH 不判断对错，只记录观察
        return None, '观察中', actual_change
```

### 收益计算

```python
def calculate_returns(prediction, actual):
    """
    计算预测的收益指标
    """
    entry = prediction.get('price_at_prediction', actual['pre_close'])
    
    return {
        'max_profit_pct': (actual['high'] - entry) / entry * 100,
        'max_loss_pct': (actual['low'] - entry) / entry * 100,
        'final_return_pct': (actual['close'] - entry) / entry * 100,
        'hit_target': actual['high'] >= prediction['target_price'] if prediction.get('target_price') else None,
        'hit_stop_loss': actual['low'] <= prediction['stop_loss_price'] if prediction.get('stop_loss_price') else None,
        'risk_reward_ratio': None  # 计算风险收益比
    }
```

## 概率校准规则（2026-08-18 强制新增）

预测时给出的**方向概率**必须事后核对，防止系统性低估风险：

1. **每次复盘核对**：预测时的方向概率（如情景A/B/C）vs 实际发生的结果，记入 `predictions_tracker.md` 校准列
2. **低估惩罚**：连续 2 次低估“破位/下跌”概率 → 该股磨底期破位概率下限自动上调（30%→40%）
3. **历史锚点（勿忘）**：2026-08-17 给国泰海通情景C破位=20%，次日即发生 → 磨底期破位概率下限 30% 已生效
4. **校准表格式**：日期 | 预测概率 | 实际结果 | 偏差 | 修正动作

## 偏差分析框架

### 偏差原因分类

```python
DEVIATION_REASONS = {
    'market': {
        'name': '大盘影响',
        'examples': ['系统性风险', '板块轮动', '政策变化']
    },
    'news': {
        'name': '消息影响',
        'examples': ['突发利好', '突发利空', '公告超预期']
    },
    'technical': {
        'name': '技术误判',
        'examples': ['形态识别错误', '支撑阻力判断错误', '指标信号滞后']
    },
    'capital': {
        'name': '资本行为',
        'examples': ['主力洗盘', '意外出货', '新主力介入']
    },
    'sentiment': {
        'name': '情绪因素',
        'examples': ['市场恐慌', '过度乐观', '羊群效应']
    },
    'cognitive': {
        'name': '认知偏差',
        'examples': ['过度自信', '确认偏误', '锚定效应']
    }
}
```

### 复盘记录格式

```sql
-- review_log 表记录
INSERT INTO review_log (
    prediction_id,
    review_date,
    actual_close,
    actual_change_pct,
    actual_high,
    actual_low,
    is_correct,
    accuracy_score,
    max_profit_pct,
    max_loss_pct,
    deviation_reason,
    market_condition,
    lesson_learned,
    capital_behavior_note
) VALUES (
    123,                    -- 关联的预测ID
    '2026-04-24',
    16.60,
    -1.13,
    16.73,
    16.48,
    FALSE,                  -- 预测BUY，实际下跌，错误
    0.0,
    0.83,                   -- (16.73-16.60)/16.60
    -0.72,                  -- (16.48-16.60)/16.60
    '大盘早盘跳水，券商板块跟跌；个股技术突破但市场系统性风险压制',
    'SIDEWAY',
    '技术突破需配合大盘环境，单独技术信号不可靠；下次需确认大盘趋势后再做个股判断',
    '早盘有资金试图拉升，但被大盘拖累，主力未强力护盘，说明对短期走势也不确定'
);
```

## 个股特征积累（每只股票一份特征快照）

### 载体与原则

- **载体**：`data/watchlist/active/{code}/profile.md`，每只股票一份，作为该股"当前特征"的唯一快照。
- **不用 sqlite**：不维护 `stock_character` 表，特征直接落在 profile.md。
- **全量重写，不增量追加**：每次复盘/深度分析后，重写 profile.md 的特征部分，而不是只加一两行，避免新旧数据混杂、特征分散。
- **落盘不强制字段**：以下特征清单是"应关注并总结"的维度，具体字段/表格形式由 Agent 按该股实际情况组织，不做硬性格式限制。

### 特征总结方法（复盘时必须做）

复盘不是"记录今天涨跌"，而是**重新查证据、重新归纳该股的特征**。步骤：

1. **回看证据**：拉该股近期 K 线、资金流、盘口，用真实数据说话，不凭印象。
2. **归纳手法**：把零散的盘面现象总结成规律（如"主力夹板吸筹""拉高派发""波段高抛低吸"），每条规律都要有至少一个实盘证据支撑。
3. **定位当前阶段**：磨底/拉升/出货/横盘/破位，并给出判断依据。
4. **标注异常**：若出现盘口、资金、量价的异常（如夹板、地量拉升、放量长阴），单独详细描述。
5. **全量重写**：把新的特征快照整段重写进 profile.md，短线状态（当前阶段/关键价位/操作建议）刷新，长期股性规律（主力手法/股性标签）保留并更新。

### 需要关注的特征维度（清单）

复盘和特征总结时，至少覆盖以下维度，有则记、无则标"无"：

| 维度 | 要回答的问题 | 举例 |
|------|-------------|------|
| 股性本质 | 它是什么类型的票？ | 波段振幅票 / 趋势票 / 情绪票 / 白马慢牛 |
| 主力手法 | 主力怎么操作？ | 夹板吸筹 / 拉高派发 / 高抛低吸 / 不主动洗盘 |
| 拉升规律 | 每次怎么启动？ | 突然放量暴力拉升 / 渐进推升 / 靠板块β |
| 出货规律 | 怎么见顶？ | 高位放量长阴 / 巨量滞涨 / 利好不涨 |
| 盘口特征 | 盘口有什么异常？ | 夹板结构 / 单边压单托单 / 尾盘拉升 |
| 量能特征 | 量怎么配合价？ | 地量磨底 / 放量突破 / 缩量上涨含意 |
| 消息敏感度 | 对什么消息反应大？ | 政策敏感 / 重组敏感 / 业绩敏感 |
| 板块联动 | 跟板块还是走独立？ | 强共振 / 弱于板块 / 独立行情 |
| 估值锚 | 技术之外的托底逻辑 | 破净 / 历史底部PE / 高位高估值 |
| 关键价位 | 支撑/压力/启动/止损 | 结构化列出，附依据 |
| 异常标记 | 当前有无异常？ | ⭐夹板吸筹 / ⚠️高位破位 / 无 |

### 特征快照示例（非强制格式，仅供参考）

```markdown
## 当前特征快照（最后复盘 2026-08-13）
- **股性本质**: 波段振幅票，反复高抛低吸，不做趋势推升
- **主力手法**: 夹板吸筹（上方18.19压2390手/下方18.11托1604手）
- **当前阶段**: 低位地量磨底（距顶部回撤11.5%）
- **异常标记**: ⭐ 夹板吸筹
- **关键价位**: 启动位18.20-18.30 / 支撑17.70-17.73 / 铁底16.22
```

## 每日复盘报告模板

文件：
- 日汇总：`reviews/daily/2026-04-24_复盘报告.md`
- 个股拆分：`data/watchlist/active/{code}/reviews/{code}_2026-04-24_复盘.md`

```markdown
# 2026-04-24 每日复盘报告

## 一、整体表现
- 预测总数: 5
- 正确: 3 (60%)
- 部分正确: 1 (20%)
- 错误: 1 (20%)
- 整体准确率: 60%

## 二、个股复盘

### 国泰海通(601211)
- **昨日预测**: BUY（置信度75%）
- **今日实际**: -1.13%
- **结果**: ❌ 错误
- **偏差原因**: 大盘早盘跳水，券商板块跟跌；个股技术突破但市场系统性风险压制
- **教训**: 技术突破需配合大盘环境，单独技术信号不可靠
- **股性更新**: 对大盘敏感度高于预期，需增加大盘过滤条件

### 贵州茅台(600519)
- **昨日预测**: HOLD（置信度80%）
- **今日实际**: +0.5%
- **结果**: ✅ 正确
- **备注**: 防御属性显现，大盘下跌时抗跌

## 三、准确率统计

### 按策略版本
| 版本 | 预测数 | 正确 | 准确率 |
|------|--------|------|--------|
| v1 | 5 | 3 | 60% |

### 按股票
| 股票 | 预测数 | 正确 | 准确率 |
|------|--------|------|--------|
| 601211 | 2 | 1 | 50% |
| 600519 | 3 | 2 | 67% |

## 四、今日教训
1. **技术信号需要大盘确认**：601211 技术突破但大盘跳水，导致失败
2. **券商板块联动性强**：需同时监控板块指数
3. **止损执行要坚决**：601211 跌破止损位后应果断离场

## 五、明日策略调整
1. 增加大盘环境过滤：大盘MA20下方不做个股BUY预测
2. 券商股增加板块指数验证
3. 直接优化 `prompts/current/` 中相关分析 Prompt；如需对比，放入 `prompts/experiments/`

## 六、股性理解更新
- **601211**: 对大盘敏感度高，需增加大盘过滤
- **600519**: 防御属性确认，大盘下跌时优先配置

---
**复盘日期**: 2026-04-24
**策略包版本**: current
**下次复盘**: 2026-04-25
```

## 持续进化机制

### Prompt 优化闭环

```
复盘发现分析偏差
    │
    ▼
连续3次同类错误？
    │
    ├─ 是 ──▶ 分析偏差模式
    │           │
    │           ▼
    │       判断是否是 Prompt 问题
    │           │
    │           ├─ 是 ──▶ 优化 Prompt
    │           │           │
    │           │           ▼
    │           │       直接更新 `prompts/current/`
    │           │           │
    │           │           ▼
    │           │       A/B 测试（current vs experiments）
    │           │           │
    │           │           ▼
    │           │       效果更好的版本保留
    │           │
    │           └─ 否 ──▶ 更新股性理解
    │
    └─ 否 ──▶ 记录到股性理解，继续观察
```

### 准确率追踪表

```sql
-- 每周更新准确率统计
CREATE TABLE IF NOT EXISTS accuracy_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date DATE NOT NULL,
    strategy_version VARCHAR(10),
    total_predictions INTEGER,
    correct_count INTEGER,
    accuracy_rate DECIMAL(5,4),
    avg_confidence DECIMAL(5,2),
    avg_actual_return DECIMAL(10,4)
);
```

## 禁止事项

- ❌ 不复盘直接做新预测
- ❌ 错了不记录原因
- ❌ 不更新股性理解
- ❌ 连续错误不调整策略
- ❌ 把错误归咎于"市场不可预测"

## 检查清单

每日复盘后检查：
- [ ] 所有昨日预测已验证
- [ ] 偏差原因已记录到 review_log
- [ ] 个股特征已全量重写到 profile.md（非增量追加）
- [ ] 异常股票已单独详细描述和分析
- [ ] 复盘报告已生成
- [ ] 准确率统计已更新
- [ ] 连续错误已分析是否需要优化 prompt
