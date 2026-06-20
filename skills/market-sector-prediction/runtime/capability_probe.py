from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

from tool_whitelist import ToolPolicy


CN_TZ = timezone(timedelta(hours=8))
KNOWN_VIBE_COMMANDS = [
    "/Volumes/zhangstExtern/openclaw/runtime/vibe-trading/vibe-trading-mcp-wrapper.sh",
    "/Volumes/zhangstExtern/openclaw/runtime/vibe-trading-venv/bin/vibe-trading-mcp",
]
VIBE_SITE_PACKAGES = "/Volumes/zhangstExtern/openclaw/runtime/vibe-trading-venv/lib/python3.14/site-packages"


class CapabilityProbe:
    """Probe the real Vibe-Trading MCP surface without assuming tool names."""

    def __init__(self, command: str = "vibe-trading-mcp", policy: ToolPolicy | None = None) -> None:
        env_command = os.environ.get("WIN_STOCK_VIBE_MCP_COMMAND") or os.environ.get("VIBE_MCP_COMMAND")
        self.command = env_command or command
        self._explicit_command = bool(env_command) or command != "vibe-trading-mcp"
        self.policy = policy or ToolPolicy.default()

    def probe(self) -> Dict[str, Any]:
        env_manifest = os.environ.get("WIN_STOCK_VIBE_TOOL_MANIFEST")
        if env_manifest:
            detected = self._parse_manifest(env_manifest)
            return self._build(True, "env-manifest", detected, [])

        command_path = self._resolve_command()
        if not command_path:
            return self._build(False, "", [], [f"{self.command} not found on PATH"])

        errors: List[str] = []
        detected, mcp_error = self._probe_mcp_tools(command_path)
        if detected:
            return self._build(True, "mcp-stdio", detected, errors)
        if mcp_error:
            errors.append(f"mcp list_tools: {mcp_error}")

        detected: List[str] = []
        for args in (["--tools-json"], ["list-tools"], ["--help"]):
            try:
                result = subprocess.run(
                    [command_path, *args],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
            except Exception as exc:
                errors.append(f"{' '.join(args)}: {exc}")
                continue
            text = f"{result.stdout}\n{result.stderr}".strip()
            parsed = self._parse_manifest(text)
            if parsed:
                detected = parsed
                break
            if result.returncode != 0:
                errors.append(f"{' '.join(args)} exit={result.returncode}")

        if not detected:
            return self._build(
                True,
                "installed-but-manifest-unavailable",
                [],
                errors + ["tool manifest unavailable; prediction tools disabled"],
            )
        return self._build(True, "detected", detected, errors)

    def _probe_mcp_tools(self, command_path: str) -> tuple[List[str], str]:
        if VIBE_SITE_PACKAGES not in sys.path and Path(VIBE_SITE_PACKAGES).exists():
            sys.path.insert(0, VIBE_SITE_PACKAGES)
        try:
            import asyncio

            from mcp.client.session import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client
        except Exception as exc:
            return [], f"mcp client unavailable: {exc}"

        async def list_tools() -> List[str]:
            params = StdioServerParameters(command=command_path, args=[], env={})
            async with stdio_client(params) as streams:
                async with ClientSession(*streams) as session:
                    await asyncio.wait_for(session.initialize(), timeout=20)
                    listed = await asyncio.wait_for(session.list_tools(), timeout=20)
                    return sorted({tool.name for tool in listed.tools if getattr(tool, "name", None)})

        try:
            return asyncio.run(list_tools()), ""
        except Exception as exc:
            return [], str(exc)

    def _resolve_command(self) -> str:
        if Path(self.command).exists():
            return self.command
        command_path = shutil.which(self.command)
        if command_path:
            return command_path
        if self._explicit_command:
            return ""
        for candidate in KNOWN_VIBE_COMMANDS:
            if Path(candidate).exists():
                return candidate
        return ""

    def _parse_manifest(self, text: str) -> List[str]:
        try:
            payload = json.loads(text)
        except Exception:
            payload = None
        if isinstance(payload, dict):
            tools = payload.get("tools") or payload.get("tools_detected") or payload.get("available_tools")
            if isinstance(tools, list):
                names = []
                for item in tools:
                    if isinstance(item, str):
                        names.append(item)
                    elif isinstance(item, dict) and item.get("name"):
                        names.append(str(item["name"]))
                return sorted(set(names))
        found = [tool for tool in self.policy.allowed_tools if tool in text]
        return sorted(set(found))

    def _build(self, available: bool, version: str, detected: List[str], missing: List[str]) -> Dict[str, Any]:
        enabled = self.policy.enabled_from_manifest(detected)
        disabled = self.policy.disabled_from_manifest(detected) if detected else sorted(self.policy.allowed_tools)
        standard = available and "get_market_data" in enabled and "factor_analysis" in enabled
        deep = standard and "run_swarm" in enabled and "get_run_result" in enabled and bool(
            os.environ.get("VIBE_LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        )
        return {
            "vibe_available": available,
            "vibe_version": version,
            "tools_detected": detected,
            "tools_enabled": enabled,
            "tools_disabled": disabled,
            "modes_available": {"standard": standard, "deep": deep},
            "missing_requirements": missing,
            "checked_at": datetime.now(CN_TZ).isoformat(timespec="seconds"),
        }
