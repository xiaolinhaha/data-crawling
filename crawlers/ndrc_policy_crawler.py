#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
国家发改委政策解读爬虫
"""

import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Blueprint

# 创建蓝图
ndrc_policy_bp = Blueprint('ndrc_policy', __name__)

class NDRCPolicyCrawler:
    """
    国家发改委政策解读爬虫类
    """
    
    def __init__(self):
        """
        初始化
        """
        self.name = "国家发改委政策解读"
        self.base_url = "https://www.ndrc.gov.cn/xxgk/jd/jd/"
        
        # 设置请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Referer': 'https://www.ndrc.gov.cn/',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        # 初始化Cookies
        self.cookies = {}
    
    def get_todays_news(self):
        """获取当天的政策解读新闻"""
        try:
            # 发送请求获取页面内容
            response = requests.get(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                timeout=10
            )
            
            # 设置正确的编码
            response.encoding = 'utf-8'
            
            # 检查响应状态
            if response.status_code != 200:
                return []
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找符合要求的新闻列表
            news_list = soup.select('.list .u-list li')
            
            if not news_list:
                return []
            
            # 获取今天的日期
            today = datetime.now().strftime('%Y/%m/%d')
            
            # 提取当天的新闻
            today_news = []
            for news in news_list:
                # 提取时间
                date_span = news.select_one('span')
                if not date_span:
                    continue
                
                news_date = date_span.text.strip()
                
                # 判断是否是当天的新闻
                if news_date == today:
                    # 提取标题和链接
                    news_link = news.select_one('a')
                    if not news_link:
                        continue
                    
                    title = news_link.text.strip()
                    url = news_link.get('href', '')
                    
                    # 处理相对URL
                    if url.startswith('./'):
                        url = 'https://www.ndrc.gov.cn/xxgk/jd/jd/' + url[2:]
                    elif url.startswith('/'):
                        url = 'https://www.ndrc.gov.cn' + url
                    
                    # 添加到结果列表
                    today_news.append({
                        'title': title,
                        'url': url,
                        'date': news_date
                    })
            
            return today_news
            
        except Exception as e:
            return []
    
    def get_article_detail(self, url):
        """获取文章详细内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # 设置正确的编码
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return None
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章内容
            content = ""
            # 尝试不同的选择器，因为政府网站结构可能有所不同
            article_content = soup.select('.TRS_Editor p, .Zoom p, .content p, .article-content p')
            
            if article_content:
                for p in article_content:
                    text = p.get_text(strip=True)
                    if text:
                        content += text + "\n\n"
            
            # 如果没有找到内容，尝试获取主要div内容
            if not content:
                main_content = soup.select_one('.TRS_Editor, .Zoom, .content, .article-content')
                if main_content:
                    content = main_content.get_text(strip=True)
            
            return content.strip()
            
        except Exception as e:
            return None
    
    def crawl(self):
        """爬取文章主函数"""
        try:
            # 获取当天最新文章
            latest_articles = self.get_todays_news()
            if not latest_articles:
                return {
                    "status": "success",
                    "message": "当天没有新的政策解读文章",
                    "data": []
                }
            
            # 获取文章详情
            results = []
            for article in latest_articles:
                article_url = article.get('url')
                article_content = self.get_article_detail(article_url)
                
                # 整合信息
                result = {
                    'title': article.get('title', ''),
                    'url': article_url,
                    'date': article.get('date', ''),
                    'source': '国家发改委',
                    'content': article_content or ''
                }
                results.append(result)
            
            return {
                "status": "success",
                "message": "成功获取国家发改委当天最新政策解读文章",
                "data": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": []
            }

@ndrc_policy_bp.route('/ndrc_policy_news', methods=['GET'])
def get_ndrc_policy_news():
    """获取国家发改委政策解读最新文章接口"""
    try:
        crawler = NDRCPolicyCrawler()
        result = crawler.crawl()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

# 测试代码
if __name__ == "__main__":
    crawler = NDRCPolicyCrawler()
    result = crawler.crawl()
    print(json.dumps(result, ensure_ascii=False, indent=2)) 