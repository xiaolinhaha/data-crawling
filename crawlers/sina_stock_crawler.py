#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
新浪财经股票爬虫
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
from datetime import datetime
from flask import Blueprint, request
from flask_restful import reqparse

# 创建蓝图
sina_stock_bp = Blueprint('sina_stock', __name__)

class SinaStockCrawler:
    """
    新浪财经股票爬虫类
    """

    def __init__(self):
        """
        初始化
        """
        self.name = "新浪财经股票"
        self.base_url = "https://finance.sina.com.cn/stock/"
        self.url = "https://finance.sina.com.cn/stock/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive'
        }
        
        # 初始化cookies
        self.cookies = {}
    
    def refresh_cookies(self):
        """
        自动刷新Cookie
        """
        try:
            print("开始自动刷新新浪财经Cookie...")
            
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
            
            # 步骤1: 访问新浪首页
            home_url = "https://www.sina.com.cn/"
            print(f"1. 访问新浪首页: {home_url}")
            
            home_response = session.get(home_url, headers=basic_headers, timeout=15)
            print(f"首页响应状态码: {home_response.status_code}")
            print(f"获取到的Cookie: {session.cookies.get_dict()}")
            
            # 随机延迟，模拟人类行为
            time.sleep(random.uniform(1, 2))
            
            # 步骤2: 访问财经股票页面
            print(f"2. 访问财经股票页面: {self.url}")
            
            list_response = session.get(self.url, headers=basic_headers, timeout=15)
            print(f"财经股票页面响应状态码: {list_response.status_code}")
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
        return text.replace('\\', '')

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
            print(f"获取HTML出错: {str(e)}")
            return None

    def parse_article_content(self, html):
        """解析文章内容，提取正文段落"""
        if not html:
            return "无法获取文章内容"
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找文章内容区域
            # 新浪财经网的常见内容选择器
            content_element = None
            
            special_selectors = [
                'div.article',
                'div#artibody', 
                'div.main-content', 
                'div.content', 
                'div.article-content',
                'div.text',
                'div.article_content'
            ]
            
            # 先尝试特定选择器
            for selector in special_selectors:
                element = soup.select_one(selector)
                if element:
                    content_element = element
                    break
            
            # 如果上面的选择器没找到，尝试更通用的方法
            if not content_element:
                # 查找可能包含文章的 div（通过类名关键词）
                content_divs = soup.find_all('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'text', 'body', 'main']))
                
                for div in content_divs:
                    # 查找有足够文本内容且包含多个段落的div
                    p_tags = div.find_all('p')
                    if len(p_tags) >= 3:  # 假设内容区域至少有3个段落
                        total_text = div.get_text(strip=True)
                        if len(total_text) > 200:  # 假设内容至少有200个字符
                            content_element = div
                            break
            
            if not content_element:
                # 最后尝试直接获取页面上的所有段落
                all_paragraphs = soup.find_all('p')
                
                if len(all_paragraphs) > 5:  # 如果有足够多的段落
                    paragraphs = []
                    for p in all_paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 20:  # 只保留有意义的段落
                            paragraphs.append(text)
                    
                    if paragraphs:
                        return '\n\n'.join(paragraphs)
                
                return "未找到文章内容"
            
            # 提取文章内容
            paragraphs = []
            
            # 移除内容中的脚本和样式元素
            for script in content_element.find_all(['script', 'style']):
                script.decompose()
            
            # 查找所有段落
            for p in content_element.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            
            # 如果没有找到足够的段落，则获取所有文本
            if len(paragraphs) < 3:
                text = content_element.get_text(separator="\n", strip=True)
                paragraphs = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 20]
            
            if not paragraphs:
                return "未找到文章内容"
            
            return '\n\n'.join(paragraphs)
            
        except Exception as e:
            return f"解析文章内容出错: {e}"

    def get_article_detail(self, url, title):
        """获取文章详情"""
        html = self.get_html(url)
        if not html:
            return None
        
        content = self.parse_article_content(html)
        
        # 使用当前日期
        date = datetime.now().strftime("%Y-%m-%d")
        
        return {
            'date': date,
            'title': title,
            'url': url,
            'content': content
        }

    def parse_stock_news(self):
        """解析股票页面顶部新闻，获取前5条新闻"""
        html = self.get_html(self.url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # 找到 tabs-contsWrap 下的第一个 tabs-cont sto_cont0 div
            tabs_cont = soup.select_one('.tabs-contsWrap .tabs-cont.sto_cont0')
            
            if not tabs_cont:
                return None
            
            # 在该区域内查找第一个 list01 列表
            news_list = tabs_cont.select('ul.list01')[0]
            if not news_list:
                return None
            
            # 获取多个有效的新闻链接（排除空格行）
            news_items = news_list.find_all('li')
            news_articles = []
            
            for item in news_items:
                # 跳过空格行
                if 'space01' in item.get('class', []):
                    continue
                
                # 找到有效新闻链接
                link = item.find('a')
                if link and link.get('href') and link.text.strip():
                    news = {
                        'title': link.text.strip(),
                        'url': link.get('href')
                    }
                    
                    # 确保URL是绝对URL
                    if not news['url'].startswith('http'):
                        if news['url'].startswith('//'):
                            news['url'] = 'https:' + news['url']
                        else:
                            news['url'] = 'https://finance.sina.com.cn' + news['url']
                    
                    news_articles.append(news)
                    
                    # 只获取前5条新闻
                    if len(news_articles) >= 5:
                        break
            
            return news_articles
            
        except Exception as e:
            print(f"解析股票新闻失败: {str(e)}")
            return None

    def crawl(self):
        """执行爬虫，获取股票新闻"""
        try:
            # 解析股票新闻，获取多条
            news_list = self.parse_stock_news()
            
            # 如果失败，尝试刷新Cookie并重新搜索
            if not news_list:
                print("初次获取股票新闻失败，尝试刷新Cookie...")
                if self.refresh_cookies():
                    print("使用刷新后的Cookie重新获取股票新闻...")
                    news_list = self.parse_stock_news()
            
            if not news_list or len(news_list) == 0:
                return {
                    "status": "error", 
                    "message": "未找到股票新闻", 
                    "data": None
                }
            
            valid_article = None
            
            # 遍历新闻，找到内容足够的文章
            for index, news_item in enumerate(news_list):
                print(f"尝试获取第{index+1}条新闻的详情...")
                
                # 获取文章详情
                article_detail = self.get_article_detail(news_item['url'], news_item['title'])
                
                # 检查内容是否有效
                if article_detail and article_detail.get('content'):
                    content = article_detail.get('content')
                    # 检查内容长度是否超过200字
                    if content != "无法获取文章内容" and content != "未找到文章内容" and len(content) >= 200:
                        print(f"第{index+1}条新闻内容有效，长度: {len(content)}字")
                        valid_article = article_detail
                        valid_article['title'] = news_item['title']
                        valid_article['url'] = news_item['url']
                        break
                    else:
                        print(f"第{index+1}条新闻内容不足200字或无效，长度: {len(content)}字")
                else:
                    print(f"第{index+1}条新闻获取详情失败")
            
            # 如果所有文章都不符合要求，返回空结果
            if not valid_article:
                return {
                    "status": "success", 
                    "message": "没有找到内容足够的新闻", 
                    "data": None
                }
            
            # 移除所有内容中的反斜杠
            title = self.remove_backslashes(valid_article['title'])
            url = self.remove_backslashes(valid_article['url'])
            date = self.remove_backslashes(valid_article['date'])
            content = self.remove_backslashes(valid_article['content'])
            
            result = {
                'title': title,
                'url': url,
                'source': self.name,
                'date': date,
                'content': content
            }
            
            return {
                "status": "success",
                "message": "成功获取新浪财经股票新闻",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"爬取过程中出错: {str(e)}",
                "data": None
            }

@sina_stock_bp.route('/sina_stock_news', methods=['GET'])
def get_sina_stock_news():
    """获取新浪财经股票新闻"""
    try:
        crawler = SinaStockCrawler()
        result = crawler.crawl()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取新浪财经股票新闻失败: {str(e)}",
            "data": None
        }

# 测试代码
if __name__ == "__main__":
    crawler = SinaStockCrawler()
    news = crawler.crawl()
    print(json.dumps(news, ensure_ascii=False, indent=4)) 