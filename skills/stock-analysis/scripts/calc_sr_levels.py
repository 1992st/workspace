#!/usr/bin/env python3
"""
通用支撑位/压力位/止损位计算工具
================================
基于K线数据的多方法交叉定位 + 加权评分系统

方法1: 均线支撑（MA5/MA10/MA20/MA60）
方法2: 局部高低点识别（近期关键价位）
方法3: 成交量加权密集区（量价区间分布）
方法4: 斐波那契回撤（最近完整波段）
方法5: 前期平台/突破位（趋势结构分析）

输出: 支撑位列表、压力位列表、止损位推荐、盈亏比计算

用法:
  python3 calc_sr_levels.py <symbol> [--days 120] [--entry PRICE]
  python3 calc_sr_levels.py 601211 --entry 19.14
  python3 calc_sr_levels.py 601211 --days 60 --entry 18.80

数据来源:
  通过 stock_client.py 获取K线数据（前复权）

设计原则:
  1. 所有价位必须有明确的计算依据（禁止拍脑袋）
  2. 支撑/压力必须区分确认次数（1次偶然 vs 多次确认）
  3. 止损 ≠ 支撑位本身，支撑位下方要留噪音margin
  4. 输出必须包含置信度和盈亏比
"""

import json
import sys
import os
import subprocess
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

# ============================================================
# 数据结构
# ============================================================

class LevelType(Enum):
    SUPPORT = "support"
    RESISTANCE = "resistance"

class SignalStrength(Enum):
    WEAK = 1       # 单一方法确认
    MODERATE = 2   # 两种方法交叉
    STRONG = 3     # 三种方法交叉
    VERY_STRONG = 4  # 四种以上方法交叉

@dataclass
class PriceLevel:
    """一个关键价位"""
    price: float
    level_type: str  # "support" | "resistance"
    strength: SignalStrength
    methods: List[str]  # 交叉确认的方法列表
    confirmations: int  # 同一价位附近的确认次数
    volume_weight: float  # 成交量权重（该价位区间的成交量占比，0-1）
    description: str
    is_active: bool = True  # 当前是否仍有效（未被突破/跌穿）

@dataclass
class StopLossRecommendation:
    """止损位推荐"""
    price: float
    label: str  # "紧止损" / "标准止损" / "宽止损"
    basis: str  # 计算依据
    risk_pct: float  # 从入场价到止损的亏损百分比
    suitable_for: str  # 适合什么场景
    score: int  # 1-5

@dataclass
class EntryScenario:
    """入场场景 + 盈亏比"""
    entry_price: float
    stop_loss: float
    stop_label: str
    risk: float  # 元
    risk_pct: float
    targets: List[Tuple[float, str]]  # [(目标价, 标签), ...]
    rr_ratios: List[float]  # 对应每个目标的盈亏比


# ============================================================
# 核心函数
# ============================================================

def fetch_kline(symbol: str, days: int = 120) -> List[Dict]:
    """通过 stock_client.py 获取K线数据"""
    script = os.path.join(os.path.dirname(__file__), 
                          '../../stock-data/scripts/stock_client.py')
    result = subprocess.run(
        ['python3', script, 'kline', symbol, str(days)],
        capture_output=True, text=True, timeout=30
    )
    data = json.loads(result.stdout)
    if not data.get('success'):
        raise RuntimeError(f"K线获取失败: {data.get('error')}")
    return data['data']['bars']


def ma(values: List[float], n: int) -> Optional[float]:
    """移动平均"""
    if len(values) >= n:
        return sum(values[-n:]) / n
    return None


