#!/usr/bin/env python3
"""获取自选股关注列表实时行情"""

import requests
from datetime import datetime

def parse_qq(code):
    url = f"http://qt.gtimg.cn/q={code}"
    try:
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
            'open': float(parts[5]),
            'high': float(parts[33]) if len(parts) > 33 else 0,
            'low': float(parts[34]) if len(parts) > 34 else 0,
            'volume': float(parts[36]) if len(parts) > 36 else 0,
            'change_pct': round((float(parts[3]) - float(parts[4])) / float(parts[4]) * 100, 2)
        }
    except:
        return None

# 关注股列表（从AGENTS.md）
watchlist = {
    "歌尔股份": "sz002241",
    "高德红外": "sz002414",
    "北方铜业": "sz000737",
    "三一重工": "sh600031",
    "禾望电气": "sh603063",
    "茶花股份": "sz002815",
    "大族激光": "sz002008",
    "中国卫星": "sh600118",
    "中航成飞": "sz302132",
    "上汽集团": "sh600104",
    "日月股份": "sh603218",
    "时代新材": "sh600458",
    "厦门钨业": "sh600549",
    "山东海化": "sz000822",
}

print(f"=== 自选股行情 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
print(f"{'名称':<10} {'代码':<10} {'现价':<8} {'涨跌%':<8} {'状态':<6}")
print("-" * 50)

results = {}
for name, code in watchlist.items():
    d = parse_qq(code)
    if d:
        results[name] = d
        status = "📈" if d['change_pct'] > 0 else "📉" if d['change_pct'] < 0 else "➡️"
        print(f"{name:<10} {code:<10} {d['current']:<8.2f} {d['change_pct']:<+7.2f}% {status}")
    else:
        print(f"{name:<10} {code:<10} 获取失败")

# 排序
if results:
    sorted_list = sorted(results.items(), key=lambda x: x[1]['change_pct'], reverse=True)
    print(f"\n🏆 今日最强: {sorted_list[0][0]} ({sorted_list[0][1]['change_pct']:+.2f}%)")
    print(f"😞 今日最弱: {sorted_list[-1][0]} ({sorted_list[-1][1]['change_pct']:+.2f}%)")

print("\n=== 完成 ===")
