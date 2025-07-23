#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
东方财富网国际经济栏目爬虫
"""

import requests
import json
import re
import time
from bs4 import BeautifulSoup
from flask import Blueprint
from datetime import datetime

# 创建蓝图
eastmoney_international_bp = Blueprint('eastmoney_international', __name__)

class EastmoneyInternationalCrawler:
    """
    东方财富网国际经济栏目爬虫
    """
    
    def __init__(self):
        """
        初始化
        """
        self.name = "东方财富网国际经济"
        self.base_url = "https://finance.eastmoney.com/a/cgjjj.html"
        self.api_url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
        
        # 设置请求头
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://finance.eastmoney.com/a/cgjjj.html',
            'Sec-Fetch-Dest': 'script',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        # 设置Cookies
        self.cookies = {
            'qgqp_b_id': '7a333970f6cb928e27b8199386fff877',
            'st_pvi': '93729199449690',
            'st_sp': '2025-04-10%2012%3A51%3A52',
            'st_inirUrl': 'https%3A%2F%2Ffinance.eastmoney.com%2Fpinglun.html',
            'st_sn': '65',
            'st_psi': '20250411175254489-118000300908-0349576056'
        }
    
    def get_latest_news(self):
        """获取最新文章列表"""
        try:
            # 生成当前时间戳
            timestamp = int(time.time() * 1000)
            
            # 请求参数
            params = {
                'client': 'web',
                'biz': 'web_news_col',
                'column': '351',  # 国际经济栏目ID
                'order': '1',
                'needInteractData': '0',
                'page_index': '1',
                'page_size': '20',
                'req_trace': str(timestamp),
                'fields': 'code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst',
                'types': '1,20',
                'callback': f'jQuery183018342709896086928_{timestamp-66}',
                '_': str(timestamp)
            }
            
            # 发送请求
            session = requests.Session()
            for key, value in self.cookies.items():
                session.cookies.set(key, value)
            
            response = session.get(
                self.api_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            # 解析JSONP响应
            jsonp_text = response.text
            match = re.search(r'jQuery\d+_\d+\((.*)\)', jsonp_text)
            if not match:
                return None
            
            json_str = match.group(1)
            data = json.loads(json_str)
            
            # 检查是否成功
            if data.get('code') != '1':
                return None
            
            # 获取文章列表
            article_list = data.get('data', {}).get('list', [])
            if not article_list:
                return None
            
            # 获取今天的日期（年-月-日）格式
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 遍历文章列表，找到今天发布的第一篇文章
            today_article = None
            for article in article_list:
                article_date = article.get('showTime', '')
                # 检查日期是否为当天
                if article_date and article_date.startswith(today):
                    today_article = article
                    break
            
            # 如果没有找到当天的文章，则返回None
            if not today_article:
                return None
            
            # 优先使用uniqueUrl，如果不存在则使用普通url字段
            article_url = today_article.get('uniqueUrl', '') or today_article.get('url', '')
            
            article_data = {
                'title': today_article.get('title', ''),
                'url': article_url,
                'summary': today_article.get('summary', ''),
                'date': today_article.get('showTime', ''),
                'source': today_article.get('mediaName', ''),
                'original_data': today_article
            }
            
            return article_data
            
        except Exception as e:
            return None
    
    def get_article_content(self, url):
        """获取文章详细内容"""
        try:
            if not url:
                return None
                
            # 发送请求
            session = requests.Session()
            for key, value in self.cookies.items():
                session.cookies.set(key, value)
            
            headers = {
                'User-Agent': self.headers['User-Agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': self.base_url
            }
            
            response = session.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return None
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title = ""
            title_element = soup.select_one('h1')
            if title_element:
                title = title_element.get_text(strip=True)
            
            # 提取日期和来源
            date = ""
            source = ""
            info_element = soup.select_one('div.time, div.inf')
            if info_element:
                info_text = info_element.get_text(strip=True)
                # 尝试提取来源和日期
                source_match = re.search(r'来源：\s*(.*?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(:\d{2})?)', info_text)
                if source_match:
                    source = source_match.group(1)
                    date = source_match.group(2)
                else:
                    # 仅提取日期
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(:\d{2})?)', info_text)
                    if date_match:
                        date = date_match.group(1)
            
            # 提取内容
            content_selectors = [
                'div.article-body', 
                'div.newsContent', 
                'div.Body', 
                'div#ContentBody', 
                'div.content',
                'div.Post_content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # 清理内容
                    for script in content_element.find_all(['script', 'style']):
                        script.decompose()
                    
                    # 提取段落
                    paragraphs = []
                    for p in content_element.find_all('p'):
                        text = p.get_text(strip=True)
                        if text:
                            paragraphs.append(text)
                    
                    if paragraphs:
                        content = '\n\n'.join(paragraphs)
                    else:
                        content = content_element.get_text(separator='\n\n', strip=True)
                    
                    break
            
            # 检查日期是否是当天
            if date:
                today = datetime.now().strftime('%Y-%m-%d')
                if not date.startswith(today):
                    return None
            
            # 返回文章详情
            return {
                'title': title,
                'date': date,
                'source': source,
                'content': content,
                'url': url
            }
            
        except Exception as e:
            return None
    
    def remove_backslashes(self, text):
        """移除文本中的反斜杠"""
        if not text:
            return text
        return text.replace('\\', '')
    
    def crawl(self):
        """抓取文章主函数"""
        try:
            # 获取当天最新文章
            latest_news = self.get_latest_news()
            if not latest_news:
                return {
                    "status": "success",
                    "message": "当天没有国际经济新闻",
                    "data": {}
                }
            
            # 获取文章详情
            article_url = latest_news.get('url')
            
            # 确保URL不为空
            if not article_url:
                return {
                    "status": "success",
                    "message": "当天没有国际经济新闻",
                    "data": {}
                }
            
            article_detail = self.get_article_content(article_url)
            if not article_detail:
                # 再次验证日期是否是当天
                article_date = latest_news.get('date', '')
                today = datetime.now().strftime('%Y-%m-%d')
                
                if not article_date or not article_date.startswith(today):
                    return {
                        "status": "success",
                        "message": "当天没有国际经济新闻",
                        "data": {}
                    }
                
                # 使用列表页信息返回
                result = {
                    'title': latest_news.get('title', ''),
                    'url': article_url,
                    'date': latest_news.get('date', ''),
                    'source': latest_news.get('source', ''),
                    'content': latest_news.get('summary', '')
                }
            else:
                # 合并信息
                result = {
                    'title': article_detail.get('title') or latest_news.get('title', ''),
                    'url': article_url,
                    'date': article_detail.get('date') or latest_news.get('date', ''),
                    'source': article_detail.get('source') or latest_news.get('source', ''),
                    'content': article_detail.get('content', '')
                }
            
            # 移除反斜杠
            for key in result:
                if isinstance(result[key], str):
                    result[key] = self.remove_backslashes(result[key])
            
            # 返回单个结果，与其他接口保持一致
            return {
                "status": "success",
                "message": "成功获取东方财富网国际经济最新文章",
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }

@eastmoney_international_bp.route('/eastmoney_international', methods=['GET'])
def get_eastmoney_international():
    """获取东方财富网国际经济最新文章接口"""
    try:
        crawler = EastmoneyInternationalCrawler()
        result = crawler.crawl()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": {}
        }

# 测试代码
if __name__ == "__main__":
    crawler = EastmoneyInternationalCrawler()
    result = crawler.crawl()
    print(json.dumps(result, ensure_ascii=False, indent=2)) 