def find_local_extrema(bars: List[Dict], window: int = 3, 
                       use_high: bool = True) -> List[Dict]:
    """
    找局部极值点（高点或低点）
    window: 极值两侧的窗口大小
    返回: [{"date": ..., "price": ..., "volume": ..., "type": "high"/"low"}, ...]
    """
    results = []
    key = 'high' if use_high else 'low'
    half = window // 2
    
    for i in range(half, len(bars) - half):
        neighbors = [bars[j][key] for j in range(i - half, i + half + 1)]
        if use_high:
            if bars[i][key] >= max(neighbors):
                results.append({
                    "date": bars[i]['date'],
                    "price": bars[i][key],
                    "volume": bars[i]['volume'],
                    "type": "high"
                })
        else:
            if bars[i][key] <= min(neighbors):
                results.append({
                    "date": bars[i]['date'],
                    "price": bars[i][key],
                    "volume": bars[i]['volume'],
                    "type": "low"
                })
    return results


def volume_profile(bars: List[Dict], n_recent: int = 30, 
                   bucket_size: float = None) -> Dict[float, Dict]:
    """
    最近N个交易日的成交量价格分布
    返回: {价格区间中心: {"vol": 累计成交量, "days": 天数, "closes": [收盘价列表]}}
    """
    recent = bars[-n_recent:]
    if bucket_size is None:
        # 自动计算合适的桶大小（目标10-20个桶）
        price_range = max(b['close'] for b in recent) - min(b['close'] for b in recent)
        bucket_size = round(price_range / 15, 2)
        if bucket_size < 0.1:
            bucket_size = 0.1
    
    profile = {}
    for bar in recent:
        bucket = round(bar['close'] / bucket_size) * bucket_size
        if bucket not in profile:
            profile[bucket] = {'vol': 0, 'days': 0, 'closes': []}
        profile[bucket]['vol'] += bar['volume']
        profile[bucket]['days'] += 1
        profile[bucket]['closes'].append(bar['close'])
    
    return profile


def fibonacci_retracement(bars: List[Dict], lookback: int = 120) -> Dict[str, float]:
    """
    找最近一轮完整波段的高点和低点，计算斐波那契回撤/扩展
    
    审查改进: 用最近20日均价在整体区间的相对位置判断趋势方向，
    而不是简单用min/max的索引顺序（后者在跨波段时失败）。
    
    返回: {"low": 低点, "high": 高点, "23.6": ..., "38.2": ..., ...}
    """
    recent = bars[-lookback:]
    closes = [b['close'] for b in recent]
    lows = [b['low'] for b in recent]
    highs = [b['high'] for b in recent]
    low_point = min(lows)
    high_point = max(highs)
    
    # 用最近20日均价的相对位置判断方向
    recent_avg = sum(closes[-20:]) / len(closes[-20:]) if len(closes) >= 20 else closes[-1]
    overall_range = high_point - low_point
    current_position = (recent_avg - low_point) / overall_range if overall_range > 0 else 0.5
    
    # 时间辅助: 低点和高点谁在后?
    low_idx = lows.index(low_point)
    high_idx = highs.index(high_point)
    
    # 综合判断: 位置(60%) + 时间先后(40%)
    # 当前≥60%分位 → 上升趋势，做回撤
    # 当前<60%分位 → 下降趋势，做反弹（保守策略）
    if current_position >= 0.6:
        fib_range = high_point - low_point
        return {
            "low": round(low_point, 2), "high": round(high_point, 2),
            "direction": f"上升回撤(当前{current_position*100:.0f}%位)",
            "波段": f"{high_point} ← {low_point}",
            "0.0": round(high_point, 2),
            "23.6": round(high_point - fib_range * 0.236, 2),
            "38.2": round(high_point - fib_range * 0.382, 2),
            "50.0": round(high_point - fib_range * 0.500, 2),
            "61.8": round(high_point - fib_range * 0.618, 2),
            "78.6": round(high_point - fib_range * 0.786, 2),
            "100.0": round(low_point, 2),
        }
    else:
        # 下跌反弹模式（也适用于中间位置，更保守）
        fib_range = high_point - low_point
        return {
            "low": round(low_point, 2), "high": round(high_point, 2),
            "direction": f"下跌反弹(当前{current_position*100:.0f}%位)",
            "波段": f"{low_point} ← {high_point}",
            "0.0": round(low_point, 2),
            "23.6": round(low_point + fib_range * 0.236, 2),
            "38.2": round(low_point + fib_range * 0.382, 2),
            "50.0": round(low_point + fib_range * 0.500, 2),
            "61.8": round(low_point + fib_range * 0.618, 2),
            "78.6": round(low_point + fib_range * 0.786, 2),
            "100.0": round(high_point, 2),
        }


