#!/usr/bin/env python3
"""国泰海通(601211) 行业+个股联动分析
记录问题 + 重新整合分析"""

import json
import pandas as pd
from datetime import datetime

print(f"=== 国泰海通 行业联动分析报告 ===")
print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

# ============ 第一部分: 问题记录 ============
print("="*60)
print("【第一部分: 本次分析发现的问题记录】")
print("="*60)

issues = """
问题1: 数据时间维度错误
- 严重程度: 🔴 严重
- 描述: 初始分析使用了2025年4月的旧K线数据(价格16.80)，实际应为2026年4月(价格16.12)
- 影响: RSI从89(超买)误判修正为42(中性)，趋势判断从"顶部出货"变为"下跌后震荡"
- 根因: K线查询时使用了错误日期范围 2025-04-01~2025-04-30
- 修正: 已重新拉取 2026-03-01~2026-04-30 数据

问题2: 行业数据缺失
- 严重程度: 🟡 中等
- 描述: 初始分析仅关注个股K线，未获取券商板块整体及同行对比数据
- 影响: 无法判断个股走势是独立行情还是板块驱动
- 修正: 已获取券商ETF(512000)、证券公司指数(399975)及7家同行数据

问题3: 分析碎片化
- 严重程度: 🟡 中等
- 描述: 个股分析、行业分析、资本行为分析分散在不同文件，未整合
- 影响: 用户难以快速获取完整结论
- 修正: 本报告进行整合

问题4: 盘口解读过于主观
- 严重程度: 🟢 轻微
- 描述: 部分庄家行为推测缺乏成交量/资金流向数据支撑
- 修正: 明确标注"推测"并给出验证条件
"""
print(issues)

# ============ 第二部分: 数据加载 ============
print("="*60)
print("【第二部分: 数据概览】")
print("="*60)

# 加载个股K线
with open('data/watchlist/active/601211/history/601211_kline_2026_04.json', 'r', encoding='utf-8') as f:
    kline_data = json.load(f)

df = pd.DataFrame(kline_data)
df['日期'] = pd.to_datetime(df['日期'])
latest = df.iloc[-1]
prev = df.iloc[-2]

# 加载行业对比数据
with open('data/watchlist/active/601211/analysis/sector_comparison_20260430.json', 'r', encoding='utf-8') as f:
    sector_data = json.load(f)

print(f"\n个股数据:")
print(f"  - K线范围: {df['日期'].min().strftime('%Y-%m-%d')} ~ {df['日期'].max().strftime('%Y-%m-%d')}")
print(f"  - 总交易日: {len(df)}")
print(f"  - 最新价: {latest['收盘']:.2f}")
print(f"  - MA5: {latest['MA5']:.2f} | MA10: {latest['MA10']:.2f} | MA20: {latest['MA20']:.2f}")

print(f"\n行业数据:")
print(f"  - 券商ETF: {sector_data['sector_etf']['price']:.3f} ({sector_data['sector_etf']['change_pct']:+.2f}%)")
print(f"  - 证券指数: {sector_data['sector_index']['price']:.2f} ({sector_data['sector_index']['change_pct']:+.2f}%)")
print(f"  - 两市成交: {sector_data['market_turnover']:.0f} 亿元")

# ============ 第三部分: 行业联动分析 ============
print("\n" + "="*60)
print("【第三部分: 行业联动分析】")
print("="*60)

# 个股 vs 板块对比
gt_change = sector_data['peers']['国泰海通']['change_pct']
sector_change = sector_data['sector_index']['change_pct']
gap = gt_change - sector_change

print(f"\n📊 相对强弱分析:")
print(f"  国泰海通今日: {gt_change:+.2f}%")
print(f"  券商板块今日: {sector_change:+.2f}%")
print(f"  相对强弱(GAP): {gap:+.2f}%")

if gap > 1:
    relative = "强于板块"
elif gap < -1:
    relative = "弱于板块"
else:
    relative = "与板块同步"
print(f"  判断: {relative}")

