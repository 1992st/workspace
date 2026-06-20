#!/usr/bin/env python3
"""
三本书一键下载脚本
在你的本地电脑上运行（需要能访问 z-lib.fm）

用法: python3 download_books.py
"""

import urllib.request
import ssl
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = False

DST = os.path.expanduser("~/Downloads/investing_books")
os.makedirs(DST, exist_ok=True)

BOOKS = [
    {
        "title": "Trading and Exchanges",
        "author": "Larry Harris",
        "isbn": "978-0195144703",
        "zlib_search": "https://z-lib.fm/s/Trading+and+Exchanges+Larry+Harris",
        "filename": "Trading_and_Exchanges_Larry_Harris.pdf",
    },
    {
        "title": "Evidence-Based Technical Analysis",
        "author": "David Aronson",
        "isbn": "978-0470008744",
        "zlib_search": "https://z-lib.fm/s/Evidence+Based+Technical+Analysis+David+Aronson",
        "filename": "Evidence_Based_Technical_Analysis_David_Aronson.pdf",
    },
    {
        "title": "The Art of Execution",
        "author": "Lee Freeman-Shor",
        "isbn": "978-0857191854",
        "zlib_search": "https://z-lib.fm/s/The+Art+of+Execution+Lee+Freeman-Shor",
        "filename": "The_Art_of_Execution_Lee_Freeman-Shor.pdf",
    },
]

def download(url, filepath, timeout=120):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        data = resp.read()
        sig = data[:4]
        if sig == b'%PDF':
            with open(filepath, 'wb') as f:
                f.write(data)
            return f"✅ PDF {len(data)/(1024*1024):.1f}MB"
        elif sig == b'PK\x03\x04':
            with open(filepath, 'wb') as f:
                f.write(data)
            return f"✅ EPUB {len(data)/(1024*1024):.1f}MB"
        elif data[:100].lower().startswith(b'<!doctype') or b'<html' in data[:100].lower():
            return f"⚠️  返回了网页（需手动从浏览器下载）"
        else:
            return f"❓ 未知格式: {data[:20]}"
    except Exception as e:
        return f"❌ {e}"

if __name__ == "__main__":
    print("=" * 60)
    print("三本投资经典一键下载")
    print("=" * 60)
    
    for i, book in enumerate(BOOKS, 1):
        print(f"\n📚 [{i}/3] {book['title']}")
        print(f"   作者: {book['author']}")
        print(f"   ISBN: {book['isbn']}")
        print(f"   🔗 浏览器打开: {book['zlib_search']}")
        print(f"   (如果自动下载失败，请用上面的链接手动下载)")
        
        # Note: Auto-download from Z-Lib requires knowing the /dl/ link
        # which requires parsing the search results page first.
        # This script gives you the direct search link.
    
    print(f"\n{'=' * 60}")
    print(f"📁 书籍保存目录: {DST}")
    print(f"{'=' * 60}")
    print(f"\n手动下载步骤:")
    print(f"1. 浏览器打开上面的 🔗 链接")
    print(f"2. 点击书名进入详情页")
    print(f"3. 点击下载按钮（PDF 或 EPUB）")
    print(f"4. 保存到 {DST}")
    print(f"\n或者直接在 Z-Lib 搜索框搜 ISBN 即可。")
