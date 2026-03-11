from playwright.sync_api import sync_playwright
import urllib.request
import os
from urllib.error import HTTPError, URLError

# ==================== 核心配置 =====================
TARGET_URL = "https://taoiptv.com/"
BASE_SUBSCRIBE_URL = "https://taoiptv.com/lives/50024.txt?token="
OUTPUT_FILE = "cqlt.txt"

# 👇 订阅文件中的真实分类名
TARGET_CATEGORIES = [
    "央视频道",
    "卫视频道",
    "西南地区"
]
# ===================================================

def get_token_from_attr():
    """基于你提供的JS源码：直接读取data-clipboard-text属性"""
    try:
        with sync_playwright() as p:
            # 启动浏览器（极简配置）
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            
            print(f"🔗 访问页面：{TARGET_URL}")
            # 等待DOM加载完成（和JS中的DOMContentLoaded一致）
            page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=30000)
            
            # 核心：直接读取#copyToken按钮的data-clipboard-text属性
            # 和你提供的JS代码逻辑完全一致
            token = page.locator("#copyToken").get_attribute("data-clipboard-text", timeout=15000)
            token = token.strip()
            browser.close()
            
            # 验证Token（16位字母数字）
            if token and len(token) == 16 and token.isalnum():
                print(f"✅ 成功获取今日Token：{token}")
                return token
            else:
                raise Exception(f"Token无效：{token}")
    
    except Exception as e:
        print(f"❌ Token获取失败：{e}")
        # 兜底：如果获取失败，尝试备用Token
        print("⚠️ 尝试使用备用Token")
        return "200c76359e543971"

def filter_subscribe(token):
    """完美适配分类格式：分类名,#genre#"""
    full_url = BASE_SUBSCRIBE_URL + token
    print(f"\n🔗 订阅地址：{full_url}")
    
    try:
        # 下载订阅文件
        req = urllib.request.Request(full_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode('utf-8', errors='ignore')
        
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        print(f"📝 订阅文件总行数：{len(lines)}")
        
        # 打印所有分类行
        print(f"\n🔍 订阅文件中所有分类：")
        for line in lines:
            if ",#genre#" in line:
                cate = line.replace(",#genre#", "").strip()
                print(f"   {cate}")
        
        # 筛选目标分类下的所有数据
        filtered_lines = []
        in_target_category = False
        
        for line in lines:
            # 识别分类行：格式为「分类名,#genre#」
            if ",#genre#" in line:
                current_cate = line.replace(",#genre#", "").strip()
                if current_cate in TARGET_CATEGORIES:
                    in_target_category = True
                    # 转换为标准格式：#genre# 分类名
                    filtered_lines.append(f"#genre# {current_cate}")
                    print(f"\n✅ 匹配分类：{current_cate}")
                else:
                    in_target_category = False
            elif in_target_category:
                filtered_lines.append(line)
                print(f"   提取：{line}")
        
        # 保存最终文件
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(filtered_lines))
        
        print(f"\n✅ 筛选完成！")
        print(f"📂 生成文件：{OUTPUT_FILE}")
        print(f"📊 有效行数：{len(filtered_lines)}")
        print(f"\n📋 内容预览：")
        for i, line in enumerate(filtered_lines[:20]):
            print(f"   {i+1}. {line}")
        
        return True
    
    except Exception as e:
        print(f"❌ 处理失败：{e}")
        return False

if __name__ == "__main__":
    print("===== 开始执行（完美适配JS源码版）=====")
    token = get_token_from_attr()
    if token:
        filter_subscribe(token)
    print("===== 执行结束 =====")
