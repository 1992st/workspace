#!/usr/bin/env python3
"""获取国泰海通实时行情 - 尝试多种数据源"""

import akshare as ak
import json
from datetime import datetime

print('=== 尝试获取实时行情 ===')

# 方法1: 使用 stock_zh_a_spot_em 但增加重试
try:
    spot_df = ak.stock_zh_a_spot_em()
    target = spot_df[spot_df['代码'] == '601211']
    if not target.empty:
        data = target.to_dict('records')[0]
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        # 保存
        with open('data/watchlist/active/601211/history/601211_spot_latest.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        print('未找到数据')
except Exception as e:
    print(f'spot_em 失败: {e}')

# 方法2: 使用个股信息接口
print('\n=== 尝试 stock_individual_info_em ===')
try:
    info = ak.stock_individual_info_em(symbol='601211')
    print(info.to_json(orient='records', force_ascii=False, indent=2))
except Exception as e:
    print(f'失败: {e}')

# 方法3: 获取最近5天历史数据
print('\n=== 获取最近5天历史数据 ===')
try:
    hist = ak.stock_zh_a_hist(symbol='601211', period='daily', start_date='20250425', end_date='20250430', adjust='qfq')
    if not hist.empty:
        print(hist.to_json(orient='records', force_ascii=False, indent=2))
        
        # 计算技术指标
        hist['MA5'] = hist['收盘'].rolling(window=5).mean()
        hist['MA10'] = hist['收盘'].rolling(window=10).mean()
        hist['MA20'] = hist['收盘'].rolling(window=20).mean()
        
        # 保存
        hist.to_json('data/watchlist/active/601211/history/601211_recent.json', 
                    orient='records', force_ascii=False, indent=2)
    else:
        print('无历史数据')
except Exception as e:
    print(f'历史数据失败: {e}')

# 方法4: 尝试使用东财个股行情
print('\n=== 尝试 stock_zh_a_spot ===')
try:
    spot_all = ak.stock_zh_a_spot()
    target2 = spot_all[spot_all['代码'] == '601211']
    if not target2.empty:
        print(target2.to_json(orient='records', force_ascii=False, indent=2))
except Exception as e:
    print(f'失败: {e}')

print('\n=== 完成 ===')
