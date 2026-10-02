#!/usr/bin/env python3
"""通用技术指标计算（腾讯 qfq 日K 输入）

用法:
  python3 scripts/tech_indicators.py <腾讯K线JSON路径> <symbol_key>

输出: MA/RSI/MACD/BOLL/量能/位置统计 的 JSON
"""
import json
import sys


def ema(values, n):
    k = 2.0 / (n + 1)
    out = []
    prev = None
    for v in values:
        prev = v if prev is None else v * k + prev * (1 - k)
        out.append(prev)
    return out


def sma(values, n):
    out = []
    for i in range(len(values)):
        if i + 1 < n:
            out.append(None)
        else:
            out.append(sum(values[i + 1 - n:i + 1]) / n)
    return out


def rsi(closes, n=14):
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag = sum(gains[:n]) / n
    al = sum(losses[:n]) / n
    for i in range(n, len(closes)):
        if i > n:
            ag = (ag * (n - 1) + gains[i - 1]) / n
            al = (al * (n - 1) + losses[i - 1]) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def stdev(values, n):
    out = []
    for i in range(len(values)):
        if i + 1 < n:
            out.append(None)
        else:
            w = values[i + 1 - n:i + 1]
            m = sum(w) / n
            out.append((sum((x - m) ** 2 for x in w) / n) ** 0.5)
    return out


def main():
    path, key = sys.argv[1], sys.argv[2]
    raw = json.load(open(path))
    node = raw["data"][key]
    bars = node.get("qfqday") or node.get("day")
    dates = [b[0] for b in bars]
    opens = [float(b[1]) for b in bars]
    closes = [float(b[2]) for b in bars]
    highs = [float(b[3]) for b in bars]
    lows = [float(b[4]) for b in bars]
    vols = [float(b[5]) for b in bars]

    ma5, ma10, ma20, ma30, ma60, ma120 = (sma(closes, n) for n in (5, 10, 20, 30, 60, 120))
    r6, r14 = rsi(closes, 6), rsi(closes, 14)
    dif = [a - b for a, b in zip(ema(closes, 12), ema(closes, 26))]
    dea = ema(dif, 9)
    macd = [2 * (a - b) for a, b in zip(dif, dea)]
    bb_mid = sma(closes, 20)
    bb_sd = stdev(closes, 20)
    bb_up = [None if m is None else m + 2 * s for m, s in zip(bb_mid, bb_sd)]
    bb_dn = [None if m is None else m - 2 * s for m, s in zip(bb_mid, bb_sd)]

    v5 = sma(vols, 5)
    v10 = sma(vols, 10)
    v60 = sma(vols, 60)

    def ret(n):
        return None if len(closes) <= n else round((closes[-1] / closes[-1 - n] - 1) * 100, 2)

    last = -1
    hi252 = max(highs)
    lo252 = min(lows)
    # 20 日涨跌幅 sigma 偏离
    rets20 = [closes[i] / closes[i - 20] - 1 for i in range(20, len(closes))]
    r20 = rets20[-1]
    mu = sum(rets20) / len(rets20)
    sd = (sum((x - mu) ** 2 for x in rets20) / len(rets20)) ** 0.5
    z20 = (r20 - mu) / sd if sd else None

    r3 = closes[-1] / closes[-4] - 1
    rets3 = [closes[i] / closes[i - 3] - 1 for i in range(3, len(closes))]
    mu3 = sum(rets3) / len(rets3)
    sd3 = (sum((x - mu3) ** 2 for x in rets3) / len(rets3)) ** 0.5
    z3 = (r3 - mu3) / sd3 if sd3 else None

    out = {
        "key": key,
        "bars": len(bars),
        "date_range": [dates[0], dates[-1]],
        "close": closes[last],
        "ma5": round(ma5[last], 2), "ma10": round(ma10[last], 2),
        "ma20": round(ma20[last], 2), "ma30": round(ma30[last], 2),
        "ma60": round(ma60[last], 2),
        "ma120": round(ma120[last], 2) if ma120[last] else None,
        "vol_last": int(vols[last]), "vol_ma5": int(v5[last]), "vol_ma10": int(v10[last]),
        "vol_ma60": int(v60[last]),
        "vol_ratio_ma5": round(vols[last] / v5[last], 2),
        "vol_ratio_ma60": round(vols[last] / v60[last], 2),
        "rsi6": round(r6[last], 1), "rsi14": round(r14[last], 1),
        "macd_dif": round(dif[last], 3), "macd_dea": round(dea[last], 3), "macd_hist": round(macd[last], 3),
        "boll_up": round(bb_up[last], 2), "boll_mid": round(bb_mid[last], 2), "boll_dn": round(bb_dn[last], 2),
        "boll_width_pct": round((bb_up[last] - bb_dn[last]) / bb_mid[last] * 100, 2),
        "range_180d": [lo252, hi252],
        "pct_from_180d_high": round((closes[last] / hi252 - 1) * 100, 2),
        "pct_from_180d_low": round((closes[last] / lo252 - 1) * 100, 2),
        "ret_5d": ret(5), "ret_10d": ret(10), "ret_20d": ret(20), "ret_60d": ret(60),
        "z20_sigma": round(z20, 2) if z20 is not None else None,
        "z3_sigma": round(z3, 2) if z3 is not None else None,
        "recent_25": [
            {"d": dates[i], "o": opens[i], "c": closes[i], "h": highs[i], "l": lows[i],
             "v": int(vols[i]), "ma5": round(ma5[i], 2) if ma5[i] else None,
             "ma20": round(ma20[i], 2) if ma20[i] else None,
             "ma60": round(ma60[i], 2) if ma60[i] else None,
             "rsi14": round(r14[i], 1) if r14[i] else None}
            for i in range(len(bars) - 25, len(bars))
        ],
        "weekly_trend_ma60_slope_10d_pct": round((ma60[last] / ma60[last - 10] - 1) * 100, 2),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
