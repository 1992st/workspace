#!/usr/bin/env python3
"""
Browser 辅助数据获取脚本
当 stock-skill 失败时，通过 HTTP 请求获取股票数据
"""

import sys
import json
import urllib.request
from datetime import datetime


def fetch_tencent_quote(symbol: str) -> dict:
    """
    从腾讯财经获取实时行情
    URL: http://qt.gtimg.cn/q=sh{code} 或 sz{code}
    
    返回字段索引（从0开始，以~分隔）：
    0: 市场标识 1=上海 2=深圳
    1: 股票名称
    2: 股票代码
    3: 当前价格
    4: 昨收
    5: 今开
    6: 成交量（手）
    7: 外盘
    8: 内盘
    9-18: 买1-5价格/数量
    19-28: 卖1-5价格/数量
    29: 时间戳 YYYYMMDDHHMMSS
    30: 涨跌额
    31: 涨跌幅%
    32: 最高价
    33: 最低价
    34: 最新价/成交量/成交额 组合
    35: 成交量（重复）
    36: 成交额（万）
    37: 换手率%
    38: 市盈率TTM
    ...
    """
    prefix = "sh" if symbol.startswith("6") else "sz"
    url = f"http://qt.gtimg.cn/q={prefix}{symbol}"
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://stock.finance.qq.com/"
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("gb2312", errors="ignore")
            
            if not raw.startswith(f"v_{prefix}{symbol}"):
                return {"success": False, "error": "Invalid response format"}
            
            # 提取引号内的数据
            start = raw.find('"') + 1
            end = raw.rfind('"')
            data_str = raw[start:end]
            parts = data_str.split("~")
            
            # 确保有足够字段
            if len(parts) < 39:
                return {"success": False, "error": f"Incomplete data: {len(parts)} fields, need >=39"}
            
            # 精确字段映射
            def get_str(idx):
                return parts[idx] if idx < len(parts) and parts[idx] else None
            
            def get_float(idx):
                val = get_str(idx)
                if val is None:
                    return None
                try:
                    return float(val)
                except ValueError:
                    return None
            
            def get_int(idx):
                val = get_str(idx)
                if val is None:
                    return None
                try:
                    return int(val)
                except ValueError:
                    return None
            
            # 解析组合字段 (格式: 最新价/成交量/成交额)
            combo = get_str(34) or ""
            amount = None
            if "/" in combo:
                combo_parts = combo.split("/")
                if len(combo_parts) >= 3:
                    try:
                        amount = int(combo_parts[2])
                    except ValueError:
                        pass
            
            result = {
                "success": True,
                "source": "browser-tencent",
                "data": {
                    "symbol": symbol,
                    "name": get_str(1) or symbol,
                    "price": get_float(3),
                    "pre_close": get_float(4),
                    "open": get_float(5),
                    "volume": get_int(6) * 100 if get_int(6) else None,  # 手→股
                    "high": get_float(33),
                    "low": get_float(34),
                    "amount": amount,
                    "change": get_float(31),
                    "change_pct": get_float(32),
                    "turnover_rate": get_float(38),
                    "pe_ttm": get_float(39),
                    "timestamp": get_str(30),
                },
                "quality_score": 90,
                "is_cached": False,
                "errors": []
            }
            
            # 验证核心数据
            if result["data"]["price"] is None or result["data"]["price"] <= 0:
                result["success"] = False
                result["error"] = "Invalid price data"
                result["quality_score"] = 0
            
            return result
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Tencent fetch failed: {str(e)}",
            "source": "browser-tencent",
            "data": None,
            "quality_score": 0,
            "is_cached": False,
            "errors": [str(e)]
        }


def fetch_eastmoney_quote(symbol: str) -> dict:
    """
    从东方财富获取实时行情（备用）
    """
    market = "1" if symbol.startswith("6") else "0"
    url = (
        f"https://push2.eastmoney.com/api/qt/stock/get"
        f"?secid={market}.{symbol}"
        f"&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f170"
    )
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/"
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            
            data = raw.get("data", {})
            if not data:
                return {"success": False, "error": "No data in response"}
            
            def em_float(field):
                val = data.get(field)
                return val / 100 if val else None
            
            result = {
                "success": True,
                "source": "browser-eastmoney",
                "data": {
                    "symbol": data.get("f57"),
                    "name": data.get("f58"),
                    "price": em_float("f43"),
                    "high": em_float("f44"),
                    "low": em_float("f45"),
                    "open": em_float("f46"),
                    "volume": data.get("f47"),
                    "amount": data.get("f48"),
                    "pre_close": em_float("f60"),
                    "change_pct": em_float("f170"),
                    "timestamp": datetime.now().isoformat(),
                },
                "quality_score": 85,
                "is_cached": False,
                "errors": []
            }
            
            # 计算涨跌额
            if result["data"]["price"] and result["data"]["pre_close"]:
                result["data"]["change"] = round(
                    result["data"]["price"] - result["data"]["pre_close"], 2
                )
            
            return result
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Eastmoney fetch failed: {str(e)}",
            "source": "browser-eastmoney",
            "data": None,
            "quality_score": 0,
            "is_cached": False,
            "errors": [str(e)]
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 browser_fetch.py <symbol> [tencent|eastmoney|auto]", file=sys.stderr)
        sys.exit(1)
    
    symbol = sys.argv[1]
    source = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    if source == "tencent":
        result = fetch_tencent_quote(symbol)
    elif source == "eastmoney":
        result = fetch_eastmoney_quote(symbol)
    else:
        # auto: 先尝试腾讯，失败再尝试东方财富
        result = fetch_tencent_quote(symbol)
        if not result["success"]:
            result = fetch_eastmoney_quote(symbol)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
