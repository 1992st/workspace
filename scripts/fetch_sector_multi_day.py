#!/usr/bin/env python3
"""获取券商行业多日期历史数据 - 5日对比"""

import requests
import json
from datetime import datetime

def parse_qq_quote(code):
    url = f"http://qt.gtimg.cn/q={code}"
    resp = requests.get(url, timeout=10)
    data = resp.text
    if not data or '~' not in data:
        return None
    parts = data.split('~')
    if len(parts) < 45:
        return None
    return {
        'name': parts[1],
        'current': float(parts[3]),
        'prev': float(parts[4]),
        'change_pct': round((float(parts[3]) - float(parts[4])) / float(parts[4]) * 100, 2)
    }

# 获取多日K线数据
symbols = {
    "国泰海通": "sh601211",
    "中信证券": "sh600030",
    "华泰证券": "sh601688",
    "东方财富": "sz300059",
    "中信建投": "sh601066",
    "中金公司": "sh601995",
    "招商证券": "sh600999",
    "券商ETF": "sh512000",
    "证券指数": "sz399975"
}

print(f"=== 券商行业多股对比 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

# 获取腾讯5日历史接口
print("=== 5日K线数据（腾讯接口）===\n")

for name, code in symbols.items():
    try:
        # 获取5日分时/历史数据
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,2026-04-23,2026-04-30,10,qfq"
        resp = requests.get(url, timeout=15)
        data = resp.json()
        
        if 'data' in data and code in data['data']:
            stock_data = data['data'][code]
            if 'qfqday' in stock_data:
                days = stock_data['qfqday']
                print(f"【{name}({code})】 获取到{len(days)}天数据")
                for d in days:
                    date, open_p, close_p, high, low, vol = d
                    change_pct = round((float(close_p) - float(open_p)) / float(open_p) * 100, 2)
                    print(f"  {date} | 开{open_p} 收{close_p} | 涨跌{change_pct:+.2f}% | 量{vol}")
                print()
    except Exception as e:
        print(f"【{name}】获取失败: {e}\n")

# 同时获取实时盘口
print("\n=== 实时盘口快照 ===")
for name, code in symbols.items():
    d = parse_qq_quote(code)
    if d:
        print(f"{name:10s}: {d['current']:8.2f} ({d['change_pct']:+.2f}%) 昨收:{d['prev']:.2f}")

print("\n=== 完成 ===")
