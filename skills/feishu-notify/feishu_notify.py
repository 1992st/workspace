#!/usr/bin/env python3
"""
Win_Stock Feishu notification client.

This script is intentionally usable from cron prompts:
  python3 skills/feishu-notify/feishu_notify.py send-report --path reviews/daily/...
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


DEFAULT_CHAT_ID = "oc_f403ab69c2c499a1aaa16066241842fb"
DEFAULT_CHUNK_LIMIT = 3500
DEFAULT_FILE_THRESHOLD = 3
DEFAULT_ENV_FILES = [
    Path("config/.env"),
    Path.home() / ".openclaw" / "workspace" / ".env",
    Path.home() / ".openclaw" / "workspace" / "skills" / "feishu" / ".env",
]


class FeishuConfigError(RuntimeError):
    """Raised when required Feishu credentials are missing."""


class FeishuNotifier:
    def __init__(
        self,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        chat_id: Optional[str] = None,
        chunk_limit: int = DEFAULT_CHUNK_LIMIT,
        env_file: Optional[Path] = None,
    ):
        load_env_files(env_file)
        self.app_id = app_id or os.getenv("FEISHU_APP_ID")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")
        self.chat_id = chat_id or os.getenv("FEISHU_CHAT_ID") or DEFAULT_CHAT_ID
        self.chunk_limit = chunk_limit
        self.base_url = "https://open.feishu.cn/open-apis"
        self._token: Optional[str] = None

    def validate_config(self) -> None:
        missing = []
        if not self.app_id:
            missing.append("FEISHU_APP_ID")
        if not self.app_secret:
            missing.append("FEISHU_APP_SECRET")
        if not self.chat_id:
            missing.append("FEISHU_CHAT_ID")
        if missing:
            raise FeishuConfigError(
                "Missing Feishu configuration: " + ", ".join(missing)
            )

    def _get_token(self) -> str:
        self.validate_config()
        if self._token:
            return self._token

        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        resp = requests.post(
            url,
            json={"app_id": self.app_id, "app_secret": self.app_secret},
            timeout=20,
        )
        data = resp.json()
        token = data.get("tenant_access_token")
        if not token:
            raise RuntimeError(f"Failed to get Feishu token: {data}")
        self._token = token
        return token

    def _post_message(self, msg_type: str, content: Dict[str, Any], chat_id: Optional[str]) -> Dict[str, Any]:
        token = self._get_token()
        target = chat_id or self.chat_id
        url = f"{self.base_url}/im/v1/messages?receive_id_type=chat_id"
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": target,
                "msg_type": msg_type,
                "content": json.dumps(content, ensure_ascii=False),
            },
            timeout=20,
        )
        try:
            return resp.json()
        except ValueError:
            return {"code": resp.status_code, "msg": resp.text}

    def send_text(self, text: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
        return self._post_message("text", {"text": text}, chat_id)

    def upload_file(self, file_path: Path, file_type: str = "stream") -> Dict[str, Any]:
        token = self._get_token()
        file_path = file_path.resolve()
        url = f"{self.base_url}/im/v1/files"
        with file_path.open("rb") as file_obj:
            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                data={"file_type": file_type, "file_name": file_path.name},
                files={"file": (file_path.name, file_obj, "text/markdown")},
                timeout=60,
            )
        try:
            return resp.json()
        except ValueError:
            return {"code": resp.status_code, "msg": resp.text}

    def send_file(self, file_key: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
        return self._post_message("file", {"file_key": file_key}, chat_id)

    def send_card(
        self,
        title: str,
        content: str,
        buttons: Optional[List[Dict[str, str]]] = None,
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        elements: List[Dict[str, Any]] = [
            {"tag": "div", "text": {"tag": "plain_text", "content": content}}
        ]
        if buttons:
            elements.append(
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": btn["text"]},
                            "type": "primary",
                            "url": btn.get("url", ""),
                        }
                        for btn in buttons
                    ],
                }
            )

        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "blue",
            },
            "elements": elements,
        }
        return self._post_message("interactive", card, chat_id)

    def split_text(self, text: str) -> List[str]:
        return split_text(text, self.chunk_limit)

    def send_report(
        self,
        report_path: Path,
        title: str,
        chat_id: Optional[str] = None,
        dry_run: bool = False,
        file_threshold: int = DEFAULT_FILE_THRESHOLD,
    ) -> Dict[str, Any]:
        report_path = report_path.resolve()
        text = report_path.read_text(encoding="utf-8")
        chunks = self.split_text(text)
        result: Dict[str, Any] = {
            "success": False,
            "dry_run": dry_run,
            "title": title,
            "report_path": str(report_path),
            "chat_id": chat_id or self.chat_id,
            "chunk_count": len(chunks),
            "sent_at": datetime.now().isoformat(timespec="seconds"),
            "delivery_mode": "file" if len(chunks) > file_threshold else "chunks",
            "responses": [],
            "error": None,
        }

        try:
            if dry_run:
                result["success"] = True
                if result["delivery_mode"] == "file":
                    result["responses"].append({"dry_run": True, "step": "card"})
                    result["responses"].append({"dry_run": True, "step": "upload_file", "path": str(report_path)})
                    result["responses"].append({"dry_run": True, "step": "send_file"})
                    result["responses"].append({"dry_run": True, "step": "path"})
                else:
                    result["responses"].append({"dry_run": True, "step": "card"})
                    result["responses"].extend(
                        {"dry_run": True, "step": "chunk", "index": idx + 1, "length": len(chunk)}
                        for idx, chunk in enumerate(chunks)
                    )
                    result["responses"].append({"dry_run": True, "step": "path"})
                return result

            self.validate_config()
            if result["delivery_mode"] == "file":
                result["responses"].append(
                    self.send_card(
                        title=title,
                        content=f"完整报告较长（按文本需 {len(chunks)} 段），已改为文件发送。\n{report_path}",
                        chat_id=chat_id,
                    )
                )
                upload_resp = self.upload_file(report_path)
                result["responses"].append(upload_resp)
                file_key = upload_resp.get("data", {}).get("file_key")
                if not file_key:
                    raise RuntimeError(f"Feishu file upload did not return file_key: {upload_resp}")
                result["file_key"] = file_key
                result["responses"].append(self.send_file(file_key, chat_id=chat_id))
                result["responses"].append(self.send_text(f"完整报告路径:\n{report_path}", chat_id=chat_id))
            else:
                result["responses"].append(
                    self.send_card(
                        title=title,
                        content=f"完整报告开始发送，共 {len(chunks)} 段。\n{report_path}",
                        chat_id=chat_id,
                    )
                )
                for idx, chunk in enumerate(chunks, start=1):
                    prefix = f"【{title}】第 {idx}/{len(chunks)} 段\n\n"
                    result["responses"].append(self.send_text(prefix + chunk, chat_id=chat_id))
                result["responses"].append(
                    self.send_text(f"完整报告路径:\n{report_path}", chat_id=chat_id)
                )
            result["success"] = all(is_success_response(resp) for resp in result["responses"])
            if not result["success"]:
                result["error"] = "At least one Feishu message returned a non-success response."
            return result
        except Exception as exc:  # The caller needs a delivery json even on failure.
            result["error"] = str(exc)
            return result


def is_success_response(resp: Dict[str, Any]) -> bool:
    return resp.get("code") in (0, None) and not resp.get("error")


def split_text(text: str, limit: int = DEFAULT_CHUNK_LIMIT) -> List[str]:
    if limit < 500:
        raise ValueError("chunk limit must be at least 500 characters")
    chunks: List[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(line) > limit:
            if current:
                chunks.append(current.rstrip())
                current = ""
            for start in range(0, len(line), limit):
                chunks.append(line[start : start + limit].rstrip())
            continue
        if len(current) + len(line) > limit:
            chunks.append(current.rstrip())
            current = line
        else:
            current += line
    if current.strip():
        chunks.append(current.rstrip())
    return chunks or [""]


def load_env_files(explicit_env_file: Optional[Path] = None) -> None:
    paths = []
    if explicit_env_file:
        paths.append(explicit_env_file)
    paths.extend(DEFAULT_ENV_FILES)

    for path in paths:
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def delivery_path_for(report_path: Path) -> Path:
    return report_path.with_suffix(".delivery.json")


def write_delivery(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send Win_Stock reports to Feishu.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    text_parser = subparsers.add_parser("send-text")
    text_parser.add_argument("text")
    text_parser.add_argument("--chat-id")
    text_parser.add_argument("--env-file", type=Path)
    text_parser.add_argument("--dry-run", action="store_true")

    card_parser = subparsers.add_parser("send-card")
    card_parser.add_argument("--title", required=True)
    card_parser.add_argument("--content", required=True)
    card_parser.add_argument("--chat-id")
    card_parser.add_argument("--env-file", type=Path)
    card_parser.add_argument("--dry-run", action="store_true")

    report_parser = subparsers.add_parser("send-report")
    report_parser.add_argument("--path", required=True)
    report_parser.add_argument("--title", required=True)
    report_parser.add_argument("--chat-id")
    report_parser.add_argument("--env-file", type=Path)
    report_parser.add_argument("--chunk-limit", type=int, default=DEFAULT_CHUNK_LIMIT)
    report_parser.add_argument("--file-threshold", type=int, default=DEFAULT_FILE_THRESHOLD)
    report_parser.add_argument("--dry-run", action="store_true")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.command == "send-text":
        notifier = FeishuNotifier(chat_id=args.chat_id, env_file=args.env_file)
        if args.dry_run:
            print(json.dumps({"success": True, "dry_run": True, "text": args.text}, ensure_ascii=False, indent=2))
            return 0
        result = notifier.send_text(args.text, chat_id=args.chat_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if is_success_response(result) else 1

    if args.command == "send-card":
        notifier = FeishuNotifier(chat_id=args.chat_id, env_file=args.env_file)
        if args.dry_run:
            print(
                json.dumps(
                    {"success": True, "dry_run": True, "title": args.title, "content": args.content},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        result = notifier.send_card(args.title, args.content, chat_id=args.chat_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if is_success_response(result) else 1

    if args.command == "send-report":
        report_path = Path(args.path)
        notifier = FeishuNotifier(chat_id=args.chat_id, chunk_limit=args.chunk_limit, env_file=args.env_file)
        result = notifier.send_report(
            report_path=report_path,
            title=args.title,
            chat_id=args.chat_id,
            dry_run=args.dry_run,
            file_threshold=args.file_threshold,
        )
        if not args.dry_run:
            write_delivery(delivery_path_for(report_path), result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("success") else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
