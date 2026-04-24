#!/usr/bin/env python3
"""
Win_Stock 统一数据客户端
三层降级：stock-skill → browser_fetch → cache/skip
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime


class StockDataClient:
    """
    统一股票数据客户端
    
    使用优先级：
    1. stock-skill（主源）
    2. browser_fetch（降级）
    3. 本地缓存（兜底）
    4. 标记失败（彻底不可用）
    """
    
    def __init__(self, workspace=None):
        self.workspace = Path(workspace or "/Volumes/zhangstExtern/openclaw/workspace/win_stock")
        self.skill_script = self.workspace / "skills/stock-skill/scripts/run.py"
        self.browser_script = self.workspace / "skills/stock-data/scripts/browser_fetch.py"
        self.cache_dir = self.workspace / "data/cache"
        self.error_log = self.workspace / "logs/errors/data_fetch_failures.jsonl"
        
        # 确保目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.error_log.parent.mkdir(parents=True, exist_ok=True)
    
    def get_quote(self, symbol: str) -> dict:
        """
        获取实时行情，三层降级
        """
        errors = []
        
        # 第一层：stock-skill
        result = self._call_skill("quote.get", {"symbol": symbol, "market": "CN-A"})
        if result and result.get("status") in ("ok", "degraded"):
            return self._normalize_skill_result(result, symbol)
        elif result:
            errors.append(f"stock-skill: {result.get('error', 'unknown')}")
        else:
            errors.append("stock-skill: 调用失败")
        
        # 第二层：browser_fetch
        result = self._call_browser(symbol)
        if result and result.get("success"):
            return result
        elif result:
            errors.append(f"browser: {result.get('error', 'unknown')}")
        else:
            errors.append("browser: 调用失败")
        
        # 第三层：缓存
        cached = self._get_cache(symbol, "quote")
        if cached:
            cached["errors"] = errors + [f"使用 {cached.get('cache_age', 0):.1f} 小时前缓存"]
            return cached
        
        # 彻底失败
        self._log_error(symbol, errors)
        return {
            "success": False,
            "source": "unavailable",
            "data": None,
            "quality_score": 0,
            "is_cached": False,
            "errors": errors
        }
    
    def get_kline(self, symbol: str, timeframe="1d", limit=30) -> dict:
        """获取K线数据"""
        result = self._call_skill("kline.get", {
            "symbol": symbol,
            "market": "CN-A",
            "timeframe": timeframe,
            "limit": limit
        })
        
        if result and result.get("status") in ("ok", "degraded"):
            return {
                "success": True,
                "source": result.get("meta", {}).get("source", "stock-skill"),
                "data": result.get("data"),
                "quality_score": 95,
                "is_cached": False,
                "errors": []
            }
        
        # K线暂不支持 browser 降级，直接返回失败
        return {
            "success": False,
            "source": "unavailable",
            "data": None,
            "quality_score": 0,
            "is_cached": False,
            "errors": ["K线数据暂仅支持 stock-skill 获取"]
        }
    
    def _call_skill(self, action: str, input_data: dict) -> dict:
        """调用 stock-skill"""
        try:
            cmd = [
                "python3", str(self.skill_script),
                "run", "--skill", "stock", "--action", action,
                "--input", json.dumps(input_data)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace)
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
            return None
            
        except Exception as e:
            return None
    
    def _call_browser(self, symbol: str) -> dict:
        """调用 browser_fetch"""
        try:
            cmd = ["python3", str(self.browser_script), symbol]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(self.workspace)
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
            return None
            
        except Exception as e:
            return None
    
    def _normalize_skill_result(self, result: dict, symbol: str) -> dict:
        """统一 stock-skill 输出格式"""
        data = result.get("data", {})
        meta = result.get("meta", {})
        
        return {
            "success": True,
            "source": meta.get("source", "stock-skill"),
            "data": {
                "symbol": symbol,
                "name": data.get("name", symbol),
                "price": data.get("price"),
                "change": data.get("change"),
                "change_pct": data.get("change_pct"),
                "open": data.get("open"),
                "high": data.get("high"),
                "low": data.get("low"),
                "pre_close": data.get("pre_close"),
                "volume": data.get("volume"),
                "amount": data.get("amount"),
                "timestamp": meta.get("fetched_at", datetime.now().isoformat()),
            },
            "quality_score": result.get("quality", {}).get("score", 90),
            "is_cached": False,
            "errors": []
        }
    
    def _get_cache(self, symbol: str, data_type: str, max_age_hours=24) -> dict:
        """获取缓存数据"""
        cache_file = self.cache_dir / symbol / f"{data_type}.json"
        
        if not cache_file.exists():
            return None
        
        # 检查年龄
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        
        if age_hours > max_age_hours:
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            return {
                "success": True,
                "source": "cache",
                "data": data,
                "quality_score": max(0, 100 - int(age_hours * 2)),
                "is_cached": True,
                "cache_age": age_hours,
                "errors": []
            }
        except:
            return None
    
    def _save_cache(self, symbol: str, data_type: str, data: dict):
        """保存缓存"""
        cache_dir = self.cache_dir / symbol
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_file = cache_dir / f"{data_type}.json"
        with open(cache_file, 'w') as f:
            json.dump(data, f, ensure_ascii=False)
    
    def _log_error(self, symbol: str, errors: list):
        """记录错误"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "errors": errors,
            "status": "pending"
        }
        
        with open(self.error_log, 'a') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


def main():
    """命令行测试"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 stock_client.py <symbol>", file=sys.stderr)
        sys.exit(1)
    
    symbol = sys.argv[1]
    client = StockDataClient()
    
    print(f"获取 {symbol} 行情...")
    result = client.get_quote(symbol)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
