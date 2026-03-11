from playwright.sync_api import sync_playwright
import urllib.request
import os
import time
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

def get_token_by_click_optimized():
    """增强版模拟点击：多重等待+容错"""
    try:
        with sync_playwright() as p:
            # 启动浏览器（优化配置）
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",  # 隐藏自动化特征
                    "--disable-gpu"
                ]
            )
            context = browser.new_context(
                permissions=["clipboard-read", "clipboard-write"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            
            print(f"🔗 正在访问页面：{TARGET_URL}")
            # 优化1：等待页面完全加载（网络空闲+DOM加载完成）
            page.goto(
                TARGET_URL, 
                wait_until="networkidle",  # 等待网络空闲
                timeout=60000  # 延长超时到60秒
            )
            print("✅ 页面加载完成")
            
            # 优化2：多种方式定位按钮（按优先级尝试）
            copy_btn = None
            # 方式1：通过id定位
            try:
                copy_btn = page.locator("#copyToken")
                copy_btn.wait_for(state="attached", timeout=30000)  # 等待元素出现在DOM中
                print("✅ 通过id定位到按钮")
            except:
                print("⚠️ id定位失败，尝试文本定位")
                # 方式2：通过文本“获取Token”定位
                try:
                    copy_btn = page.get_by_text("获取Token", exact=True)
                    copy_btn.wait_for(state="attached", timeout=30000)
                    print("✅ 通过文本定位到按钮")
                except:
                    print("⚠️ 文本定位失败，尝试CSS选择器")
                    # 方式3：通过CSS选择器定位
                    try:
                        copy_btn = page.locator("[data-clipboard-text]")
                        copy_btn.first.wait_for(state="attached", timeout=30000)
                        print("✅ 通过CSS选择器定位到按钮")
                    except:
                        raise Exception("所有定位方式均失败")
            
            # 优化3：模拟真实操作（滚动到可见+悬浮+点击）
            copy_btn.scroll_into_view_if_needed()
            time.sleep(1)  # 短暂等待
            copy_btn.hover()
            print("✅ 鼠标悬浮成功")
            time.sleep(0.5)
            copy_btn.click()
            print("✅ 点击按钮成功")
            
            # 优化4：等待剪贴板写入
            time.sleep(1)
            
            # 读取剪贴板
            token = page.evaluate("navigator.clipboard.readText()").strip()
            browser.close()
            
            # 验证Token
            if token and len(token) == 16 and token.isalnum():
                print(f"✅ 成功获取今日Token：{token}")
                return token
            else:
                raise Exception(f"Token无效：{token}")
    
    except Exception as e:
        print(f"❌ Token获取失败：{e}")
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
    print("===== 开始执行（增强模拟点击版）=====")
    token = get_token_by_click_optimized()
    if token:
        filter_subscribe(token)
    print("===== 执行结束 =====")