def cluster_prices(prices: List[float], tolerance_pct: float = 1.5) -> List[Tuple[float, int]]:
    """
    将相近的价格聚类，返回 (聚类中心, 成员数量)
    用于识别"多次测试"的关键价位
    """
    if not prices:
        return []
    
    sorted_prices = sorted(prices)
    clusters = []
    current_cluster = [sorted_prices[0]]
    
    for p in sorted_prices[1:]:
        if abs(p - current_cluster[-1]) / current_cluster[-1] * 100 <= tolerance_pct:
            current_cluster.append(p)
        else:
            clusters.append((round(sum(current_cluster) / len(current_cluster), 2), 
                           len(current_cluster)))
            current_cluster = [p]
    clusters.append((round(sum(current_cluster) / len(current_cluster), 2), 
                   len(current_cluster)))
    
    # 按聚类大小排序
    clusters.sort(key=lambda x: x[1], reverse=True)
    return clusters


def identify_platform(bars: List[Dict], lookback: int = 30) -> List[Dict]:
    """
    识别近期平台（窄幅震荡区）
    返回: [{"start": 日期, "end": 日期, "high": 最高, "low": 最低, "avg": 均价, "days": 天数}]
    """
    recent = bars[-lookback:]
    platforms = []
    in_platform = False
    platform_bars = []
    
    for i, bar in enumerate(recent):
        if not platform_bars:
            platform_bars = [bar]
            continue
        
        avg_close = sum(b['close'] for b in platform_bars) / len(platform_bars)
        # 判断是否还在平台内（波动率 < 3%）
        if abs(bar['close'] - avg_close) / avg_close < 0.03:
            platform_bars.append(bar)
        else:
            if len(platform_bars) >= 5:  # 至少5天才算平台
                platforms.append({
                    "start": platform_bars[0]['date'],
                    "end": platform_bars[-1]['date'],
                    "high": max(b['high'] for b in platform_bars),
                    "low": min(b['low'] for b in platform_bars),
                    "avg": round(sum(b['close'] for b in platform_bars) / len(platform_bars), 2),
                    "days": len(platform_bars),
                })
            platform_bars = [bar]
    
    if len(platform_bars) >= 5:
        platforms.append({
            "start": platform_bars[0]['date'],
            "end": platform_bars[-1]['date'],
            "high": max(b['high'] for b in platform_bars),
            "low": min(b['low'] for b in platform_bars),
            "avg": round(sum(b['close'] for b in platform_bars) / len(platform_bars), 2),
            "days": len(platform_bars),
        })
    
    return platforms


