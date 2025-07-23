#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
环球网国际新闻爬虫
"""

import requests
import json
import re
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from flask import Blueprint

# 创建蓝图
huanqiu_world_bp = Blueprint('huanqiu_world', __name__)

class HuanqiuWorldCrawler:
    """
    环球网国际新闻爬虫类
    """
    
    def __init__(self):
        """
        初始化
        """
        self.name = "环球网国际新闻"
        self.base_url = "https://world.huanqiu.com/roll"
        self.api_url = "https://world.huanqiu.com/api/list2"
        
        # 设置请求头
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://world.huanqiu.com/roll',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'x-requested-with': 'XMLHttpRequest'
        }
        
        # 初始化Cookies
        self.cookies = {}
    
    def is_within_24_hours(self, timestamp):
        """判断时间戳是否在过去24小时内"""
        if not timestamp:
            return False
        try:
            # 将毫秒时间戳转换为datetime对象
            article_time = datetime.fromtimestamp(int(timestamp) / 1000)
            
            # 计算24小时前的时间
            time_24h_ago = datetime.now() - timedelta(hours=24)
            
            # 判断文章时间是否在过去24小时内
            return article_time >= time_24h_ago
        except:
            return False
    
    def get_latest_news(self):
        """获取过去24小时内的最新两条新闻"""
        try:
            # 设置请求参数 - 增加数量以提高找到符合条件文章的概率
            params = {
                'node': '/e3pmh22ph/e3pmh2398',
                'offset': '0',
                'limit': '30'
            }
            
            # 发送请求
            response = requests.get(
                self.api_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code != 200:
                return []
            
            # 解析响应
            data = response.json()
            
            # 获取新闻列表
            news_list = data.get('list', [])
            if not news_list:
                return []
            
            # 筛选过去24小时内的新闻
            recent_news = []
            for news in news_list:
                ctime = news.get('ctime', 0)
                if self.is_within_24_hours(ctime):
                    recent_news.append(news)
            
            if not recent_news:
                return []
            
            # 最多返回两条新闻
            result_news = recent_news[:min(2, len(recent_news))]
            
            # 提取新闻信息
            articles_data = []
            for news in result_news:
                article_data = {
                    'aid': news.get('aid', ''),
                    'title': news.get('title', ''),
                    'summary': news.get('summary', ''),
                    'date': self.format_timestamp(news.get('ctime', '')),
                    'source': news.get('source', {}).get('name', ''),
                    'source_url': news.get('source', {}).get('url', ''),
                    'url': f"https://world.huanqiu.com/article/{news.get('aid', '')}"
                }
                articles_data.append(article_data)
            
            return articles_data
            
        except Exception as e:
            return []
    
    def format_timestamp(self, timestamp):
        """格式化时间戳为日期字符串"""
        if not timestamp:
            return ""
        try:
            dt = datetime.fromtimestamp(int(timestamp) / 1000)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return ""
    
    def get_article_detail(self, url):
        """获取文章详细内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章内容
            content = ""
            article_content = soup.select('.article-content p')
            
            if article_content:
                for p in article_content:
                    text = p.get_text(strip=True)
                    if text:
                        content += text + "\n\n"
            
            # 如果没有找到内容，尝试其他选择器
            if not content:
                article_content = soup.select('article p')
                if article_content:
                    for p in article_content:
                        text = p.get_text(strip=True)
                        if text:
                            content += text + "\n\n"
            
            # 如果仍然没有找到内容，尝试从页面源码中提取
            if not content:
                content_match = re.search(r'<textarea class="article-content">(.*?)</textarea>', response.text, re.DOTALL)
                if content_match:
                    html_content = content_match.group(1)
                    soup_content = BeautifulSoup(html_content, 'html.parser')
                    paragraphs = soup_content.find_all('p')
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text:
                            content += text + "\n\n"
            
            return content.strip()
            
        except Exception as e:
            return None
    
    def crawl(self):
        """爬取文章主函数"""
        try:
            # 计算时间范围用于显示
            now = datetime.now()
            time_24h_ago = now - timedelta(hours=24)
            time_range = f"{time_24h_ago.strftime('%Y-%m-%d %H:%M')} 至 {now.strftime('%Y-%m-%d %H:%M')}"
            
            # 获取过去24小时内最新文章
            latest_articles = self.get_latest_news()
            if not latest_articles:
                return {
                    "status": "success",
                    "message": f"在时间范围（{time_range}）内没有国际新闻",
                    "data": [],
                    "time_range": time_range
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
                    'source': article.get('source', ''),
                    'summary': article.get('summary', ''),
                    'content': article_content or article.get('summary', '')
                }
                results.append(result)
            
            return {
                "status": "success",
                "message": f"成功获取在时间范围（{time_range}）内的环球网国际新闻最新文章",
                "data": results,
                "time_range": time_range
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": []
            }

@huanqiu_world_bp.route('/huanqiu_world_news', methods=['GET'])
def get_huanqiu_world_news():
    """获取环球网国际新闻过去24小时内的最新文章接口"""
    try:
        crawler = HuanqiuWorldCrawler()
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
    crawler = HuanqiuWorldCrawler()
    result = crawler.crawl()
    print(json.dumps(result, ensure_ascii=False, indent=2)) 