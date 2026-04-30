#!/usr/bin/env python3
"""获取国泰海通真实K线并重新分析 - 修正版"""

import requests
import pandas as pd
from datetime import datetime

# 获取2026年K线
url = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh601211,day,2026-03-01,2026-04-30,100,qfq'
resp = requests.get(url, timeout=30)
data = resp.json()

kline = data['data']['sh601211']['qfqday']
columns = ['日期', '开盘', '收盘', '最高', '最低', '成交量']
df = pd.DataFrame(kline, columns=columns)
df['开盘'] = df['开盘'].astype(float)
df['收盘'] = df['收盘'].astype(float)
df['最高'] = df['最高'].astype(float)
df['最低'] = df['最低'].astype(float)
df['成交量'] = df['成交量'].astype(float)

# 均线
df['MA5'] = df['收盘'].rolling(5).mean()
df['MA10'] = df['收盘'].rolling(10).mean()
df['MA20'] = df['收盘'].rolling(20).mean()

# 涨跌幅
df['涨跌额'] = df['收盘'].diff()
df['涨跌幅'] = df['收盘'].pct_change() * 100

# 保存
df.to_json('data/watchlist/active/601211/history/601211_kline_2026_04.json',
           orient='records', force_ascii=False, indent=2)

print(f"获取到 {len(df)} 天K线")
print("\n=== 最近15天真实数据 ===")
print(df.tail(15)[['日期','开盘','收盘','最高','最低','涨跌幅','成交量']].to_string())

latest = df.iloc[-1]
prev = df.iloc[-2]

print(f"\n=== 当前真实技术指标 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
print(f"最新收盘价: {latest['收盘']:.2f}")
print(f"昨收: {prev['收盘']:.2f}")
print(f"MA5: {latest['MA5']:.2f}")
print(f"MA10: {latest['MA10']:.2f}")
print(f"MA20: {latest['MA20']:.2f}")

# RSI
delta = df['收盘'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))
print(f"RSI(14): {rsi.iloc[-1]:.2f}")

# 趋势判断
print(f"\n52周区间: 14.51 ~ 17.73")
print(f"当前位置: {latest['收盘']:.2f} (区间{(latest['收盘']-14.51)/(17.73-14.51)*100:.1f}%处)")

# 近期特征
recent_5 = df.tail(5)
print(f"\n近5日涨跌幅: {recent_5['涨跌幅'].tolist()}")
print(f"近5日均量: {recent_5['成交量'].mean():.0f}")

# 关键事件
max_vol_idx = df['成交量'].tail(20).idxmax()
max_vol_row = df.loc[max_vol_idx]
print(f"\n近20日最大成交量: {max_vol_row['日期']} {max_vol_row['成交量']:.0f}手 收{max_vol_row['收盘']:.2f}")
