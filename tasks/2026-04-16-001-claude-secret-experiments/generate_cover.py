#!/usr/bin/env python3
"""
生成小红书配图脚本
需要安装: pip install playwright
安装浏览器: playwright install chromium
"""

from playwright.sync_api import sync_playwright
import os

def generate_xiaohongshu_cover():
    html_path = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-16-001-claude-secret-experiments/xiaohongshu-cover.html"
    output_path = "/Volumes/zhangstExtern/openclaw/workspace/agent-radar-desk/tasks/2026-04-16-001-claude-secret-experiments/xiaohongshu-cover.png"
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 900, "height": 1200})
        
        # 加载 HTML 文件
        page.goto(f"file://{html_path}")
        
        # 等待渲染完成
        page.wait_for_timeout(1000)
        
        # 截图
        page.screenshot(path=output_path, full_page=True)
        
        browser.close()
        
        print(f"✅ 配图已生成: {output_path}")
        print(f"尺寸: 900x1200 (3:4 小红书标准)")

if __name__ == "__main__":
    generate_xiaohongshu_cover()
