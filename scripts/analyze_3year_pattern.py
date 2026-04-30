#!/usr/bin/env python3
"""国泰海通3年K线历史分析 - 结合大盘和庄家手法"""

import requests
import json
from datetime import datetime

# 获取3年K线 (约750个交易日)
url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh601211,day,2023-01-01,2026-04-30,800,qfq"
resp = requests.get(url, timeout=60)
data = resp.json()

kline = data['data']['sh601211']['qfqday']
print(f"获取到 {len(kline)} 天K线数据")

# 手动解析
parsed = []
for row in kline:
    if len(row) >= 6:
        parsed.append({
            '日期': row[0],
            '开盘': float(row[1]),
            '收盘': float(row[2]),
            '最高': float(row[3]),
            '最低': float(row[4]),
            '成交量': float(row[5])
        })

print(f"成功解析 {len(parsed)} 条数据 ({parsed[0]['日期']} ~ {parsed[-1]['日期']})")

# 计算涨跌幅和均线
for i in range(1, len(parsed)):
    prev_close = parsed[i-1]['收盘']
    curr_close = parsed[i]['收盘']
    parsed[i]['涨跌幅'] = round((curr_close - prev_close) / prev_close * 100, 2)

# 计算MA5/10/20
for i in range(len(parsed)):
    if i >= 4:
        parsed[i]['MA5'] = sum(parsed[j]['收盘'] for j in range(i-4, i+1)) / 5
    if i >= 9:
        parsed[i]['MA10'] = sum(parsed[j]['收盘'] for j in range(i-9, i+1)) / 10
    if i >= 19:
        parsed[i]['MA20'] = sum(parsed[j]['收盘'] for j in range(i-19, i+1)) / 20

# 保存
with open('data/watchlist/active/601211/history/601211_kline_3year.json', 'w', encoding='utf-8') as f:
    json.dump(parsed, f, ensure_ascii=False, indent=2)

print("\n=== 3年数据概览 ===")
print(f"最高价: {max(d['最高'] for d in parsed):.2f}")
print(f"最低价: {min(d['最低'] for d in parsed):.2f}")
print(f"当前价: {parsed[-1]['收盘']:.2f}")

# 找出所有暴跌日
crashes = [d for d in parsed[20:] if d.get('涨跌幅', 0) <= -3.0]
print(f"\n3年内单日暴跌≥-3%次数: {len(crashes)}")

# 分析暴跌后走势
print("\n=== 暴跌后走势分析（最近15次）===")
for crash in crashes[-15:]:
    idx = parsed.index(crash)
    date = crash['日期']
    close = crash['收盘']
    change = crash['涨跌幅']
    
    # 后续走势
    future_5 = parsed[idx:idx+6]
    future_10 = parsed[idx:idx+11]
    future_20 = parsed[idx:idx+21]
    
    day5_change = 0
    day10_change = 0
    day20_change = 0
    
    if len(future_5) >= 6:
        day5_change = round((future_5[5]['收盘'] - close) / close * 100, 2)
    if len(future_10) >= 11:
        day10_change = round((future_10[10]['收盘'] - close) / close * 100, 2)
    if len(future_20) >= 21:
        day20_change = round((future_20[20]['收盘'] - close) / close * 100, 2)
    
    # 判断趋势
    if day5_change > 5:
        trend_5 = "📈 强势反弹"
    elif day5_change > 0:
        trend_5 = "🔄 弱反弹"
    elif day5_change > -5:
        trend_5 = "➡️ 横盘"
    else:
        trend_5 = "📉 继续跌"
    
    print(f"\n【{date}】 收{close:.2f} 跌{change:.2f}%")
    print(f"  5日后: {day5_change:+.2f}% {trend_5}")
    print(f"  10日后: {day10_change:+.2f}%")
    print(f"  20日后: {day20_change:+.2f}%")

# 统计规律
print("\n\n=== 3年统计规律 ===")
stats_5 = []
stats_10 = []
stats_20 = []

for crash in crashes:
    idx = parsed.index(crash)
    close = crash['收盘']
    
    future_5 = parsed[idx:idx+6]
    future_10 = parsed[idx:idx+11]
    future_20 = parsed[idx:idx+21]
    
    if len(future_5) >= 6:
        stats_5.append((future_5[5]['收盘'] - close) / close * 100)
    if len(future_10) >= 11:
        stats_10.append((future_10[10]['收盘'] - close) / close * 100)
    if len(future_20) >= 21:
        stats_20.append((future_20[20]['收盘'] - close) / close * 100)

if stats_5:
    print(f"暴跌后5日:")
    print(f"  上涨概率: {len([s for s in stats_5 if s > 0])}/{len(stats_5)} ({len([s for s in stats_5 if s > 0])/len(stats_5)*100:.1f}%)")
    print(f"  平均涨跌: {sum(stats_5)/len(stats_5):+.2f}%")
    print(f"  最大反弹: {max(stats_5):+.2f}%")
    print(f"  最大下跌: {min(stats_5):+.2f}%")

if stats_10:
    print(f"\n暴跌后10日:")
    print(f"  上涨概率: {len([s for s in stats_10 if s > 0])}/{len(stats_10)} ({len([s for s in stats_10 if s > 0])/len(stats_10)*100:.1f}%)")
    print(f"  平均涨跌: {sum(stats_10)/len(stats_10):+.2f}%")

if stats_20:
    print(f"\n暴跌后20日:")
    print(f"  上涨概率: {len([s for s in stats_20 if s > 0])}/{len(stats_20)} ({len([s for s in stats_20 if s > 0])/len(stats_20)*100:.1f}%)")
    print(f"  平均涨跌: {sum(stats_20)/len(stats_20):+.2f}%")

# 当前走势
print("\n\n=== 当前走势（最近20日）===")
recent = parsed[-20:]
for d in recent:
    change_str = f"{d.get('涨跌幅', 0):+.2f}%" if '涨跌幅' in d else "N/A"
    ma5_str = f"MA5:{d['MA5']:.2f}" if 'MA5' in d else ""
    print(f"{d['日期']} | 收{d['收盘']:.2f} | {change_str} | {ma5_str}")

print("\n=== 分析完成 ===")
