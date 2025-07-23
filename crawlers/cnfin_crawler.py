import requests
from bs4 import BeautifulSoup
import time
import datetime
import re
import json
import os
import random
from flask import Blueprint, request
from flask_restful import reqparse

# 创建蓝图
cnfin_bp = Blueprint('cnfin', __name__)

class CnfinCrawler:
    """中国金融信息网爬虫，获取新闻列表和内容"""
    
    def __init__(self):
        self.name = "中国金融信息网"
        self.base_url = "https://www.cnfin.com"
        self.list_url = "https://www.cnfin.com/news/index.html"
        self.content_selectors = ['div.content-article', 'div.content', 'div.article-body', 'div.main-content']
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base_url
        }
        
        # 初始化cookies
        self.cookies = {}
    
    def refresh_cookies(self):
        """
        自动刷新Cookie
        """
        try:
            print("开始自动刷新中国金融信息网Cookie...")
            
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
            
            # 步骤1: 访问网站首页
            home_url = self.base_url
            print(f"1. 访问中国金融信息网首页: {home_url}")
            
            home_response = session.get(home_url, headers=basic_headers, timeout=15)
            print(f"首页响应状态码: {home_response.status_code}")
            print(f"获取到的Cookie: {session.cookies.get_dict()}")
            
            # 随机延迟，模拟人类行为
            time.sleep(random.uniform(1, 2))
            
            # 步骤2: 访问新闻列表页
            print(f"2. 访问新闻列表页: {self.list_url}")
            
            list_response = session.get(self.list_url, headers=basic_headers, timeout=15)
            print(f"列表页响应状态码: {list_response.status_code}")
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
    
    def normalize_url(self, url):
        """标准化URL，正确处理各种格式的相对链接"""
        if not url:
            return None
            
        # 如果是以//开头的URL（协议相对URL）
        if url.startswith('//'):
            return 'https:' + url
            
        # 如果是完整的URL（已经包含协议和域名）
        if url.startswith('http://') or url.startswith('https://'):
            return url
            
        # 如果是以/开头的绝对路径
        if url.startswith('/'):
            return self.base_url + url
            
        # 其他情况，作为相对路径处理
        return self.base_url + '/' + url
    
    def get_html(self, url):
        """获取网页HTML内容"""
        try:
            # 标准化URL
            url = self.normalize_url(url)
            
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
    
    def parse_article_list(self, html):
        """解析文章列表页，获取文章链接和时间"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找目标元素
            target_ul = soup.select_one('ul.cjmh-gdxw-cont')
            
            if not target_ul:
                return None
            
            # 查找所有文章项目 div.ui-zxlist-item
            news_items = target_ul.select('div.ui-zxlist-item')
            
            # 提取新闻信息
            article_links = []
            
            for idx, item in enumerate(news_items):
                # 查找标题和链接
                title_elem = item.select_one('h3 a')
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                link = title_elem.get('href', '')
                
                # 查找发布时间
                pub_time_elem = item.select_one('div.ui-publish')
                pub_time = pub_time_elem.text.strip() if pub_time_elem else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 规范化链接
                link = self.normalize_url(link)
                
                article_links.append({
                    'title': title,
                    'url': link,
                    'pub_time': pub_time
                })
                
                # 只获取前5条
                if len(article_links) >= 5:
                    break
                
            return article_links
            
        except Exception as e:
            return None
    
    def extract_date_from_article(self, html):
        """从文章详情页提取日期"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 首先查找页面中的日期元素
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{4}年\d{1,2}月\d{1,2}日)'
            ]
            
            # 尝试在页面文本中查找日期
            page_text = soup.get_text()
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    date_str = match.group(1)
                    # 转换为标准格式
                    if '年' in date_str:
                        date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                    return date_str
            
            # 如果没找到，返回当前日期
            return datetime.datetime.now().strftime("%Y-%m-%d")
            
        except Exception as e:
            return datetime.datetime.now().strftime("%Y-%m-%d")
    
    def parse_article_content(self, html):
        """解析文章内容，提取正文"""
        if not html:
            return "无法获取文章内容"
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 尝试在页面中查找文章正文容器
            content_element = None
            
            # 针对中国金融信息网的内容选择器
            for selector in self.content_selectors:
                element = soup.select_one(selector)
                if element:
                    content_element = element
                    break
            
            # 如果没找到，尝试查找主要内容区
            if not content_element:
                # 尝试找带有"article"、"content"等关键词的类
                content_divs = soup.find_all('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'body', 'main']))
                
                for div in content_divs:
                    # 查找有足够文本内容且包含多个段落的div
                    paragraphs = div.find_all('p')
                    if len(paragraphs) >= 2:
                        content_element = div
                        break
            
            # 如果仍然没有找到，直接找页面中的段落
            if not content_element:
                all_paragraphs = soup.find_all('p')
                
                # 过滤掉短文本段落
                paragraphs = []
                for p in all_paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 20:  # 有意义的段落应该至少有一定长度
                        paragraphs.append(text)
                
                if paragraphs:
                    return '\n\n'.join(paragraphs)
                
                return "未找到文章内容"
            
            # 提取正文内容
            # 移除脚本和样式元素
            for script in content_element.select('script, style'):
                script.decompose()
            
            # 获取所有段落文本
            paragraphs = []
            for p in content_element.find_all(['p']):
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # 过滤太短的段落
                    paragraphs.append(text)
            
            # 如果没有找到段落，获取div的文本
            if not paragraphs:
                text = content_element.get_text(separator="\n", strip=True)
                paragraphs = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 20]
            
            if not paragraphs:
                return "未找到有效的文章内容"
            
            return '\n\n'.join(paragraphs)
            
        except Exception as e:
            return f"解析文章内容出错: {e}"
    
    def get_article_detail(self, url):
        """获取文章详情，包括日期和内容"""
        html = self.get_html(url)
        if not html:
            return None
        
        date = self.extract_date_from_article(html)
        content = self.parse_article_content(html)
        
        return {
            'date': date,
            'content': content
        }
    
    def crawl(self):
        """爬取中国金融信息网的新闻"""
        try:
            # 获取网站首页HTML
            homepage_html = self.get_html(self.list_url)
            
            # 如果获取失败，尝试刷新Cookie
            if not homepage_html:
                print("初次获取列表页失败，尝试刷新Cookie...")
                if self.refresh_cookies():
                    print("使用刷新后的Cookie重新获取列表页...")
                    homepage_html = self.get_html(self.list_url)
            
            if not homepage_html:
                return {
                    "status": "error",
                    "message": "获取网站首页失败",
                    "data": None
                }
            
            # 解析文章列表
            article_links = self.parse_article_list(homepage_html)
            if not article_links or len(article_links) == 0:
                return {
                    "status": "error",
                    "message": "解析文章列表失败",
                    "data": None
                }
            
            # 获取第一篇文章
            first_article = article_links[0]
            
            # 检查文章是否在过去24小时内发布
            pub_time = first_article.get('pub_time', '')
            print(f"获取到的文章发布时间: {pub_time}")
            
            # 如果pub_time为空或格式不对，尝试获取文章详情中的日期
            if not pub_time or len(pub_time) < 10:
                article_detail_temp = self.get_article_detail(first_article['url'])
                if article_detail_temp and article_detail_temp.get('date'):
                    pub_time = article_detail_temp.get('date')
                    print(f"从文章详情中获取到的发布时间: {pub_time}")
            
            try:
                # 解析发布时间
                if ':' in pub_time:  # 包含时分秒的格式
                    if pub_time.count(':') == 2:  # 包含秒
                        pub_datetime = datetime.datetime.strptime(pub_time, "%Y-%m-%d %H:%M:%S")
                    else:  # 只有时分
                        pub_datetime = datetime.datetime.strptime(pub_time, "%Y-%m-%d %H:%M")
                else:  # 只有日期
                    pub_datetime = datetime.datetime.strptime(pub_time, "%Y-%m-%d")
                
                # 计算时间差
                current_time = datetime.datetime.now()
                time_diff = current_time - pub_datetime
                
                # 如果文章不是24小时内发布的，返回空结果
                if time_diff.days >= 1:
                    print(f"文章发布时间({pub_time})不在过去24小时内，返回空结果")
                    return {
                        "status": "success",
                        "message": "没有24小时内的新文章",
                        "data": None
                    }
                    
                print(f"文章发布于过去24小时内({pub_time})，继续获取详情")
            except Exception as e:
                print(f"解析发布时间出错: {str(e)}，将继续获取文章详情")
                # 如果解析出错，继续获取文章详情
            
            # 获取第一篇文章的详情
            article_detail = self.get_article_detail(first_article['url'])
            
            # 如果获取详情失败，尝试刷新Cookie后重试
            if not article_detail or not article_detail.get('content') or article_detail.get('content') == "无法获取文章内容":
                print("获取文章详情失败，尝试刷新Cookie...")
                if self.refresh_cookies():
                    print("使用刷新后的Cookie重新获取文章详情...")
                    article_detail = self.get_article_detail(first_article['url'])
            
            if not article_detail:
                return {
                    "status": "error",
                    "message": "获取文章详情失败",
                    "data": None
                }
            
            # 移除所有内容中的反斜杠
            title = self.remove_backslashes(first_article['title'])
            url = self.remove_backslashes(first_article['url'])
            date = self.remove_backslashes(article_detail['date'])
            content = self.remove_backslashes(article_detail['content'])
            
            result = {
                'title': title,
                'url': url,
                'source': self.name,
                'date': date,
                'content': content
            }
            
            return {
                "status": "success",
                "message": "成功获取中国金融信息网新闻",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"爬取过程中出错: {str(e)}",
                "data": None
            }

# 集成到Flask蓝图
cnfin_bp = Blueprint('cnfin', __name__)

@cnfin_bp.route('/cnfin_news', methods=['GET'])
def get_cnfin_news():
    """获取中国金融信息网的最新新闻"""
    crawler = CnfinCrawler()
    result = crawler.crawl()
    return result 