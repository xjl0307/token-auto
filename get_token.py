import urllib.request
import re
import os
import time
from urllib.error import HTTPError, URLError

# ==================== 核心配置 =====================
TARGET_URL = "https://taoiptv.com/"
BASE_SUBSCRIBE_URL = "https://taoiptv.com/lives/50024.txt?token="
OUTPUT_FILE = "cqlt.txt"
DEBUG_HTML_FILE = "page_source.html"  # 保存页面源码用于调试

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
    """纯HTTP请求+保存源码+多正则匹配"""
    token = None
    # 重试3次
    for retry in range(3):
        try:
            print(f"🔗 第{retry+1}次尝试访问页面：{TARGET_URL}")
            req = urllib.request.Request(TARGET_URL, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                # 尝试多种编码解码
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                html = ""
                for encoding in encodings:
                    try:
                        html = content.decode(encoding)
                        print(f"✅ 使用{encoding}编码解码成功")
                        break
                    except:
                        continue
            
            # 保存页面源码到文件（用于调试）
            with open(DEBUG_HTML_FILE, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ 页面源码已保存到：{DEBUG_HTML_FILE}")
            
            # 打印源码前2000字符，快速查看结构
            print(f"\n📝 页面源码前2000字符：\n{html[:2000]}\n")
            
            # 多种正则模式匹配Token（覆盖所有可能格式）
            patterns = [
                # 模式1：id="copyToken" 包含data-clipboard-text
                r'id=["\']copyToken["\'][^>]*data-clipboard-text=["\']([^"\']+)["\']',
                # 模式2：任意位置的data-clipboard-text
                r'data-clipboard-text=["\']([a-zA-Z0-9]{16})["\']',
                # 模式3：宽松匹配16位字母数字（不限制属性）
                r'["\']([a-zA-Z0-9]{16})["\']',
                # 模式4：copyToken按钮内的所有16位字符
                r'copyToken[^>]*([a-zA-Z0-9]{16})'
            ]
            
            for i, pattern in enumerate(patterns):
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    token_candidate = match.group(1).strip()
                    # 验证Token格式（16位字母数字）
                    if len(token_candidate) == 16 and token_candidate.isalnum():
                        token = token_candidate
                        print(f"✅ 模式{i+1}匹配到Token：{token}")
                        return token
                    else:
                        print(f"⚠️ 模式{i+1}匹配到无效内容：{token_candidate}")
            
            print(f"⚠️ 第{retry+1}次未找到有效Token，重试中...")
            time.sleep(2)
        
        except (HTTPError, URLError) as e:
            print(f"⚠️ 第{retry+1}次请求失败：{e}")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ 第{retry+1}次处理失败：{e}")
            time.sleep(2)
    
    print("❌ 所有尝试均失败，使用备用Token")
    return "200c76359e543971"

def filter_subscribe(token):
    """完美适配分类格式：分类名,#genre#"""
    full_url = BASE_SUBSCRIBE_URL + token
    print(f"\n🔗 订阅地址：{full_url}")
    
    try:
        req = urllib.request.Request(full_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode('utf-8', errors='ignore')
        
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        print(f"📝 订阅文件总行数：{len(lines)}")
        
        # 筛选目标分类下的所有数据
        filtered_lines = []
        in_target_category = False
        
        for line in lines:
            if ",#genre#" in line:
                current_cate = line.replace(",#genre#", "").strip()
                if current_cate in TARGET_CATEGORIES:
                    in_target_category = True
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
        return True
    
    except Exception as e:
        print(f"❌ 处理失败：{e}")
        return False

if __name__ == "__main__":
    print("===== 开始执行（调试版）=====")
    token = get_token_by_http()
    if token:
        filter_subscribe(token)
    print("===== 执行结束 =====")
