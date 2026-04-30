#!/usr/bin/env python3
"""获取国泰海通(601211)股票数据"""

import akshare as ak
import json
import pandas as pd
from datetime import datetime
import os

# 创建数据目录
os.makedirs('data/watchlist/active/601211/history', exist_ok=True)
os.makedirs('data/watchlist/active/601211/special', exist_ok=True)

results = {}

# 1. 获取实时行情
print('=== 获取实时行情 ===')
try:
    spot_df = ak.stock_zh_a_spot_em()
    target = spot_df[spot_df['代码'] == '601211']
    if not target.empty:
        spot_data = target.to_dict('records')[0]
        results['spot'] = spot_data
        print(json.dumps(spot_data, ensure_ascii=False, indent=2))
        
        # 保存到文件
        today = datetime.now().strftime('%Y%m%d')
        with open(f'data/watchlist/active/601211/history/601211_spot_{today}.json', 'w', encoding='utf-8') as f:
            json.dump(spot_data, f, ensure_ascii=False, indent=2)
    else:
        print('未找到股票数据')
except Exception as e:
    print(f'获取实时行情失败: {e}')

# 2. 获取历史K线数据
print('\n=== 获取历史K线数据 ===')
try:
    hist_df = ak.stock_zh_a_hist(symbol='601211', period='daily', start_date='20250101', adjust='qfq')
    print(f'获取到 {len(hist_df)} 条历史数据')
    
    # 保存历史数据
    today = datetime.now().strftime('%Y%m%d')
    hist_df.to_json(f'data/watchlist/active/601211/history/601211_daily_{today}.json', 
                    orient='records', force_ascii=False, indent=2)
    
    # 打印最近10天数据
    recent = hist_df.tail(10)
    print(recent.to_json(orient='records', force_ascii=False, indent=2))
    results['history'] = hist_df.tail(30).to_dict('records')
except Exception as e:
    print(f'获取历史数据失败: {e}')

# 3. 获取财务指标
print('\n=== 获取财务指标 ===')
try:
    finance_df = ak.stock_financial_abstract(symbol='601211')
    print(f'获取到 {len(finance_df)} 条财务数据')
    
    # 保存财务数据
    today = datetime.now().strftime('%Y%m%d')
    finance_df.head(5).to_json(f'data/watchlist/active/601211/special/601211_finance_{today}.json',
                               orient='records', force_ascii=False, indent=2)
    
    print(finance_df.head(3).to_json(orient='records', force_ascii=False, indent=2))
    results['finance'] = finance_df.head(5).to_dict('records')
except Exception as e:
    print(f'获取财务数据失败: {e}')

# 4. 获取个股新闻
print('\n=== 获取个股新闻 ===')
try:
    news_df = ak.stock_news_em(symbol='601211')
    print(f'获取到 {len(news_df)} 条新闻')
    print(news_df.head(3)[['标题', '发布时间']].to_json(orient='records', force_ascii=False, indent=2))
    results['news'] = news_df.head(5).to_dict('records')
except Exception as e:
    print(f'获取新闻失败: {e}')

# 保存汇总结果
with open('data/watchlist/active/601211/latest_data.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('\n=== 数据获取完成 ===')
