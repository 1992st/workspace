#!/usr/bin/env python3
"""获取券商行业数据 - 国泰海通行业对比分析"""

import requests
import json
from datetime import datetime

print(f"=== 券商行业数据获取 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

# 1. 获取券商ETF/板块行情
print("=== 1. 券商板块ETF (512000) ===")
try:
    url = "http://qt.gtimg.cn/q=sh512000"
    resp = requests.get(url, timeout=10)
    data = resp.text
    if data:
        print(data[:500])
except Exception as e:
    print(f"失败: {e}")

# 2. 获取主要券商股行情做对比
print("\n=== 2. 主要券商股行情对比 ===")
peers = {
    "国泰海通": "sh601211",
    "中信证券": "sh600030", 
    "华泰证券": "sh601688",
    "东方财富": "sz300059",
    "中信建投": "sh601066",
    "中金公司": "sh601995",
    "招商证券": "sh600999"
}

for name, code in peers.items():
    try:
        url = f"http://qt.gtimg.cn/q={code}"
        resp = requests.get(url, timeout=10)
        data = resp.text
        # 解析腾讯行情格式
        if data and '"' in data:
            parts = data.split('~')
            if len(parts) > 3:
                price = parts[3] if len(parts) > 3 else "N/A"
                change = parts[4] if len(parts) > 4 else "N/A"
                prev = parts[5] if len(parts) > 5 else "N/A"
                print(f"{name}({code}): 现价={price}, 涨跌={change}, 昨收={prev}")
    except Exception as e:
        print(f"{name} 获取失败: {e}")

# 3. 获取市场成交额（券商受益指标）
print("\n=== 3. A股市场成交额 ===")
try:
    url = "http://qt.gtimg.cn/q=sh000001"  # 上证指数
    resp = requests.get(url, timeout=10)
    data = resp.text
    if data:
        parts = data.split('~')
        if len(parts) > 37:
            turnover = parts[37] if len(parts) > 37 else "N/A"
            print(f"上证指数成交额: {turnover}")
            
    # 深证成指
    url2 = "http://qt.gtimg.cn/q=sz399001"
    resp2 = requests.get(url2, timeout=10)
    data2 = resp2.text
    if data2:
        parts2 = data2.split('~')
        if len(parts2) > 37:
            turnover2 = parts2[37] if len(parts2) > 37 else "N/A"
            print(f"深证成指成交额: {turnover2}")
except Exception as e:
    print(f"失败: {e}")

# 4. 获取证券公司指数
print("\n=== 4. 证券公司指数 (399975) ===")
try:
    url = "http://qt.gtimg.cn/q=sz399975"
    resp = requests.get(url, timeout=10)
    data = resp.text
    if data:
        print(data[:300])
except Exception as e:
    print(f"失败: {e}")

print("\n=== 行业数据获取完成 ===")
