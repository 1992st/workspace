#!/usr/bin/env python3
"""获取国泰海通完整K线数据并分析"""

import json
import requests
import pandas as pd
from datetime import datetime

# 获取K线数据
url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh601211,day,2025-03-01,2025-04-30,200,qfq"
resp = requests.get(url, timeout=30)
data = resp.json()

# 解析数据
kline_data = data['data']['sh601211']['qfqday']
columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量']

# 创建DataFrame
df = pd.DataFrame(kline_data, columns=columns)
df['开盘'] = df['开盘'].astype(float)
df['收盘'] = df['收盘'].astype(float)
df['最高'] = df['最高'].astype(float)
df['最低'] = df['最低'].astype(float)
df['成交量'] = df['成交量'].astype(float)

# 计算技术指标
df['MA5'] = df['收盘'].rolling(window=5).mean()
df['MA10'] = df['收盘'].rolling(window=10).mean()
df['MA20'] = df['收盘'].rolling(window=20).mean()
df['MA60'] = df['收盘'].rolling(window=60).mean()

# 计算涨跌幅
df['涨跌幅'] = df['收盘'].pct_change() * 100

# 保存数据
df.to_json('data/watchlist/active/601211/history/601211_kline_202504.json', 
           orient='records', force_ascii=False, indent=2)

print(f"获取到 {len(df)} 条K线数据")
print("\n=== 最近10天数据 ===")
print(df.tail(10)[['日期', '开盘', '收盘', '最高', '最低', '成交量', 'MA5', 'MA10']].to_string())

# 计算技术指标
print("\n=== 技术指标 ===")
latest = df.iloc[-1]
prev = df.iloc[-2]

print(f"最新收盘价: {latest['收盘']:.2f}")
print(f"MA5: {latest['MA5']:.2f}")
print(f"MA10: {latest['MA10']:.2f}")
print(f"MA20: {latest['MA20']:.2f}")
print(f"MA60: {latest['MA60']:.2f}")

# 判断趋势
if latest['收盘'] > latest['MA5'] > latest['MA10']:
    trend = "短期多头"
elif latest['收盘'] < latest['MA5'] < latest['MA10']:
    trend = "短期空头"
else:
    trend = "震荡"

print(f"趋势判断: {trend}")

# 计算RSI
delta = df['收盘'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))
print(f"RSI(14): {rsi.iloc[-1]:.2f}")

# 保存分析结果
analysis = {
    'date': datetime.now().strftime('%Y-%m-%d'),
    'latest_price': latest['收盘'],
    'ma5': latest['MA5'],
    'ma10': latest['MA10'],
    'ma20': latest['MA20'],
    'ma60': latest['MA60'],
    'rsi14': rsi.iloc[-1],
    'trend': trend,
    'volume_trend': '放量' if latest['成交量'] > df['成交量'].tail(20).mean() else '缩量'
}

with open('data/watchlist/active/601211/technical_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)

print("\n分析完成，数据已保存")
