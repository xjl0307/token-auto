from playwright.sync_api import sync_playwright
import urllib.request
import re
import os
from urllib.error import HTTPError, URLError

# ==================== 核心配置 =====================
TARGET_URL = "https://taoiptv.com/"
BASE_SUBSCRIBE_URL = "https://taoiptv.com/lives/50024.txt?token="
OUTPUT_FILE = "cqlt.txt"

# 👇 请根据实际订阅文件中的分类名修改
TARGET_CATEGORIES = [
    "央视频道", 
    "卫视频道", 
    "西南地区"
]
# ===================================================

def get_token_by_click():
    """模拟浏览器点击获取Token"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                permissions=["clipboard-read", "clipboard-write"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            page.goto(TARGET_URL, wait_until="load", timeout=30000)
            copy_btn = page.locator("#copyToken")
            copy_btn.wait_for(timeout=10000)
            copy_btn.hover()
            copy_btn.click()
            token = page.evaluate("navigator.clipboard.readText()").strip()
            browser.close()
            
            if token and len(token) >= 16:
                print(f"✅ 获取到Token：{token}")
                return token
            else:
                raise Exception("Token无效")
    except Exception as e:
        print(f"❌ Token获取失败：{e}")
        return "200c76359e543971"  # 兜底Token

def filter_subscribe(token):
    """筛选#genre#行下的数据"""
    full_url = BASE_SUBSCRIBE_URL + token
    try:
        req = urllib.request.Request(full_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode('utf-8', errors='ignore')
        
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        filtered = []
        in_target = False
        
        for line in lines:
            if line.startswith("#genre#"):
                cate = line.replace("#genre#", "").strip()
                if cate in TARGET_CATEGORIES:
                    in_target = True
                    filtered.append(line)
                else:
                    in_target = False
            elif in_target:
                filtered.append(line)
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(filtered))
        
        print(f"✅ 筛选完成，生成文件：{OUTPUT_FILE}")
        print(f"📊 筛选后行数：{len(filtered)}")
        return True
    except Exception as e:
        print(f"❌ 订阅处理失败：{e}")
        return False

if __name__ == "__main__":
    token = get_token_by_click()
    if token:
        filter_subscribe(token)
