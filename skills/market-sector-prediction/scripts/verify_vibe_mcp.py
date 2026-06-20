from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


CN_TZ = timezone(timedelta(hours=8))
DEFAULT_COMMAND = "/Volumes/zhangstExtern/openclaw/runtime/vibe-trading/vibe-trading-mcp-wrapper.sh"
VENV_SITE = "/Volumes/zhangstExtern/openclaw/runtime/vibe-trading-venv/lib/python3.14/site-packages"

if VENV_SITE not in sys.path:
    sys.path.insert(0, VENV_SITE)

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return value


async def _verify(command: str, call_tool: str | None, call_payload: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "checked_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
        "command": command,
        "server_initialized": False,
        "tools_count": 0,
        "tools": [],
        "tool_call": None,
        "errors": [],
    }

    if not Path(command).exists():
        result["errors"].append(f"command not found: {command}")
        return result

    try:
        params = StdioServerParameters(command=command, args=[], env={})
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as session:
                init = await asyncio.wait_for(session.initialize(), timeout=20)
                result["server_initialized"] = True
                result["server_info"] = _to_jsonable(init)

                listed = await asyncio.wait_for(session.list_tools(), timeout=20)
                tools = sorted(
                    {
                        tool.name
                        for tool in listed.tools
                        if getattr(tool, "name", None)
                    }
                )
                result["tools_count"] = len(tools)
                result["tools"] = tools

                if call_tool:
                    if call_tool not in tools:
                        result["tool_call"] = {
                            "tool": call_tool,
                            "status": "skipped",
                            "reason": "tool not available",
                        }
                    else:
                        try:
                            payload = call_payload or {}
                            called = await asyncio.wait_for(session.call_tool(call_tool, payload), timeout=60)
                            result["tool_call"] = {
                                "tool": call_tool,
                                "status": "ok",
                                "payload": payload,
                                "result": _to_jsonable(called),
                            }
                        except Exception as exc:
                            result["tool_call"] = {
                                "tool": call_tool,
                                "status": "error",
                                "error": str(exc),
                            }
    except Exception as exc:
        result["errors"].append(str(exc))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Vibe-Trading MCP over stdio.")
    parser.add_argument("--command", default=DEFAULT_COMMAND)
    parser.add_argument("--call-tool", default="")
    parser.add_argument("--payload", default="{}")
    args = parser.parse_args()

    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as exc:
        print(json.dumps({"status": "error", "error": f"invalid payload json: {exc}"}, ensure_ascii=False, indent=2))
        return 2
    if not isinstance(payload, dict):
        print(json.dumps({"status": "error", "error": "payload must be a JSON object"}, ensure_ascii=False, indent=2))
        return 2

    result = asyncio.run(_verify(args.command, args.call_tool or None, payload))
    status = "ok" if result["server_initialized"] and result["tools_count"] > 0 and not result["errors"] else "error"
    print(json.dumps({"status": status, "data": result}, ensure_ascii=False, indent=2))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
