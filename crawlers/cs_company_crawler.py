#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
中证网公司要闻爬虫
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_restful import reqparse

# 创建蓝图
cs_company_bp = Blueprint('cs_company', __name__)

class CSCompanyCrawler:
    """
    中证网公司要闻爬虫类
    """

    def __init__(self):
        """
        初始化
        """
        self.name = "中证网公司要闻"
        self.base_url = "https://www.cs.com.cn/ssgs/gsxw/"
        self.url = "https://www.cs.com.cn/ssgs/gsxw/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        }
        
        # 初始化cookies
        self.cookies = {}
    
    def refresh_cookies(self):
        """
        自动刷新Cookie
        """
        try:
            print("开始自动刷新中证网Cookie...")
            
            # 创建一个新会话
            session = requests.Session()
            
            # 设置基本的浏览器标识
            basic_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 步骤1: 访问中证网首页
            home_url = "https://www.cs.com.cn/"
            print(f"1. 访问中证网首页: {home_url}")
            
            home_response = session.get(home_url, headers=basic_headers, timeout=15)
            print(f"首页响应状态码: {home_response.status_code}")
            print(f"获取到的Cookie: {session.cookies.get_dict()}")
            
            # 随机延迟，模拟人类行为
            time.sleep(random.uniform(1, 2))
            
            # 步骤2: 访问公司要闻页面
            print(f"2. 访问公司要闻页面: {self.url}")
            
            list_response = session.get(self.url, headers=basic_headers, timeout=15)
            print(f"公司要闻页面响应状态码: {list_response.status_code}")
            print(f"更新后的Cookie: {session.cookies.get_dict()}")
            
            # 获取所有Cookie
            cookies = session.cookies.get_dict()
            
            # 更新Cookie
            if cookies:
                # 记录原来的Cookie
                old_cookies = self.cookies.copy() if hasattr(self, 'cookies') else {}
                
                # 更新Cookie
                self.cookies = cookies
                
                print(f"Cookie已成功刷新！")
                print(f"原Cookie: {old_cookies}")
                print(f"新Cookie: {self.cookies}")
                return True
            else:
                print("未能获取到有效的Cookie")
                return False
                
        except Exception as e:
            print(f"刷新Cookie出错: {str(e)}")
            return False
    
    def remove_backslashes(self, text):
        """移除文本中的反斜杠"""
        if not text:
            return text
        # 使用更安全的方式处理反斜杠，保留必要的转义字符
        return text.replace('\\\\', '\\').replace('\\"', '"').replace('\\n', '\n')

    def get_html(self, url):
        """获取网页HTML内容"""
        try:
            # 创建会话并设置cookies
            session = requests.Session()
            if self.cookies:
                for key, value in self.cookies.items():
                    session.cookies.set(key, value)
            
            response = session.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
            else:
                print(f"获取HTML失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取HTML内容出错: {str(e)}")
            return None

    def extract_article_content(self, html):
        """从详情页提取文章内容"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # 针对中证网特定的文章内容区域选择器
            article_content = soup.select_one('#artibody') or soup.select_one('#article-content') or soup.select_one('#content')
            
            if not article_content:
                # 尝试其他可能的选择器
                article_content = soup.select_one('div.article-content') or soup.select_one('.content') or soup.select_one('#article')
            
            if not article_content:
                # 尝试更广泛的选择器
                article_content = soup.find('div', class_=lambda c: c and any(key in c.lower() for key in ['article', 'content', 'text-content']))
            
            if not article_content:
                # 最后尝试直接选择所有p标签
                paragraphs = []
                for p in soup.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:  # 只选择有实质内容的段落
                        paragraphs.append(text)
                
                if paragraphs:
                    return '\n\n'.join(paragraphs)
                return "无法获取文章内容"
            
            # 提取段落
            paragraphs = []
            for p in article_content.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            
            if not paragraphs:
                # 直接获取所有文本作为备选
                text = article_content.get_text(separator="\n", strip=True)
                paragraphs = [line.strip() for line in text.split('\n') if line.strip()]
            
            return '\n\n'.join(paragraphs)
            
        except Exception as e:
            print(f"解析文章内容出错: {str(e)}")
            return f"解析文章内容出错: {str(e)}"

    def get_article_detail(self, url, title=None, article_date=None):
        """获取文章详情"""
        html = self.get_html(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 如果没有传入标题
        if not title:
            title_element = soup.find('h1')
            if title_element:
                title = title_element.get_text(strip=True)
            else:
                title = "中证网公司要闻"
        
        # 如果没有传入日期
        if not article_date:
            date_element = soup.select_one('.date') or soup.select_one('.time')
            if date_element:
                date_text = date_element.get_text(strip=True)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    article_date = date_match.group(1)
                else:
                    article_date = datetime.now().strftime("%Y-%m-%d")
            else:
                article_date = datetime.now().strftime("%Y-%m-%d")
        
        content = self.extract_article_content(html)
        
        return {
            'title': title,
            'url': url,
            'date': article_date,
            'content': content
        }

    def parse_latest_articles(self, count=2):
        """解析中证网公司要闻页面的最新n篇文章"""
        html = self.get_html(self.url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # 找到所有具有日期信息的新闻条目
            news_items = []
            
            # 查找公司要闻区域的文章
            articles = soup.find_all('li')
            
            for article in articles:
                # 查找日期信息
                date_element = article.find(string=re.compile(r'\d{4}-\d{2}-\d{2}'))
                if date_element:
                    # 获取日期文本
                    date_text = date_element.strip()
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                    if date_match:
                        article_date = date_match.group(1)
                        
                        # 获取链接和标题
                        link = article.find('a', href=True)
                        if link:
                            url = link.get('href')
                            title = link.get_text(strip=True)
                            
                            # 清洗标题，移除日期前缀
                            title = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', '', title).strip()
                            
                            # 确保URL是绝对路径
                            if url and not url.startswith('http'):
                                if url.startswith('/'):
                                    url = 'https://www.cs.com.cn' + url
                                else:
                                    # 修复相对路径问题
                                    url = 'https://www.cs.com.cn/ssgs/gsxw/' + url.lstrip('./')
                            
                            news_items.append({
                                'date': article_date,
                                'title': title,
                                'url': url
                            })
            
            # 按日期排序，取最新的n篇
            if news_items:
                news_items.sort(key=lambda x: x['date'], reverse=True)
                return news_items[:count]
            
            return None
            
        except Exception as e:
            print(f"解析中证网文章列表出错: {str(e)}")
            return None

    def is_within_24_hours(self, date_str):
        """
        判断给定的日期字符串是否在过去24小时内
        
        Args:
            date_str: 时间字符串，格式为 'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DD'
            
        Returns:
            bool: 是否在过去24小时内
        """
        try:
            # 提取日期部分
            date_part = date_str.split(' ')[0] if ' ' in date_str else date_str
            
            # 解析时间字符串
            if ' ' in date_str and ':' in date_str:
                # 如果包含时间部分 (例如: 2024-05-14 10:30:00)
                article_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            elif ' ' in date_str:
                # 日期和时间但没有秒 (例如: 2024-05-14 10:30)
                article_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            else:
                # 如果只有日期部分，添加当天开始时间 (00:00:00)
                article_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 获取当前时间
            now = datetime.now()
            
            # 计算24小时前的时间点
            time_24h_ago = now - timedelta(hours=24)
            
            # 判断文章日期是否在过去24小时内
            return time_24h_ago <= article_date <= now
        except Exception as e:
            print(f"日期检查出错: {str(e)}")
            # 如果解析失败，返回False
            return False

    def crawl(self):
        """执行爬虫，获取中证网公司要闻页面的过去24小时内最新两篇文章，内容长度必须大于200字"""
        try:
            # 计算时间范围用于显示
            now = datetime.now()
            time_24h_ago = now - timedelta(hours=24)
            time_range = f"{time_24h_ago.strftime('%Y-%m-%d %H:%M')} 至 {now.strftime('%Y-%m-%d %H:%M')}"
            
            # 尝试从列表页获取最新文章信息
            articles_info = self.parse_latest_articles(count=10)  # 获取10篇，以便有更多文章可筛选
            
            # 如果获取失败，尝试刷新Cookie并重试
            if not articles_info:
                print("初次获取文章列表失败，尝试刷新Cookie...")
                if self.refresh_cookies():
                    print("使用刷新后的Cookie重新获取文章列表...")
                    articles_info = self.parse_latest_articles(count=10)
            
            # 如果列表页解析失败，使用硬编码备选方案
            if not articles_info:
                articles_info = [
                ]
            
            # 筛选出过去24小时内发布的文章
            recent_articles = []
            for article in articles_info:
                if self.is_within_24_hours(article['date']):
                    recent_articles.append(article)
            
            # 如果没有过去24小时内发布的文章，返回空
            if not recent_articles:
                return {
                    "status": "success",
                    "message": f"没有在时间范围（{time_range}）内发布的文章",
                    "data": None
                }
            
            # 收集符合内容长度要求的文章
            valid_articles = []
            
            # 获取每篇文章的详情，并筛选内容长度大于200字的文章
            for article_info in recent_articles:
                # 获取文章详情
                article_detail = self.get_article_detail(
                    article_info['url'], 
                    article_info['title'],
                    article_info['date']
                )
                
                # 如果获取详情失败，尝试刷新Cookie后重试
                if not article_detail or not article_detail.get('content') or article_detail.get('content') == "无法获取文章内容":
                    print("获取文章详情失败，尝试刷新Cookie...")
                    if self.refresh_cookies():
                        print("使用刷新后的Cookie重新获取文章详情...")
                        article_detail = self.get_article_detail(
                            article_info['url'], 
                            article_info['title'],
                            article_info['date']
                        )
                
                if not article_detail or not article_detail.get('content'):
                    continue
                
                # 检查内容长度是否大于200字
                content_length = len(article_detail['content'])
                if content_length < 200:
                    print(f"文章 '{article_detail['title']}' 内容长度不足200字，跳过")
                    continue
                
                # 移除所有内容中的反斜杠
                title = self.remove_backslashes(article_detail['title'])
                url = self.remove_backslashes(article_detail['url'])
                date = self.remove_backslashes(article_detail['date'])
                content = self.remove_backslashes(article_detail['content'])
                
                result = {
                    'title': title,
                    'url': url,
                    'source': self.name,
                    'date': date,
                    'content': content,
                    'content_length': content_length  # 添加内容长度字段，方便调试
                }
                
                valid_articles.append(result)
                
                # 最多收集2篇符合条件的文章
                if len(valid_articles) >= 2:
                    break
            
            # 如果没有符合条件的文章，返回空
            if not valid_articles:
                return {
                    "status": "success",
                    "message": f"没有内容长度大于200字的在时间范围（{time_range}）内的文章",
                    "data": None
                }
            
            # 处理返回结果，移除临时字段
            for article in valid_articles:
                if 'content_length' in article:
                    del article['content_length']
            
            # 返回成功信息，包含文章数量和时间范围
            articles_count = len(valid_articles)
            return {
                "status": "success",
                "message": f"成功获取在时间范围（{time_range}）内的中证网公司要闻，共 {articles_count} 条",
                "data": valid_articles
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"爬取过程中出错: {str(e)}",
                "data": None
            }

@cs_company_bp.route('/cs_company_article', methods=['GET'])
def get_cs_company_article():
    """获取中证网公司要闻页面的最新文章"""
    try:
        crawler = CSCompanyCrawler()
        result = crawler.crawl()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取中证网公司要闻失败: {str(e)}",
            "data": None
        }

# 测试代码
if __name__ == "__main__":
    crawler = CSCompanyCrawler()
    news = crawler.crawl()
    print(json.dumps(news, ensure_ascii=False, indent=4))