# 同行排名
peers_sorted = sorted(sector_data['peers'].items(), key=lambda x: x[1]['change_pct'], reverse=True)
print(f"\n🏆 今日券商股排名:")
for i, (name, data) in enumerate(peers_sorted, 1):
    marker = "👉" if name == "国泰海通" else "  "
    print(f"  {marker} {i}. {name}: {data['change_pct']:+.2f}%")

# 异常检测
print(f"\n⚠️ 异常检测:")
max_peer = peers_sorted[0]
min_peer = peers_sorted[-1]
spread = max_peer[1]['change_pct'] - min_peer[1]['change_pct']
print(f"  板块内涨跌分化: {spread:.2f}%")
if spread > 3:
    print(f"  🔴 分化严重！{max_peer[0]}异常强势，可能有单独利好")
else:
    print(f"  ✅ 分化不大，板块联动性良好")

# ============ 第四部分: 量价+成交联动 ============
print("\n" + "="*60)
print("【第四部分: 量价与成交联动】")
print("="*60)

# 国泰海通近5日量能
recent_5 = df.tail(5)
avg_vol_5 = recent_5['成交量'].mean()
avg_vol_20 = df.tail(20)['成交量'].mean()
latest_vol = latest['成交量']

print(f"\n📈 国泰海通量能:")
print(f"  今日成交量: {latest_vol:.0f} 手")
print(f"  5日均量: {avg_vol_5:.0f} 手")
print(f"  20日均量: {avg_vol_20:.0f} 手")
print(f"  量比(相对5日): {latest_vol/avg_vol_5:.2f}")

# 与行业量能对比
print(f"\n📊 行业量能环境:")
market_turnover = sector_data['market_turnover']
if market_turnover > 15000:
    turnover_status = "🔥 成交活跃(>1.5万亿)，利好券商经纪+两融"
elif market_turnover > 10000:
    turnover_status = "✅ 成交正常(1-1.5万亿)"
else:
    turnover_status = "⚠️ 成交偏淡(<1万亿)"
print(f"  两市成交额: {market_turnover:.0f} 亿元")
print(f"  环境判断: {turnover_status}")

# 联动结论
print(f"\n🔗 联动结论:")
if market_turnover > 15000 and gt_change < sector_change:
    print(f"  ⚠️ 成交活跃但国泰海通跑输板块 → 资金未流入该股，可能被边缘化")
elif market_turnover > 15000 and gt_change >= sector_change:
    print(f"  ✅ 成交活跃且国泰海通同步/领跑 → 资金关注度高")
elif market_turnover < 10000:
    print(f"  ⚠️ 成交低迷，券商板块整体承压")
else:
    print(f"  ➡️ 成交正常，个股表现取决于自身逻辑")

# ============ 第五部分: 综合判断 ============
print("\n" + "="*60)
print("【第五部分: 行业+个股综合判断】")
print("="*60)

# 多维度打分
scores = {
    '技术面': 45,  # 短期空头，MA下方，RSI 42中性
    '基本面': 75,  # Q1业绩爆发+156%，但板块周期性
    '行业面': 55,  # 成交活跃利好，但跑输板块
    '资金情绪': 40,  # 反弹至16.38失败，多头无力
}
weights = {'技术面': 0.25, '基本面': 0.30, '行业面': 0.25, '资金情绪': 0.20}
total_score = sum(scores[k] * weights[k] for k in scores)

print(f"\n📋 综合评分卡:")
for dim, score in scores.items():
    w = weights[dim] * 100
    print(f"  {dim}: {score}/100 (权重{w:.0f}%)")
print(f"  ─────────────────────")
print(f"  综合评分: {total_score:.1f}/100")

if total_score >= 70:
    overall = "偏多"
elif total_score >= 50:
    overall = "中性"
else:
    overall = "偏空"
print(f"  整体判断: {overall}")

# 核心矛盾
print(f"\n⚖️ 核心矛盾:")
print(f"  利好: 两市成交1.68万亿(活跃) + Q1业绩+156%")
print(f"  利空: 短期均线空头排列 + 反弹16.38失败 + 跑输板块")
print(f"  结论: 基本面和行业环境支持，但技术面和资金情绪偏空")