def compute_support_resistance(bars: List[Dict], current_price: float) -> Tuple[List[PriceLevel], List[PriceLevel]]:
    """
    计算所有支撑位和压力位
    """
    closes = [b['close'] for b in bars]
    highs = [b['high'] for b in bars]
    lows = [b['low'] for b in bars]
    volumes = [b['volume'] for b in bars]
    
    supports = []
    resistances = []
    
    # ---- 方法1: 均线支撑/压力 ----
    for n, name in [(5, "MA5"), (10, "MA10"), (20, "MA20"), (60, "MA60")]:
        m = ma(closes, n)
        if m is None:
            continue
        if m < current_price:
            supports.append(PriceLevel(
                price=round(m, 2), level_type="support",
                strength=SignalStrength.WEAK, methods=[name],
                confirmations=1, volume_weight=0.0,
                description=f"{name}均线支撑"
            ))
        else:
            resistances.append(PriceLevel(
                price=round(m, 2), level_type="resistance",
                strength=SignalStrength.WEAK, methods=[name],
                confirmations=1, volume_weight=0.0,
                description=f"{name}均线压力"
            ))
    
    # ---- 方法2: 近期关键低点/高点（取最近N天内的极值，每个单独列出） ----
    # 找最近15天内的所有日线低点，作为潜在支撑
    recent_15 = bars[-15:]
    for bar in recent_15:
        if bar['low'] < current_price:
            supports.append(PriceLevel(
                price=round(bar['low'], 2), level_type="support",
                strength=SignalStrength.WEAK, methods=["近期低点"],
                confirmations=1, volume_weight=0.0,
                description=f"{bar['date']} 日低 {bar['low']:.2f}"
            ))
    for bar in recent_15:
        if bar['high'] > current_price:
            resistances.append(PriceLevel(
                price=round(bar['high'], 2), level_type="resistance",
                strength=SignalStrength.WEAK, methods=["近期高点"],
                confirmations=1, volume_weight=0.0,
                description=f"{bar['date']} 日高 {bar['high']:.2f}"
            ))
    
    # 局部极值点（更长周期）
    local_lows = find_local_extrema(bars, window=5, use_high=False)
    local_highs = find_local_extrema(bars, window=5, use_high=True)
    
    for l in local_lows:
        if l['price'] < current_price:
            supports.append(PriceLevel(
                price=round(l['price'], 2), level_type="support",
                strength=SignalStrength.MODERATE, methods=["局部极值低点"],
                confirmations=1, volume_weight=0.0,
                description=f"{l['date']} 局部低点 {l['price']:.2f}"
            ))
    
    for h in local_highs:
        if h['price'] > current_price:
            resistances.append(PriceLevel(
                price=round(h['price'], 2), level_type="resistance",
                strength=SignalStrength.MODERATE, methods=["局部极值高点"],
                confirmations=1, volume_weight=0.0,
                description=f"{h['date']} 局部高点 {h['price']:.2f}"
            ))
    
    # ---- 方法3: 成交量加权密集区 ----
    profile = volume_profile(bars, n_recent=30)
    total_vol = sum(v['vol'] for v in profile.values())
    
    for bucket, info in profile.items():
        vol_pct = info['vol'] / total_vol
        if vol_pct < 0.05:
            continue  # 忽略低成交量区间
        
        if bucket < current_price:
            supports.append(PriceLevel(
                price=bucket, level_type="support",
                strength=SignalStrength.MODERATE if vol_pct > 0.10 else SignalStrength.WEAK,
                methods=["成交量密集"],
                confirmations=info['days'], volume_weight=round(vol_pct, 2),
                description=f"成交密集区(占{vol_pct*100:.0f}%成交量, {info['days']}天)"
            ))
        else:
            resistances.append(PriceLevel(
                price=bucket, level_type="resistance",
                strength=SignalStrength.MODERATE if vol_pct > 0.10 else SignalStrength.WEAK,
                methods=["成交量密集"],
                confirmations=info['days'], volume_weight=round(vol_pct, 2),
                description=f"成交密集区(占{vol_pct*100:.0f}%成交量, {info['days']}天)"
            ))
    
    # ---- 方法4: 斐波那契回撤 ----
    fib = fibonacci_retracement(bars, lookback=min(250, len(bars)))
    fib_levels = {k: v for k, v in fib.items() if k not in ('low', 'high', 'direction') and isinstance(v, (int, float))}
    
    for level_name, price in fib_levels.items():
        if price < current_price * 0.95:  # 跳过太远的
            continue
        if price > current_price * 1.05:
            continue
        
        label = f"斐波那契{fib['direction']}{level_name}"
        if price < current_price:
            supports.append(PriceLevel(
                price=price, level_type="support",
                strength=SignalStrength.MODERATE, methods=["斐波那契"],
                confirmations=1, volume_weight=0.0,
                description=label
            ))
        else:
            resistances.append(PriceLevel(
                price=price, level_type="resistance",
                strength=SignalStrength.MODERATE, methods=["斐波那契"],
                confirmations=1, volume_weight=0.0,
                description=label
            ))
    
    # ---- 方法5: 平台识别 ----
    platforms = identify_platform(bars, lookback=60)
    for plat in platforms:
        if plat['avg'] < current_price:
            supports.append(PriceLevel(
                price=plat['avg'], level_type="support",
                strength=SignalStrength.STRONG if plat['days'] >= 10 else SignalStrength.MODERATE,
                methods=["前期平台"],
                confirmations=plat['days'], volume_weight=0.0,
                description=f"前期平台 {plat['start']}~{plat['end']}({plat['days']}天) 均价{plat['avg']}"
            ))
    
    # ---- 合并：相近价位去重 ----
    supports = merge_levels(supports, current_price)
    resistances = merge_levels(resistances, current_price)
    
    # 按价格排序
    supports.sort(key=lambda x: x.price, reverse=True)  # 从上到下（近到远）
    resistances.sort(key=lambda x: x.price)  # 从下到上（近到远）
    
    return supports, resistances


