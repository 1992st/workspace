#!/usr/bin/env python3
"""
国泰海通(601211) 缩量形态历史回测
分析"缩量极致→变盘"假设是否成立：
- 历史上缩量到极致(地量)出现多少次
- 每次持续多久
- 缩量之后的走势方向分布
数据：日K volume（500天，2024-06~2026-08）
"""
import json, subprocess, sys

def get_kline():
    r = subprocess.run(
        [sys.executable, "skills/stock-data/scripts/stock_client.py", "klinex", "601211", "daily", "500"],
        capture_output=True, text=True, timeout=120
    )
    d = json.loads(r.stdout)
    return d["data"]["bars"]

def run():
    bars = get_kline()
    # bars: date, open, close, high, low, volume
    # 计算20日滚动均量，定义"缩量日" = volume < 20日均量的 0.6 倍
    vols = [b["volume"] for b in bars]
    dates = [b["date"] for b in bars]
    closes = [b["close"] for b in bars]

    n = len(bars)
    ma20 = []
    for i in range(n):
        window = vols[max(0, i-19):i+1]
        ma20.append(sum(window)/len(window))

    # 定义缩量日：volume / ma20 < 0.6
    # 定义"缩量极致"：volume / ma20 < 0.45，且为阶段性低量
    shrink_ratios = []
    for i in range(n):
        if ma20[i] > 0:
            shrink_ratios.append(vols[i]/ma20[i])
        else:
            shrink_ratios.append(1.0)

    # 找"缩量段"：连续缩量天数 >= 3，且期间 ratio 均值 < 0.6
    episodes = []
    i = 0
    while i < n:
        if shrink_ratios[i] < 0.6:
            j = i
            while j < n and shrink_ratios[j] < 0.6:
                j += 1
            length = j - i
            if length >= 3:
                # 该段最低ratio
                min_ratio = min(shrink_ratios[i:j])
                episodes.append({
                    "start_idx": i,
                    "end_idx": j-1,
                    "start_date": dates[i],
                    "end_date": dates[j-1],
                    "length": length,
                    "min_ratio": min_ratio,
                    "close_before": closes[i-1] if i > 0 else closes[i],
                    "close_end": closes[j-1],
                })
            i = j
        else:
            i += 1

    print("="*70)
    print("国泰海通 缩量形态历史统计（500日，volume vs 20日均量）")
    print("="*70)
    print(f"缩量定义：当日量 / 20日均量 < 0.60")
    print(f"极致缩量：当日量 / 20日均量 < 0.45")
    print(f"缩量段判定：连续缩量 >= 3 天（且日均 ratio<0.6）")
    print()
    print(f"共识别缩量段 {len(episodes)} 次：")
    print("-"*70)
    for e in episodes:
        # 段后走势：段结束日起算未来5/10/20日涨跌幅
        end = e["end_idx"]
        def fwd_pct(k):
            if end + k < n:
                return round((closes[end+k]/closes[end]-1)*100, 2)
            return None
        pct5, pct10, pct20 = fwd_pct(5), fwd_pct(10), fwd_pct(20)
        print(f"  {e['start_date']} ~ {e['end_date']} | 持续{e['length']}日 | 最低量比{e['min_ratio']:.2f}")
        print(f"      段末收盘{e['close_end']} | 后5日{pct5}% | 后10日{pct10}% | 后20日{pct20}%")
    print("-"*70)

    # 当前状态
    print()
    print("当前状态（最近5日 量比）：")
    for k in range(-5, 0):
        idx = n + k
        print(f"  {dates[idx]} 收{closes[idx]} 量{vols[idx]:,} 量比{shrink_ratios[idx]:.2f}")

    # 最近一次缩量段的后续
    if episodes:
        last = episodes[-1]
        print()
        print(f"最近一次缩量段：{last['start_date']}~{last['end_date']}，持续{last['length']}日")

if __name__ == "__main__":
    run()
