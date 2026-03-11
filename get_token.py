import urllib.request
import re
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

# 请求头（模拟真实浏览器）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}
# ===================================================

def get_token_by_http():
    """纯HTTP请求+正则匹配Token，无浏览器依赖"""
    token = None
    # 重试3次，提升成功率
    for retry in range(3):
        try:
            print(f"🔗 第{retry+1}次尝试访问页面：{TARGET_URL}")
            # 创建请求对象
            req = urllib.request.Request(TARGET_URL, headers=HEADERS)
            # 设置超时时间
            with urllib.request.urlopen(req, timeout=30) as response:
                # 读取页面源码（自动解压gzip）
                content = response.read()
                # 尝试解码
                try:
                    html = content.decode('utf-8')
                except:
                    html = content.decode('gbk', errors='ignore')
            
            print("✅ 页面源码获取成功")
            
            # 核心：正则匹配data-clipboard-text属性中的Token
            # 适配你的页面结构：id="copyToken" data-clipboard-text="16位Token"
            pattern = r'id="copyToken"[^>]*data-clipboard-text="([a-zA-Z0-9]{16})"'
            match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
            
            if match:
                token = match.group(1).strip()
                print(f"✅ 成功获取今日Token：{token}")
                return token
            else:
                # 备用正则：直接匹配data-clipboard-text属性
                pattern_backup = r'data-clipboard-text="([a-zA-Z0-9]{16})"'
                match_backup = re.search(pattern_backup, html, re.IGNORECASE | re.DOTALL)
                if match_backup:
                    token = match_backup.group(1).strip()
                    print(f"✅ 备用正则匹配到Token：{token}")
                    return token
                else:
                    print(f"⚠️ 第{retry+1}次未找到Token，重试中...")
                    time.sleep(2)  # 等待2秒重试
        
        except (HTTPError, URLError) as e:
            print(f"⚠️ 第{retry+1}次请求失败：{e}")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ 第{retry+1}次处理失败：{e}")
            time.sleep(2)
    
    # 所有重试失败，使用备用Token
    print("❌ 所有尝试均失败，使用备用Token")
    return "200c76359e543971"

def filter_subscribe(token):
    """完美适配分类格式：分类名,#genre#"""
    full_url = BASE_SUBSCRIBE_URL + token
    print(f"\n🔗 订阅地址：{full_url}")
    
    try:
        # 下载订阅文件
        req = urllib.request.Request(full_url, headers=HEADERS)
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
    print("===== 开始执行（纯HTTP稳定版）=====")
    token = get_token_by_http()
    if token:
        filter_subscribe(token)
    print("===== 执行结束 =====")