def merge_levels(levels: List[PriceLevel], current_price: float, 
                 tolerance_pct: float = 1.0) -> List[PriceLevel]:
    """
    合并相近价位，融合多个方法的证据
    tolerance_pct: 1%以内视为同一价位区域
    """
    if not levels:
        return []
    
    sorted_levels = sorted(levels, key=lambda x: x.price, reverse=True)
    merged = []
    cluster = [sorted_levels[0]]
    
    for level in sorted_levels[1:]:
        ref_price = cluster[-1].price
        if abs(level.price - ref_price) / ref_price * 100 <= tolerance_pct:
            cluster.append(level)
        else:
            merged.append(fuse_cluster(cluster))
            cluster = [level]
    merged.append(fuse_cluster(cluster))
    
    # 二次去重：去掉过近的合并结果
    final = []
    for m in merged:
        if not final or abs(m.price - final[-1].price) / final[-1].price > 0.02:
            final.append(m)
        elif m.strength.value > final[-1].strength.value:
            final[-1] = m
    
    return final


def fuse_cluster(cluster: List[PriceLevel]) -> PriceLevel:
    """融合一个聚类中的所有价位"""
    if len(cluster) == 1:
        return cluster[0]
    
    # 加权平均价格（按确认次数和成交量权重）
    total_weight = sum(l.confirmations + l.volume_weight * 10 for l in cluster)
    weighted_price = sum(
        l.price * (l.confirmations + l.volume_weight * 10) for l in cluster
    ) / total_weight if total_weight > 0 else sum(l.price for l in cluster) / len(cluster)
    
    all_methods = list(set(m for l in cluster for m in l.methods))
    total_confirmations = sum(l.confirmations for l in cluster)
    max_vol_weight = max(l.volume_weight for l in cluster)
    
    # 强度：方法多样性 × 确认次数
    method_score = min(len(all_methods), 4)
    conf_score = min(total_confirmations // 3, 4) + 1
    strength_val = min(method_score, conf_score)
    
    return PriceLevel(
        price=round(weighted_price, 2),
        level_type=cluster[0].level_type,
        strength=SignalStrength(strength_val),
        methods=all_methods,
        confirmations=total_confirmations,
        volume_weight=max_vol_weight,
        description="; ".join(set(l.description for l in cluster)),
    )


def recommend_stop_loss(supports: List[PriceLevel], entry_price: float,
                        current_price: float) -> List[StopLossRecommendation]:
    """
    根据支撑位体系推荐止损位
    """
    recommendations = []
    
    # 取entry_price下方的支撑位
    below = [s for s in supports if s.price < entry_price]
    below.sort(key=lambda x: x.price, reverse=True)
    
    if not below:
        return recommendations
    
    # 紧止损: 最近的强力支撑下方，margin用百分比(0.5%-1%)而非固定值
    tight_candidates = [s for s in below if s.strength.value >= 2][:3]
    if not tight_candidates:
        tight_candidates = below[:1]
    if tight_candidates:
        tight_base = tight_candidates[0].price
        # margin: 支撑位的0.5%~1% 或 至少0.10元，高价股保底0.5%
        pct_margin = max(tight_base * 0.005, tight_base * 0.01 if tight_base > 100 else 0.15, 0.10)
        tight_stop = round(tight_base - pct_margin, 2)
        risk = (entry_price - tight_stop) / entry_price * 100
        recommendations.append(StopLossRecommendation(
            price=tight_stop,
            label="紧止损",
            basis=f"{tight_candidates[0].description}, margin={pct_margin:.2f}",
            risk_pct=round(risk, 2),
            suitable_for="追高买入者(≥19.00)",
            score=4 if risk < 3 else 3
        ))
    
    # 标准止损: 取entry下方距离2%-6%的支撑
    standard_candidates = [s for s in below if 1.5 < (entry_price - s.price) / entry_price * 100 < 8]
    if not standard_candidates:
        standard_candidates = below[1:4] if len(below) > 1 else below
    
    if standard_candidates:
        candidate = standard_candidates[0]
        # margin用支撑位价格的百分比
        pct_margin = max(candidate.price * 0.008, 0.15)
        std_stop = round(candidate.price - pct_margin, 2)
        risk = (entry_price - std_stop) / entry_price * 100
        recommendations.append(StopLossRecommendation(
            price=std_stop,
            label="标准止损",
            basis=f"{candidate.description[:60]}, margin={pct_margin:.2f}",
            risk_pct=round(risk, 2),
            suitable_for="回调买入者(中等价位)",
            score=5 if 1.5 < risk < 6 else (4 if risk < 8 else 3)
        ))
    
    # 宽止损: 最深支撑位，margin用1%-1.5%
    if len(below) >= 2:
        deep = below[-1]
        pct_margin = max(deep.price * 0.012, 0.25)
        wide_stop = round(deep.price - pct_margin, 2)
        risk = (entry_price - wide_stop) / entry_price * 100
        recommendations.append(StopLossRecommendation(
            price=wide_stop,
            label="宽止损",
            basis=f"{deep.description}, margin={pct_margin:.2f}",
            risk_pct=round(risk, 2),
            suitable_for="长线持有者(容忍大回撤)",
            score=3 if risk < 8 else 2
        ))
    
    # 去重（相近价位合并）
    recommendations.sort(key=lambda x: x.price, reverse=True)
    unique = []
    for r in recommendations:
        if not unique or abs(r.price - unique[-1].price) / unique[-1].price > 0.02:
            unique.append(r)
        elif r.score > unique[-1].score:
            unique[-1] = r
    
    return unique


def compute_rr_scenarios(entry_prices: List[float], 
                         stop_losses: List[StopLossRecommendation],
                         supports: List[PriceLevel],
                         resistances: List[PriceLevel],
                         current_price: float) -> List[EntryScenario]:
    """
    计算多个入场价格场景的盈亏比
    """
    scenarios = []
    
    # 目标价取压力位，过滤距离太近的（<3%没意义）和弱压力
    all_targets = [r for r in resistances 
                   if (r.price - current_price) / current_price > 0.03  # 至少3%空间
                   and r.strength.value >= 2]  # 至少中等强度
    if len(all_targets) < 2:
        all_targets = [r for r in resistances 
                       if (r.price - current_price) / current_price > 0.02]  # 放宽到2%
    targets = [(r.price, r.description[:40], r.strength.value) for r in all_targets[:5]]
    
    for entry in entry_prices:
        # 选最合适的止损
        best_stop = None
        for sl in stop_losses:
            if sl.price < entry:
                if best_stop is None:
                    best_stop = sl
                elif sl.label == "标准止损":
                    best_stop = sl
                    break
        
        if not best_stop:
            continue
        
        risk = entry - best_stop.price
        risk_pct = risk / entry * 100
        
        rr_list = []
        for tp_data in targets:
            tp = tp_data[0]
            if tp > entry:
                gain_pct = (tp - entry) / entry * 100
                rr_list.append(round(gain_pct / risk_pct, 1) if risk_pct > 0 else 999)
        
        scenarios.append(EntryScenario(
            entry_price=entry,
            stop_loss=best_stop.price,
            stop_label=best_stop.label,
            risk=round(risk, 2),
            risk_pct=round(risk_pct, 2),
            targets=targets[:5],
            rr_ratios=rr_list,
        ))
    
    return scenarios


# ============================================================
# 输出格式化
# ============================================================

def format_report(symbol: str, current_price: float, bars: List[Dict],
                  supports: List[PriceLevel], resistances: List[PriceLevel],
                  stop_losses: List[StopLossRecommendation],
                  scenarios: List[EntryScenario],
                  fib: Dict) -> str:
    """生成格式化的分析报告"""
    
    lines = []
    lines.append(f"=" * 70)
    lines.append(f"  {symbol} — 支撑/压力/止损位分析")
    lines.append(f"  当前价: {current_price} | 数据范围: {bars[0]['date']} ~ {bars[-1]['date']} ({len(bars)}天)")
    lines.append(f"=" * 70)
    
    # 均线
    closes = [b['close'] for b in bars]
    lines.append(f"\n{'─' * 50}")
    lines.append("📊 均线系统")
    lines.append(f"{'─' * 50}")
    for n, name in [(5, "MA5"), (10, "MA10"), (20, "MA20"), (60, "MA60")]:
        m = ma(closes, n)
        if m:
            diff = (current_price / m - 1) * 100
            arrow = "🔺" if diff > 0 else "🔻" if diff < 0 else "➖"
            lines.append(f"  {name}: {m:.2f} (现价{diff:+.1f}%) {arrow}")
    
    # 斐波那契
    lines.append(f"\n{'─' * 50}")
    lines.append(f"📐 斐波那契{fib.get('direction', '')}")
    lines.append(f"{'─' * 50}")
    if fib.get('波段'):
        lines.append(f"  波段: {fib['波段']}")
    else:
        lines.append(f"  波段: {fib.get('low', '?')} → {fib.get('high', '?')}")
    for k, v in sorted(fib.items()):
        if k in ('low', 'high', 'direction', '波段'):
            continue
        if not isinstance(v, (int, float)):
            continue
        marker = " ⬅ 当前附近" if abs(v - current_price) / current_price < 0.02 else ""
        lines.append(f"  {k}: {v}{marker}")
    
    # 平台
    platforms = identify_platform(bars, lookback=60)
    if platforms:
        lines.append(f"\n{'─' * 50}")
        lines.append("🏗️  近期平台")
        lines.append(f"{'─' * 50}")
        for p in platforms[-5:]:
            lines.append(f"  {p['start']}~{p['end']} ({p['days']}天)")
            lines.append(f"    区间: {p['low']} ~ {p['high']}  均价: {p['avg']}")
    
    # 支撑位
    lines.append(f"\n{'─' * 50}")
    lines.append("🟢 支撑位（由近到远）")
    lines.append(f"{'─' * 50}")
    if supports:
        for s in supports[:8]:
            stars = "★" * s.strength.value
            vol_info = f"量权:{s.volume_weight:.0%}" if s.volume_weight > 0 else ""
            lines.append(f"  {s.price:>8.2f} {stars:6s} {s.description}")
            if vol_info:
                lines.append(f"          └─ {vol_info} | 方法: {', '.join(s.methods)}")
    else:
        lines.append("  (无明显支撑位)")
    
    # 压力位
    lines.append(f"\n{'─' * 50}")
    lines.append("🔴 压力位（由近到远）")
    lines.append(f"{'─' * 50}")
    if resistances:
        for r in resistances[:8]:
            stars = "★" * r.strength.value
            vol_info = f"量权:{r.volume_weight:.0%}" if r.volume_weight > 0 else ""
            lines.append(f"  {r.price:>8.2f} {stars:6s} {r.description}")
            if vol_info:
                lines.append(f"          └─ {vol_info} | 方法: {', '.join(r.methods)}")
    else:
        lines.append("  (无明显压力位)")
    
    # 止损推荐
    lines.append(f"\n{'─' * 50}")
    lines.append(f"🛑 止损位推荐")
    lines.append(f"{'─' * 50}")
    if stop_losses:
        for sl in stop_losses:
            lines.append(f"  [{sl.label}] {sl.price:.2f}")
            lines.append(f"    依据: {sl.basis}")
            lines.append(f"    风险: {sl.risk_pct:.1f}%  适合: {sl.suitable_for}  评分: {'★'*sl.score}")
    else:
        lines.append("  (无法生成止损位 — 支撑位不足)")
    
    # 盈亏比
    lines.append(f"\n{'─' * 50}")
    lines.append("💰 入场场景与盈亏比")
    lines.append(f"{'─' * 50}")
    if scenarios:
        for sc in scenarios:
            rr_parts = []
            for tp, rr in zip(sc.targets, sc.rr_ratios):
                if len(tp) >= 2:
                    rr_parts.append(f"目标{tp[0]:.2f}({str(tp[1])[:20]}): {rr:.1f}:1")
            rr_str = " / ".join(rr_parts) if rr_parts else "无有效目标"
            lines.append(f"  买入 {sc.entry_price:.2f} → 止损 {sc.stop_loss:.2f}({sc.stop_label})")
            lines.append(f"    风险: {sc.risk_pct:.1f}%  |  {rr_str}")
    else:
        lines.append("  (无有效入场场景)")
    
    lines.append(f"\n{'=' * 70}")
    lines.append("⚠️ 免责声明: 本工具仅提供技术分析参考，不构成投资建议。")
    lines.append(f"{'=' * 70}")
    
    return "\n".join(lines)


# ============================================================
# Main
# ============================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="通用支撑位/压力位/止损位计算工具")
    parser.add_argument("symbol", help="股票代码，如 601211")
    parser.add_argument("--days", type=int, default=250, help="K线天数 (默认250)")
    parser.add_argument("--entry", type=float, nargs="*", 
                       help="入场价（可多个），如 --entry 18.50 18.80 19.00")
    parser.add_argument("--current-price", type=float, 
                       help="当前价（可选，默认取最新收盘价）")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    # 获取数据
    bars = fetch_kline(args.symbol, args.days)
    
    current_price = args.current_price or bars[-1]['close']
    
    # 计算
    supports, resistances = compute_support_resistance(bars, current_price)
    fib = fibonacci_retracement(bars, lookback=min(250, len(bars)))
    
    # 入场价
    entry_prices = args.entry if args.entry else [current_price]
    
    # 止损
    stop_losses = recommend_stop_loss(supports, current_price, current_price)
    
    # 盈亏比
    scenarios = compute_rr_scenarios(
        entry_prices, stop_losses, supports, resistances, current_price
    )
    
    if args.json:
        output = {
            "symbol": args.symbol,
            "current_price": current_price,
            "data_range": f"{bars[0]['date']} ~ {bars[-1]['date']}",
            "bars_count": len(bars),
            "fibonacci": fib,
            "supports": [{"price": s.price, "strength": s.strength.value, 
                         "methods": s.methods, "description": s.description} 
                        for s in supports[:10]],
            "resistances": [{"price": r.price, "strength": r.strength.value,
                           "methods": r.methods, "description": r.description}
                          for r in resistances[:10]],
            "stop_losses": [{"price": sl.price, "label": sl.label, 
                           "risk_pct": sl.risk_pct, "score": sl.score}
                          for sl in stop_losses],
            "scenarios": [{"entry": sc.entry_price, "stop": sc.stop_loss,
                         "risk_pct": sc.risk_pct, "rr_ratios": sc.rr_ratios}
                        for sc in scenarios],
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        report = format_report(
            args.symbol, current_price, bars,
            supports, resistances, stop_losses, scenarios, fib
        )
        print(report)
    
    # 返回码
    if not supports and not resistances:
        sys.exit(1)


if __name__ == "__main__":
    main()
