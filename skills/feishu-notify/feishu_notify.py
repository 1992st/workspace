#!/usr/bin/env python3
"""
Win_Stock 飞书通知客户端
支持文本、卡片、紧急消息发送
"""

import os
import json
import requests
from typing import Optional, List, Dict

class FeishuNotifier:
    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None, 
                 chat_id: Optional[str] = None):
        self.app_id = app_id or os.getenv("FEISHU_APP_ID")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET")
        self.chat_id = chat_id or os.getenv("FEISHU_CHAT_ID") or "oc_f403ab69c2c499a1aaa16066241842fb"
        self.base_url = "https://open.feishu.cn/open-apis"
        self._token = None
    
    def _get_token(self) -> str:
        """获取 tenant_access_token"""
        if self._token:
            return self._token
        
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret
        })
        data = resp.json()
        self._token = data.get("tenant_access_token")
        return self._token
    
    def send_text(self, text: str, chat_id: Optional[str] = None) -> Dict:
        """发送文本消息"""
        token = self._get_token()
        target = chat_id or self.chat_id
        
        url = f"{self.base_url}/im/v1/messages?receive_id_type=chat_id"
        resp = requests.post(url, headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "receive_id": target,
            "msg_type": "text",
            "content": json.dumps({"text": text})
        })
        return resp.json()
    
    def send_card(self, title: str, content: str, 
                  buttons: Optional[List[Dict]] = None,
                  chat_id: Optional[str] = None) -> Dict:
        """发送卡片消息"""
        token = self._get_token()
        target = chat_id or self.chat_id
        
        elements = [
            {"tag": "div", "text": {"tag": "plain_text", "content": content}}
        ]
        
        if buttons:
            actions = []
            for btn in buttons:
                actions.append({
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": btn["text"]},
                    "type": "primary",
                    "url": btn.get("url", "")
                })
            elements.append({"tag": "action", "actions": actions})
        
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": title},
                "template": "blue"
            },
            "elements": elements
        }
        
        url = f"{self.base_url}/im/v1/messages?receive_id_type=chat_id"
        resp = requests.post(url, headers={
            "Authorization": f"Bearer {token}"
        }, json={
            "receive_id": target,
            "msg_type": "interactive",
            "content": json.dumps(card)
        })
        return resp.json()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        notifier = FeishuNotifier()
        result = notifier.send_text(sys.argv[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))
