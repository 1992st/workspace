#!/usr/bin/env python3
"""
分析前置数据门控 (Pre-Analysis Data Gate)

在开始任何分析之前，必须先通过此门控。
返回 ready=True 才能继续分析，否则返回缺失清单。

用法:
  python3 analysis_gate.py 601211
  python3 analysis_gate.py 601211 --strict   # 严格模式：任何缺失都拒绝
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


WORKSPACE = Path(__file__).resolve().parents[2]
STOCK_CLIENT = WORKSPACE / "skills/stock-data/scripts/stock_client.py"


def _run(cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, str(STOCK_CLIENT), *cmd],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(WORKSPACE),
            env={**__import__('os').environ, "PYTHONUNBUFFERED": "1"},
        )
        if result.returncode != 0:
            stderr_tail = result.stderr.strip()[-300:] if result.stderr else ""
            return {"success": False, "error": f"exit={result.returncode}: {stderr_tail}"}
        if not result.stdout.strip():
            return {"success": False, "error": "空输出"}
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"超时 {timeout}s"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON解析失败: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class AnalysisGate:
    """分析前置门控：必须通过才能开始分析"""

    # 必须获取的数据维度及其最低标准
    REQUIRED_CHECKS = {
        "kline_60d": {
            "description": "60个交易日K线（日线，前复权）",
            "command": lambda s: ["kline", s, "60"],
            "min_bars": 40,  # 至少40根有效K线（允许少量缺失）
            "weight": 30,     # 权重分
        },
        "quote": {
            "description": "实时行情（最新价/涨跌幅/量比/PE/PB/市值）",
            "command": lambda s: ["quote", s],
            "required_fields": ["price", "pe", "change_pct", "volume", "turnover_rate"],
            "weight": 25,
        },
        "market": {
            "description": "大盘指数行情（上证/深证/创业板）",
            "command": lambda s: ["market"],
            "required_indices": ["000001", "399001", "399006"],
            "weight": 15,
        },
        "sector": {
            "description": "行业板块信息 + 板块热度",
            "command": lambda s: ["sector", s],
            "required_fields": ["industry"],
            "weight": 15,
        },
        "finance": {
            "description": "PE/PB/市值（估值数据）",
            "command": lambda s: ["finance", s],
            "required_fields": ["pe_ttm", "pb"],
            "weight": 15,
        },
    }

    def __init__(self, symbol: str, strict: bool = False):
        self.symbol = symbol.zfill(6)
        self.strict = strict
        self.results: Dict[str, Dict[str, Any]] = {}
        self.gaps: List[str] = []
        self.warnings: List[str] = []
        self.total_score = 100
        self.ready = False

    def run(self) -> Dict[str, Any]:
        """执行所有检查，返回门控结果"""
        for check_id, config in self.REQUIRED_CHECKS.items():
            self._check_one(check_id, config)

        # 计算就绪分数
        self._compute_readiness()

        return self._build_report()

    def _check_one(self, check_id: str, config: Dict[str, Any]) -> None:
        """执行单项数据检查"""
        print(f"  📡 {config['description']}...", end=" ", flush=True)

        cmd = config["command"](self.symbol)
        result = _run(cmd)

        if not result.get("success"):
            msg = f"[{check_id}] 获取失败: {result.get('error', 'unknown')}"
            self.gaps.append(msg)
            self.total_score -= config["weight"]
            print(f"❌ {msg}")
            return

        data = result.get("data", {})

        # --- 针对不同类型的数据做质量检查 ---

        if check_id == "kline_60d":
            bars = data.get("bars", [])
            count = len(bars)
            if count < config["min_bars"]:
                msg = f"[{check_id}] K线不足: 仅{count}根 (需要≥{config['min_bars']})"
                self.gaps.append(msg)
                self.total_score -= config["weight"]
                print(f"⚠️ {msg}")
            else:
                # 检查最新数据时效性
                latest_date = bars[-1].get("date", "") if bars else ""
                print(f"✅ {count}根K线 (最新:{latest_date})")

        elif check_id == "quote":
            missing = [f for f in config["required_fields"] if data.get(f) is None]
            if missing:
                msg = f"[{check_id}] 缺失字段: {missing}"
                self.warnings.append(msg)
                self.total_score -= config["weight"] // 2
                print(f"⚠️ {msg}")
            else:
                print(f"✅ 量比={data.get('volume_ratio')} PE={data.get('pe')}")

        elif check_id == "market":
            indices = data.get("indices", [])
            found_codes = {i.get("code", "") for i in indices}
            missing_idx = [c for c in config["required_indices"] if c not in found_codes]
            if missing_idx:
                msg = f"[{check_id}] 缺失指数: {missing_idx}"
                self.warnings.append(msg)
                self.total_score -= config["weight"] // 2
                print(f"⚠️ {msg}")
            else:
                changes = [f"{i['name']}:{i.get('change_pct', 0):+.1f}%" for i in indices[:3]]
                print(f"✅ {', '.join(changes)}")

        elif check_id == "sector":
            industry = data.get("industry", "")
            if not industry:
                msg = f"[{check_id}] 无法确定行业"
                self.warnings.append(msg)
                self.total_score -= config["weight"] // 2
                print(f"⚠️ {msg}")
            else:
                print(f"✅ {industry}")

        elif check_id == "finance":
            missing = [f for f in config["required_fields"] if data.get(f) is None]
            if missing:
                msg = f"[{check_id}] 缺失字段: {missing}"
                self.warnings.append(msg)
                self.total_score -= config["weight"] // 2
                print(f"⚠️ {msg}")
            else:
                print(f"✅ PE={data.get('pe_ttm')} PB={data.get('pb')}")

        self.results[check_id] = result

    def _compute_readiness(self) -> None:
        """根据 gaps 和 score 判断是否就绪"""
        if self.strict:
            # 严格模式：零容忍
            self.ready = len(self.gaps) == 0 and self.total_score >= 90
        else:
            # 标准模式：允许少量警告，不能有硬缺失
            self.ready = len(self.gaps) == 0 and self.total_score >= 60

    def _build_report(self) -> Dict[str, Any]:
        """生成门控报告"""
        return {
            "symbol": self.symbol,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
            "ready": self.ready,
            "total_score": self.total_score,
            "gaps": self.gaps,
            "warnings": self.warnings,
            "mode": "strict" if self.strict else "standard",
            "verdict": self._verdict(),
        }

    def _verdict(self) -> str:
        if self.ready:
            return "PASS — 可以开始分析"
        if len(self.gaps) > 0:
            gap_names = [g.split("]")[0].replace("[", "") for g in self.gaps]
            return f"BLOCKED — 以下数据缺失: {', '.join(gap_names)}。先补数据再分析。"
        return "CAUTION — 数据有警告，置信度需降低"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 analysis_gate.py <股票代码> [--strict]", file=sys.stderr)
        print("  --strict  严格模式：任何字段缺失都拒绝", file=sys.stderr)
        raise SystemExit(1)

    symbol = sys.argv[1]
    strict = "--strict" in sys.argv

    gate = AnalysisGate(symbol, strict=strict)
    print(f"\n🔒 数据门控检查: {symbol}")
    print("=" * 50)
    report = gate.run()
    print("=" * 50)

    # 输出 JSON 报告（供 agent 读取）
    if "--json" in sys.argv or "-j" in sys.argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"\n📊 门控结果:")
        print(f"   就绪分数: {report['total_score']}/100")
        print(f"   是否通过: {'✅ PASS' if report['ready'] else '❌ BLOCKED'}")
        print(f"   判定: {report['verdict']}")

        if report["gaps"]:
            print(f"\n🔴 硬缺失 ({len(report['gaps'])}项):")
            for g in report["gaps"]:
                print(f"   - {g}")

        if report["warnings"]:
            print(f"\n🟡 警告 ({len(report['warnings'])}项):")
            for w in report["warnings"]:
                print(f"   - {w}")

    if not report["ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
