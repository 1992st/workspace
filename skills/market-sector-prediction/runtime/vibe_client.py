from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Dict

from capability_probe import CapabilityProbe
from tool_whitelist import ToolPolicy

VIBE_SITE_PACKAGES = "/Volumes/zhangstExtern/openclaw/runtime/vibe-trading-venv/lib/python3.14/site-packages"


class VibeClient:
    """Controlled Vibe-Trading client.

    This adapter intentionally does not expose arbitrary MCP tools. Real MCP
    invocation can be wired behind call_tool once the manifest is available.
    """

    def __init__(self, probe: CapabilityProbe | None = None, policy: ToolPolicy | None = None) -> None:
        self.policy = policy or ToolPolicy.default()
        self.probe_runner = probe or CapabilityProbe(policy=self.policy)
        self._capabilities: Dict[str, Any] | None = None

    def health_check(self) -> Dict[str, Any]:
        self._capabilities = self.probe_runner.probe()
        return self._capabilities

    @property
    def capabilities(self) -> Dict[str, Any]:
        if self._capabilities is None:
            return self.health_check()
        return self._capabilities

    def call_tool(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.policy.validate(tool_name)
        caps = self.capabilities
        if tool_name not in caps.get("tools_enabled", []):
            return {
                "status": "error",
                "tool": tool_name,
                "error": f"tool not enabled by Vibe manifest: {tool_name}",
                "payload": {},
            }
        try:
            result = asyncio.run(self._call_tool_stdio(tool_name, payload))
        except Exception as exc:
            return {"status": "error", "tool": tool_name, "error": str(exc), "payload": payload}
        status, error = self._business_status(result)
        return {"status": status, "tool": tool_name, "error": error, "payload": result}

    async def _call_tool_stdio(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if VIBE_SITE_PACKAGES not in sys.path:
            sys.path.insert(0, VIBE_SITE_PACKAGES)
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        command = self.probe_runner._resolve_command()
        if not command:
            raise RuntimeError("Vibe MCP command is unavailable")
        params = StdioServerParameters(command=command, args=[], env={})
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as session:
                await asyncio.wait_for(session.initialize(), timeout=20)
                result = await asyncio.wait_for(session.call_tool(tool_name, payload), timeout=90)
                if hasattr(result, "model_dump"):
                    return result.model_dump(mode="json")
                if hasattr(result, "dict"):
                    return result.dict()
                return {"raw": str(result)}

    def _business_status(self, result: Dict[str, Any]) -> tuple[str, str]:
        if result.get("isError"):
            return "error", "MCP tool returned isError=true"
        texts = []
        for item in result.get("content") or []:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(str(item.get("text") or ""))
        for text in texts:
            parsed = self._parse_json_text(text)
            if isinstance(parsed, dict):
                if parsed.get("status") == "error":
                    return "error", str(parsed.get("error") or parsed)
                if parsed.get("_unresolved") and len(parsed) == 1:
                    return "error", f"unresolved symbols: {', '.join(map(str, parsed.get('_unresolved') or []))}"
        return "ok", ""

    def _parse_json_text(self, text: str) -> Any:
        try:
            return json.loads(text)
        except Exception:
            return None

    def get_market_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.call_tool("get_market_data", payload)

    def factor_analysis(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.call_tool("factor_analysis", payload)

    def pattern_recognition(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.call_tool("pattern_recognition", payload)

    def backtest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.call_tool("backtest", payload)

    def run_swarm(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.call_tool("run_swarm", payload)
