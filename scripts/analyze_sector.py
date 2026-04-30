#!/usr/bin/env python3
"""券商行业数据解析与对比分析"""

import requests
from datetime import datetime

def parse_qq_quote(code):
    """解析腾讯行情数据"""
    url = f"http://qt.gtimg.cn/q={code}"
    resp = requests.get(url, timeout=10)
    data = resp.text
    if not data or '~' not in data:
        return None
    parts = data.split('~')
    # 腾讯格式: v_code="1~name~code~current~prev~open~..."
    if len(parts) < 45:
        return None
    return {
        'name': parts[1],
        'code': parts[2],
        'current': float(parts[3]),
        'prev': float(parts[4]),
        'open': float(parts[5]),
        'high': float(parts[33]) if len(parts) > 33 else 0,
        'low': float(parts[34]) if len(parts) > 34 else 0,
        'volume': float(parts[36]) if len(parts) > 36 else 0,
        'turnover': float(parts[37]) if len(parts) > 37 else 0,
    }

# 获取数据
peers = {
    "国泰海通": "sh601211",
    "中信证券": "sh600030",
    "华泰证券": "sh601688", 
    "东方财富": "sz300059",
    "中信建投": "sh601066",
    "中金公司": "sh601995",
    "招商证券": "sh600999",
}

results = {}
for name, code in peers.items():
    d = parse_qq_quote(code)
    if d:
        d['change_pct'] = round((d['current'] - d['prev']) / d['prev'] * 100, 2)
        results[name] = d

# 板块数据
etf_data = parse_qq_quote("sh512000")  # 券商ETF华宝
if etf_data:
    etf_data['change_pct'] = round((etf_data['current'] - etf_data['prev']) / etf_data['prev'] * 100, 2)

sector_index = parse_qq_quote("sz399975")  # 证券公司指数
if sector_index:
    sector_index['change_pct'] = round((sector_index['current'] - sector_index['prev']) / sector_index['prev'] * 100, 2)

# 市场成交额
sh_index = parse_qq_quote("sh000001")
sz_index = parse_qq_quote("sz399001")

print(f"=== 券商行业对比分析 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

print("=== 1. 券商板块整体 ===")
if etf_data:
    print(f"券商ETF(512000): {etf_data['current']:.3f} ({etf_data['change_pct']:+.2f}%)")
if sector_index:
    print(f"证券公司指数(399975): {sector_index['current']:.2f} ({sector_index['change_pct']:+.2f}%)")

print("\n=== 2. 个股涨跌对比 ===")
print(f"{'券商名称':<10} {'现价':<8} {'昨收':<8} {'涨跌':<8} {'状态':<8}")
print("-" * 50)
for name, d in results.items():
    status = "📈" if d['change_pct'] > 0 else "📉" if d['change_pct'] < 0 else "➡️"
    print(f"{name:<10} {d['current']:<8.2f} {d['prev']:<8.2f} {d['change_pct']:<+7.2f}% {status}")

# 排序
sorted_results = sorted(results.items(), key=lambda x: x[1]['change_pct'], reverse=True)
print(f"\n🏆 今日最强: {sorted_results[0][0]} ({sorted_results[0][1]['change_pct']:+.2f}%)")
print(f"😞 今日最弱: {sorted_results[-1][0]} ({sorted_results[-1][1]['change_pct']:+.2f}%)")

# 国泰海通排名
gt_position = [i for i, (name, _) in enumerate(sorted_results) if name == "国泰海通"][0] + 1
print(f"📊 国泰海通排名: 第{gt_position}/{len(sorted_results)}名")

print("\n=== 3. 市场成交额（券商行业景气度指标）===")
if sh_index and sz_index:
    sh_turnover = sh_index['turnover'] / 10000  # 转为亿元
    sz_turnover = sz_index['turnover'] / 10000
    total = sh_turnover + sz_turnover
    print(f"上证成交额: {sh_turnover:.0f} 亿元")
    print(f"深证成交额: {sz_turnover:.0f} 亿元")
    print(f"两市合计: {total:.0f} 亿元")
    if total > 15000:
        print("🔥 成交活跃，对券商经纪业务有利")
    elif total > 10000:
        print("✅ 成交正常")
    else:
        print("⚠️ 成交偏淡")

# 保存
import json, os
os.makedirs('data/watchlist/active/601211/analysis', exist_ok=True)
with open('data/watchlist/active/601211/analysis/sector_comparison_20260430.json', 'w', encoding='utf-8') as f:
    json.dump({
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'sector_etf': {'price': etf_data['current'], 'change_pct': etf_data['change_pct']} if etf_data else None,
        'sector_index': {'price': sector_index['current'], 'change_pct': sector_index['change_pct']} if sector_index else None,
        'peers': {name: {'price': d['current'], 'change_pct': d['change_pct']} for name, d in results.items()},
        'market_turnover': total if (sh_index and sz_index) else None,
        'gt_rank': gt_position
    }, f, ensure_ascii=False, indent=2)

print("\n=== 数据已保存 ===")
