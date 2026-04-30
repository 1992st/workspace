#!/usr/bin/env python3
"""获取国泰海通500日K线历史，分析类似走势 - 纯JSON版"""

import requests
from datetime import datetime

# 获取500日K线
url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh601211,day,2024-01-01,2026-04-30,500,qfq"
resp = requests.get(url, timeout=30)
data = resp.json()

kline = data['data']['sh601211']['qfqday']
print(f"获取到 {len(kline)} 天K线数据")

# 手动解析，不依赖pandas
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

print(f"成功解析 {len(parsed)} 条数据")

# 计算涨跌幅
for i in range(1, len(parsed)):
    prev_close = parsed[i-1]['收盘']
    curr_close = parsed[i]['收盘']
    parsed[i]['涨跌幅'] = round((curr_close - prev_close) / prev_close * 100, 2)

# 找出类似走势：单日暴跌-2%以上
print("\n=== 历史类似暴跌日（单日跌幅≥-2%）===")
crashes = [d for d in parsed[1:] if d.get('涨跌幅', 0) <= -2.0]

# 只分析最近10次暴跌
for crash in crashes[-10:]:
    date = crash['日期']
    close = crash['收盘']
    change = crash['涨跌幅']
    
    # 找到在parsed中的索引
    idx = parsed.index(crash)
    
    # 后续5日走势
    future = parsed[idx:idx+6]
    if len(future) >= 6:
        day1 = future[1]['涨跌幅']
        day2 = future[2]['涨跌幅']
        day3 = future[3]['涨跌幅']
        day5_price = future[5]['收盘']
        day5_change = round((day5_price - close) / close * 100, 2)
        
        print(f"\n【{date}】 收{close:.2f} 跌{change:.2f}%")
        print(f"  次日: {day1:+.2f}%")
        print(f"  第2日: {day2:+.2f}%")
        print(f"  第3日: {day3:+.2f}%")
        print(f"  5日后: {day5_change:+.2f}%")
        
        if day5_change > 3:
            trend = "📈 快速反弹"
        elif day5_change > 0:
            trend = "🔄 缓慢修复"
        elif day5_change > -3:
            trend = "➡️ 横盘震荡"
        else:
            trend = "📉 继续下跌"
        print(f"  后续: {trend}")

# 当前走势
print("\n\n=== 当前走势特征（最近10日）===")
recent = parsed[-10:]
for d in recent:
    change_str = f"{d.get('涨跌幅', 0):+.2f}%" if '涨跌幅' in d else "N/A"
    print(f"{d['日期']} | 收{d['收盘']:.2f} | {change_str}")

# 统计规律
print("\n\n=== 暴跌后5日统计规律 ===")
stats = []
for crash in crashes:
    idx = parsed.index(crash)
    future = parsed[idx:idx+6]
    if len(future) >= 6:
        day5_price = future[5]['收盘']
        day5_change = (day5_price - crash['收盘']) / crash['收盘'] * 100
        stats.append(day5_change)

if stats:
    avg_5day = sum(stats) / len(stats)
    up_count = len([s for s in stats if s > 0])
    down_count = len([s for s in stats if s <= 0])
    
    print(f"历史暴跌次数: {len(stats)}")
    print(f"5日后上涨概率: {up_count}/{len(stats)} ({up_count/len(stats)*100:.1f}%)")
    print(f"5日后平均涨跌: {avg_5day:+.2f}%")
    print(f"5日后最大反弹: {max(stats):+.2f}%")
    print(f"5日后最大下跌: {min(stats):+.2f}%")

print("\n=== 分析完成 ===")
