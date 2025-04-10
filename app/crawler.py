import requests
from bs4 import BeautifulSoup
import random
import logging

def get_baidu_slogan():
    """
    爬取百度首页的一条文案
    返回：随机一条文案字符串，如果爬取失败则返回错误信息
    """
    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 发送GET请求到百度首页
        response = requests.get('https://www.baidu.com', headers=headers, timeout=5)
        response.raise_for_status()  # 如果请求不成功则抛出异常
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 尝试提取百度首页的标语或推荐文案
        # 以下选择器可能需要根据百度页面的实际结构调整
        slogans = []
        
        # 尝试获取百度首页底部的热搜词
        hot_words = soup.select('.hotsearch-item')
        if hot_words:
            for item in hot_words:
                text = item.get_text().strip()
                if text:
                    slogans.append(text)
        
        # 尝试获取百度首页底部的文案
        footer_texts = soup.select('.s-bottom-layer-content a')
        if footer_texts:
            for item in footer_texts:
                text = item.get_text().strip()
                if text:
                    slogans.append(text)
        
        # 如果找不到任何文案，尝试获取其他元素
        if not slogans:
            various_texts = soup.find_all(['a', 'span', 'div'], limit=20)
            for item in various_texts:
                text = item.get_text().strip()
                if text and len(text) > 5 and len(text) < 50:  # 筛选合适长度的文本
                    slogans.append(text)
        
        # 如果有多个文案，随机选择一个返回
        if slogans:
            return random.choice(slogans)
        else:
            return "未能在百度首页找到合适的文案"
            
    except requests.exceptions.RequestException as e:
        logging.error(f"请求百度首页时出错: {str(e)}")
        return f"爬取失败: {str(e)}"
    except Exception as e:
        logging.error(f"解析百度首页时出错: {str(e)}")
        return f"解析失败: {str(e)}" 