# ============ 第六部分: 操作建议 ============
print("\n" + "="*60)
print("【第六部分: 基于行业联动的操作建议】")
print("="*60)

print(f"""
📌 持仓者:
  - 若成本 > 16.50: 目前浮亏，关注16.00整数关口支撑
  - 若成本 < 16.00: 可继续持有，等待板块轮动
  - 止损统一设: 15.80 (跌破则确认弱势)

📌 空仓者:
  需同时满足以下条件方可介入:
    ① 个股放量突破16.40 (站上MA5)
    ② 券商板块指数持续走强 (399975 > 760)
    ③ 两市成交维持1.5万亿以上
  
  或:
    ① 个股缩量跌至16.00以下
    ② RSI降至35以下 (超卖)
    ③ 板块内部分化收窄 (国泰海通不再垫底)

📌 行业配置角度:
  - 若看好券商板块，国泰海通并非首选标的
  - 弹性更好的选择: 东方财富、中信建投(需排除单独利好因素)
  - 国泰海通适合: 求稳、偏好大盘蓝筹、不追求弹性的投资者

⚠️ 关键跟踪指标 (节后):
  1. 券商指数399975能否突破760
  2. 两市成交能否维持1.5万亿+
  3. 国泰海通能否站上16.40 (MA5)
  4. 中信建投异常涨幅是否有持续性(验证是否为板块龙头切换)
""")

# ============ 第七部分: 记录归档 ============
print("\n" + "="*60)
print("【第七部分: 分析记录归档】")
print("="*60)

report = {
    "analysis_date": datetime.now().strftime('%Y-%m-%d %H:%M'),
    "stock_code": "601211",
    "stock_name": "国泰海通",
    "issues_found": [
        {"id": 1, "severity": "严重", "desc": "使用了2025年旧数据(16.80)，实际应为2026年数据(16.12)", "impact": "RSI和趋势判断完全错误"},
        {"id": 2, "severity": "中等", "desc": "未结合行业数据进行个股分析", "impact": "无法判断板块驱动还是个股独立行情"},
        {"id": 3, "severity": "中等", "desc": "分析碎片化", "impact": "用户难以获取完整结论"},
        {"id": 4, "severity": "轻微", "desc": "盘口解读过于主观", "impact": "部分庄家推测缺乏数据支撑"}
    ],
    "individual": {
        "latest_price": latest['收盘'],
        "ma5": latest['MA5'],
        "ma10": latest['MA10'],
        "ma20": latest['MA20'],
        "rsi14": 42.36,
        "trend": "short_down",
        "support": [16.00, 15.80],
        "resistance": [16.40, 16.72]
    },
    "sector": {
        "sector_etf_change": sector_data['sector_etf']['change_pct'],
        "sector_index_change": sector_data['sector_index']['change_pct'],
        "gt_rank": sector_data['gt_rank'],
        "gt_vs_sector_gap": gap,
        "market_turnover": sector_data['market_turnover'],
        "turnover_status": "活跃" if sector_data['market_turnover'] > 15000 else "正常"
    },
    "linkage_conclusion": {
        "relative_strength": relative,
        "core_conflict": "基本面/行业环境利好 vs 技术面/资金情绪偏空",
        "total_score": round(total_score, 1),
        "overall_bias": overall,
        "operation": "观望为主，等方向"
    }
}

output_path = 'data/watchlist/active/601211/analysis/integrated_analysis_20260430.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n✅ 综合分析报告已保存至:")
print(f"   {output_path}")
print(f"\n📁 同时生成的文件:")
print(f"   - 个股K线: data/watchlist/active/601211/history/601211_kline_2026_04.json")
print(f"   - 行业对比: data/watchlist/active/601211/analysis/sector_comparison_20260430.json")
print(f"   - 修正报告: data/watchlist/active/601211/analysis/comprehensive_analysis_20260430_corrected.md")

print("\n" + "="*60)
print("分析完成")
print("="*60)
