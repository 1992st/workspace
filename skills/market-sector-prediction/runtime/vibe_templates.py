from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


CN_TZ = timezone(timedelta(hours=8))
MARKET_INDEX_CODES = ["000001.SH", "399001.SZ", "399006.SZ"]
SECTOR_REPRESENTATIVES = {
    "证券": ["601211.SH", "600030.SH", "000776.SZ", "601688.SH", "600837.SH"],
}


def date_window(horizon: str) -> tuple[str, str]:
    end = datetime.now(CN_TZ)
    days = 45 if horizon == "short" else 120
    return (end - timedelta(days=days)).strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def market_data_payload(codes: List[str], horizon: str, source: str = "akshare") -> Dict[str, Any]:
    start_date, end_date = date_window(horizon)
    return {
        "codes": codes,
        "start_date": start_date,
        "end_date": end_date,
        "source": source,
        "interval": "1D",
        "max_rows": 120,
    }


def factor_payload(codes: List[str], horizon: str, factor_name: str = "turnover_rate", source: str = "akshare") -> Dict[str, Any]:
    start_date, end_date = date_window(horizon)
    return {
        "codes": codes,
        "factor_name": factor_name,
        "start_date": start_date,
        "end_date": end_date,
        "source": source,
        "top_n": min(10, max(1, len(codes) // 3)),
        "bottom_n": min(10, max(1, len(codes) // 3)),
    }


def factor_csv_payload(root: Path, target_type: str, target: str, horizon: str, codes: List[str]) -> Dict[str, Any]:
    run_dir = build_run_dir(root, target_type, target, horizon, codes)
    factor_csv = run_dir / "artifacts" / "factor_values.csv"
    return_csv = run_dir / "artifacts" / "forward_returns.csv"
    dates = _sample_dates(horizon)
    factor_rows = []
    return_rows = []
    for idx, date in enumerate(dates):
        factor_row = {"date": date}
        return_row = {"date": date}
        for pos, code in enumerate(codes):
            factor_row[code] = round((pos + 1) * 0.1 + idx * 0.01, 4)
            return_row[code] = round(((pos % 5) - 2) * 0.002 + idx * 0.0001, 5)
        factor_rows.append(factor_row)
        return_rows.append(return_row)
    _write_csv(factor_csv, factor_rows)
    _write_csv(return_csv, return_rows)
    output_dir = run_dir / "factor_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    return {
        "factor_csv": str(factor_csv),
        "return_csv": str(return_csv),
        "output_dir": str(output_dir),
        "n_groups": min(5, max(2, len(codes))),
    }


def build_run_dir(root: Path, target_type: str, target: str, horizon: str, codes: List[str]) -> Path:
    date = datetime.now(CN_TZ).strftime("%Y-%m-%d")
    safe_target = target.replace("/", "_").replace(":", "_")
    run_dir = root / "data" / "predictions" / "vibe_runs" / f"{date}_{target_type}_{safe_target}_{horizon}"
    code_dir = run_dir / "code"
    artifacts = run_dir / "artifacts"
    code_dir.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    config = {
        "source": "tushare" if _tushare_token_available(root) else "akshare",
        "codes": codes,
        "start_date": date_window(horizon)[0],
        "end_date": date_window(horizon)[1],
        "initial_cash": 1000000,
        "commission": 0.0003,
        "slippage": 0.0005,
    }
    (run_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    (code_dir / "signal_engine.py").write_text(_signal_engine_code(), encoding="utf-8")
    return run_dir


def write_local_ohlcv(run_dir: Path, snapshots: List[Dict[str, Any]], min_rows: int = 20) -> Dict[str, Any]:
    artifacts = run_dir / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    insufficient: list[str] = []
    for item in snapshots:
        code = _vibe_code(str(item.get("code", "")))
        rows = item.get("ohlcv") or item.get("bars") or []
        if not rows and item.get("date") and item.get("price"):
            rows = [
                {
                    "date": item.get("date"),
                    "open": item.get("open") or item.get("price"),
                    "high": item.get("high") or item.get("price"),
                    "low": item.get("low") or item.get("price"),
                    "close": item.get("price"),
                    "volume": item.get("volume") or 0,
                }
            ]
        normalized = [_normalize_ohlcv_row(row) for row in rows if _normalize_ohlcv_row(row)]
        if len(normalized) < min_rows:
            insufficient.append(code)
            continue
        path = artifacts / f"ohlcv_{code}.csv"
        _write_csv(path, normalized)
        written.append(str(path))
    return {"written": written, "insufficient": insufficient, "min_rows": min_rows}


def _signal_engine_code() -> str:
    return """from __future__ import annotations

from typing import Dict
import pandas as pd


class SignalEngine:
    def generate(self, data_map: Dict[str, pd.DataFrame]) -> Dict[str, pd.Series]:
        signals: Dict[str, pd.Series] = {}
        for code, data in data_map.items():
            if data is None or data.empty or "close" not in data:
                continue
            close = data["close"]
            ma5 = close.rolling(5).mean()
            ma20 = close.rolling(20).mean()
            signal = pd.Series(0.0, index=data.index)
            signal.loc[ma5 > ma20] = 1.0
            signal.loc[ma5 < ma20] = 0.0
            signals[code] = signal.fillna(0.0)
        return signals
"""


def _tushare_token_available(root: Path) -> bool:
    if os.getenv("TUSHARE_TOKEN", "").strip():
        return True
    env_path = root.parents[1] / "runtime" / "vibe-trading" / "vibe-env"
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("TUSHARE_TOKEN=") and line.split("=", 1)[1].strip():
                return True
    except OSError:
        return False
    return False


def _sample_dates(horizon: str) -> list[str]:
    days = 30 if horizon == "short" else 90
    end = datetime.now(CN_TZ)
    return [(end - timedelta(days=days - idx)).strftime("%Y-%m-%d") for idx in range(days)]


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = list(rows[0].keys())
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(str(row.get(column, "")) for column in columns))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _vibe_code(code: str) -> str:
    code = code.strip()
    if not code:
        return "unknown"
    if "." in code:
        return code
    suffix = "SH" if code.startswith(("5", "6", "9", "0")) and code == "000001" else "SZ"
    if code.startswith(("6", "9")):
        suffix = "SH"
    return f"{code}.{suffix}"


def _normalize_ohlcv_row(row: Dict[str, Any]) -> Dict[str, Any] | None:
    date = row.get("date") or row.get("日期")
    close = row.get("close", row.get("收盘", row.get("price")))
    if not date or close is None:
        return None
    return {
        "date": date,
        "open": row.get("open", row.get("开盘", close)),
        "high": row.get("high", row.get("最高", close)),
        "low": row.get("low", row.get("最低", close)),
        "close": close,
        "volume": row.get("volume", row.get("成交量", 0)),
    }
