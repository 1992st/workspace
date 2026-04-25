#!/usr/bin/env python3
"""
生成小红书配图脚本 - 系列第1期
需要安装: pip install playwright
安装浏览器: playwright install chromium
"""

from playwright.sync_api import sync_playwright
import os

def generate_xiaohongshu_cover():
    html_path = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-16-001-claude-secret-experiments/xiaohongshu-series-1-cover.html"
    output_path = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-16-001-claude-secret-experiments/xiaohongshu-series-1-cover.png"
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 1200})
        page.goto(f"file://{html_path}")
        page.wait_for_timeout(1500)  # 等待动画渲染
        page.screenshot(path=output_path, full_page=True)
        browser.close()
        
        print(f"✅ 小红书配图已生成: {output_path}")
        print(f"尺寸: 900x1200 (3:4 小红书标准)")
        print(f"主题: Claude 五大实验功能 + BUDDY 重点")

if __name__ == "__main__":
    generate_xiaohongshu_cover()
