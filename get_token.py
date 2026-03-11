import requests
from bs4 import BeautifulSoup
import urllib.request
import os
import time
from urllib.error import HTTPError, URLError

# ==================== 核心配置 =====================
TARGET_URL = "https://taoiptv.com/"
BASE_SUBSCRIBE_URL = "https://taoiptv.com/lives/50024.txt?token="
OUTPUT_FILE = "cqlt.txt"
DEBUG_FILE = "debug_info.txt"  # 调试信息文件

# 目标分类
TARGET_CATEGORIES = [
    "央视频道",
    "卫视频道",
    "西南地区"
]

# 增强版请求头（模拟真实浏览器）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="122", "Google Chrome";v="122"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"'
}

# 重试配置
RETRY_TIMES = 5
RETRY_DELAY = 3
# ===================================================

def get_token_by_bs4():
    """使用requests+BeautifulSoup精准解析页面提取Token"""
    session = requests.Session()
    session.headers.update(HEADERS)
    # 禁用SSL验证（避免GitHub Actions环境证书问题）
    session.verify = False
    
    token = None
    debug_info = []
    
    for retry in range(RETRY_TIMES):
        try:
            debug_info.append(f"\n=== 第{retry+1}次尝试 ===")
            debug_info.append(f"访问URL：{TARGET_URL}")
            
            # 发送请求（允许重定向，延长超时）
            response = session.get(
                TARGET_URL,
                timeout=30,
                allow_redirects=True,
                stream=True
            )
            debug_info.append(f"响应状态码：{response.status_code}")
            
            # 处理编码
            response.encoding = response.apparent_encoding or 'utf-8'
            html = response.text
            debug_info.append(f"页面编码：{response.encoding}")
            debug_info.append(f"页面长度：{len(html)}字符")
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html, 'html.parser')
            debug_info.append("HTML解析完成")
            
            # 多种方式查找按钮元素
            # 方式1：通过id查找
            copy_btn = soup.find(id="copyToken")
            if copy_btn:
                debug_info.append("找到id=copyToken的元素")
                # 提取data-clipboard-text属性
                token = copy_btn.get("data-clipboard-text", "").strip()
                debug_info.append(f"提取到Token：{token}")
            else:
                # 方式2：查找所有包含data-clipboard-text的按钮
                all_btns = soup.find_all(attrs={"data-clipboard-text": True})
                debug_info.append(f"找到{len(all_btns)}个带data-clipboard-text的元素")
                if all_btns:
                    # 取第一个有效Token
                    for btn in all_btns:
                        temp_token = btn.get("data-clipboard-text", "").strip()
                        if len(temp_token) == 16 and temp_token.isalnum():
                            token = temp_token
                            debug_info.append(f"从按钮提取到有效Token：{token}")
                            break
            
            # 验证Token
            if token and len(token) == 16 and token.isalnum():
                debug_info.append(f"✅ 第{retry+1}次成功获取Token：{token}")
                break
            else:
                debug_info.append(f"⚠️ 第{retry+1}次提取的Token无效：{token}")
                token = None
                time.sleep(RETRY_DELAY)
        
        except Exception as e:
            error_msg = f"⚠️ 第{retry+1}次失败：{str(e)}"
            debug_info.append(error_msg)
            print(error_msg)
            time.sleep(RETRY_DELAY)
    
    # 保存调试信息
    with open(DEBUG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(debug_info))
    print(f"✅ 调试信息已保存到：{DEBUG_FILE}")
    
    if not token:
        print("❌ 所有尝试均失败，使用备用Token")
        token = "200c76359e543971"
    else:
        print(f"✅ 成功获取今日Token：{token}")
    
    return token

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
        print(f"❌ 处理订阅失败：{e}")
        return False

if __name__ == "__main__":
    # 禁用requests警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    print("===== 开始执行（BS4解析版）=====")
    token = get_token_by_bs4()
    if token:
        filter_subscribe(token)
    print("===== 执行结束 =====")
