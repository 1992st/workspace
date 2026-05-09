---
name: daily-review
description: Win_Stock 每日复盘 Skill - 收盘后自动复盘，验证预测、分析偏差、积累股性理解
version: 2.0
---

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
│ 3. 更新股性理解  │ ← 写入 stock_character 表
│ • 波动特征      │
│ • 资金特征      │
│ • 消息敏感度    │
│ • 技术特征      │
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
│ 5. 更新股票档案  │ ← 更新 profile.md
│ • 最新复盘索引  │
│ • 股性观察更新  │
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

## 股性理解积累

### 股性特征记录

```sql
-- stock_character 表记录
INSERT INTO stock_character (
    observation_date,
    character_type,
    description,
    evidence,
    confidence
) VALUES 
-- 波动特征
('2026-04-24', 'volatile', '波动率中等，日内振幅1.5%', '近20日平均振幅1.8%', 4),

-- 资金特征  
('2026-04-24', 'institutional_favorite', '机构持仓集中，主力控盘明显', '前十大股东持股65%', 4),

-- 消息敏感度
('2026-04-24', 'news_sensitive', '对重组消息极度敏感', '重组公告后3日涨幅15%', 5),

-- 技术特征
('2026-04-24', 'momentum', '突破MA20后惯性上涨2-3天', '近5次突破MA20，4次后续2日上涨', 3);
```

### 股性档案更新

每次复盘后更新 `profile.md`：

```markdown
## 股性特征（持续积累）

### 已观察到的特征
- [x] **消息敏感型**: 对重组/政策消息反应剧烈，公告后3日平均涨幅12%
- [x] **机构控盘型**: 前十大股东持股65%，盘中波动相对平稳
- [x] **技术跟随型**: 突破MA20后惯性上涨2-3天，成功率80%

### 操盘风格观察
- 主力资金风格: 机构控盘，游资偶尔参与
- 典型走势特征: 早盘决定全天方向，尾盘很少异动
- 对消息敏感度: **极高**（重组/政策）
- 板块联动性: 强（跟随券商板块）

### 历史验证记录
| 日期 | 预测 | 实际 | 结果 | 偏差原因 |
|------|------|------|------|---------|
| 2026-04-23 | BUY | +2.1% | ✅ | 重组预期 |
| 2026-04-24 | BUY | -1.13% | ❌ | 大盘跳水 |
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
- [ ] 股性理解已更新到 stock_character
- [ ] 股票档案 profile.md 已更新
- [ ] 复盘报告已生成
- [ ] 准确率统计已更新
- [ ] 连续错误已分析是否需要优化 prompt
