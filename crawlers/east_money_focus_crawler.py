import requests
from bs4 import BeautifulSoup
import json
import os
import datetime
import re
from flask import Blueprint, request
from flask_restful import reqparse


class EastMoneyFocusCrawler:
    """东方财富网焦点页面爬虫，爬取newsGuid下的第一个a标签内容"""
    
    def __init__(self):
        self.name = "东方财富网焦点"
        self.base_url = "https://finance.eastmoney.com"
        self.list_url = "https://finance.eastmoney.com/yaowen.html"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base_url
        }
    
    def remove_backslashes(self, text):
        """移除文本中的反斜杠"""
        if not text:
            return text
        return text.replace('\\', '')
    
    def get_html(self, url):
        """获取网页HTML内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as e:
            return None
    
    def parse_focus_article(self, html):
        """解析焦点页面，获取newsGuid下的第一个a标签内容"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找class为newsGuid的div
            news_guid_div = soup.find('div', class_='newsGuid')
            if not news_guid_div:
                # 尝试查找其他可能包含焦点新闻的元素
                news_lists = soup.find_all('div', class_='news_list')
                if news_lists:
                    for news_list in news_lists:
                        first_a = news_list.find('a')
                        if first_a and first_a.text.strip():
                            title = first_a.text.strip()
                            link = first_a.get('href', '')
                            
                            # 处理相对链接
                            if not link.startswith('http'):
                                if link.startswith('/'):
                                    link = self.base_url + link
                                else:
                                    link = self.base_url + '/' + link
                            
                            return {
                                'title': title,
                                'url': link
                            }
                return None
            
            # 获取div下的第一个a标签
            first_a = news_guid_div.find('a')
            if not first_a:
                return None
            
            title = first_a.text.strip()
            if not title:
                # 如果a标签文本为空，可能标题在其他标签中
                title_span = first_a.find('span')
                if title_span:
                    title = title_span.text.strip()
                
                # 如果仍然为空，尝试获取a标签的title属性
                if not title:
                    title = first_a.get('title', '')
                
                # 如果还是为空，尝试获取a标签的alt属性
                if not title:
                    img = first_a.find('img')
                    if img:
                        title = img.get('alt', '')
            
            # 如果以上方法都无法获取标题，尝试从URL中提取标题或使用页面标题
            if not title:
                # 从文章页面获取标题
                article_html = self.get_html(first_a.get('href', ''))
                if article_html:
                    article_soup = BeautifulSoup(article_html, 'html.parser')
                    article_title = article_soup.find('title')
                    if article_title:
                        title = article_title.text.strip()
                        # 去除网站名称后缀
                        title = title.replace(' _ 东方财富网', '').strip()
            
            link = first_a.get('href', '')
            
            # 处理相对链接
            if not link.startswith('http'):
                if link.startswith('/'):
                    link = self.base_url + link
                else:
                    link = self.base_url + '/' + link
            
            return {
                'title': title,
                'url': link
            }
        
        except Exception as e:
            return None
    
    def extract_date_from_article(self, html):
        """从文章详情页提取日期"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找可能包含日期的元素
            date_div = soup.find('div', class_='time')
            if date_div:
                date_text = date_div.get_text(strip=True)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    return date_match.group(1)
            
            # 如果上面的方法找不到，尝试其他可能含有日期的元素
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}/\d{2}/\d{2})'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, soup.get_text())
                if date_match:
                    date_str = date_match.group(1)
                    # 统一转换为yyyy-mm-dd格式
                    if '年' in date_str:
                        date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                    elif '/' in date_str:
                        date_str = date_str.replace('/', '-')
                    return date_str
            
            # 如果实在找不到日期，返回当前日期
            return datetime.datetime.now().strftime("%Y-%m-%d")
        
        except Exception as e:
            return datetime.datetime.now().strftime("%Y-%m-%d")
    
    def parse_article_content(self, html):
        """解析文章内容，去除图片"""
        if not html:
            return "无法获取文章内容"
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 东方财富网特定结构：
            # 1. 通常文章内容在id为ContentBody的div中
            # 2. 或者在class为Body的div中
            # 3. 有时在class为newsContent的div中
            
            # 优先尝试主要内容区域
            content_div = soup.find('div', id='ContentBody')  # 主要内容区域
            if not content_div:
                # 尝试其他可能的选择器
                content_div = soup.find('div', class_='Body')
                if not content_div:
                    content_div = soup.find('div', class_='content')
                    if not content_div:
                        content_div = soup.find('div', class_='newsContent')
                        if not content_div:
                            # 对于特定的页面布局，查找特定的结构
                            main_content = soup.find('div', class_='main-content')
                            if main_content:
                                article_cont = main_content.find('div', class_='article-cont')
                                if article_cont:
                                    content_div = article_cont
            
            # 如果仍然没有找到内容区域，尝试通用方法
            if not content_div:
                # 查找可能包含文章的 div（通过类名关键词）
                content_divs = soup.find_all('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'text', 'body', 'main']))
                
                for div in content_divs:
                    # 查找有足够文本内容且包含多个段落的div
                    p_tags = div.find_all('p')
                    if len(p_tags) >= 3:  # 假设内容至少有3个段落
                        content_div = div
                        break
            
            # 如果仍未找到内容区域，直接查找页面中的段落
            if not content_div:
                all_paragraphs = soup.find_all('p')
                paragraphs = []
                
                for p in all_paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:  # 只保留有意义的段落
                        paragraphs.append(text)
                
                if paragraphs:
                    return '\n\n'.join(paragraphs)
                
                return "未找到文章内容"
            
            # 处理找到的内容区域
            # 移除脚本、样式等元素
            for script in content_div.find_all(['script', 'style']):
                script.decompose()
            
            # 移除所有图片和相关容器
            for img in content_div.find_all('img'):
                img.decompose()
            
            # 移除可能的图片容器
            for img_container in content_div.find_all(['div', 'p'], class_=lambda c: c and ('img' in str(c).lower() or 'pic' in str(c).lower())):
                img_container.decompose()
            
            # 获取所有段落文本
            paragraphs = []
            for p in content_div.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # 只保留有意义的段落
                    paragraphs.append(text)
            
            # 如果段落太少，获取所有文本内容
            if len(paragraphs) < 3:
                text = content_div.get_text(separator="\n", strip=True)
                paragraphs = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 20]
            
            # 过滤掉一些可能的噪音段落
            filtered_paragraphs = [p for p in paragraphs if not any(noise in p for noise in ['责任编辑', '免责声明', '原标题', '来源'])]
            
            if not filtered_paragraphs:
                return "未找到有效的文章内容"
            
            return '\n\n'.join(filtered_paragraphs)
        
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
        """爬取东方财富网焦点文章"""
        html = self.get_html(self.list_url)
        if not html:
            return {"status": "error", "message": "获取焦点页面失败", "data": []}
        
        article = self.parse_focus_article(html)
        if not article:
            return {"status": "error", "message": "解析焦点文章失败", "data": []}
        
        detail = self.get_article_detail(article['url'])
        if not detail:
            return {"status": "error", "message": "获取文章详情失败", "data": []}
        
        # 移除所有内容中的反斜杠
        title = self.remove_backslashes(article['title'])
        url = self.remove_backslashes(article['url'])
        date = self.remove_backslashes(detail['date'])
        content = self.remove_backslashes(detail['content'])
        
        result = {
            'title': title,
            'url': url,
            'date': date,
            'content': content
        }
        
        # 处理返回消息中的反斜杠
        message = "成功获取焦点文章"
        source = self.name
        
        return {
            "status": "success",
            "message": message,
            "source": source,
            "data": [result]
        }

# 集成到Flask蓝图
east_money_focus_bp = Blueprint('east_money_focus', __name__)

@east_money_focus_bp.route('/east_money_focus', methods=['GET'])
def get_east_money_focus():
    """获取东方财富网焦点文章"""
    crawler = EastMoneyFocusCrawler()
    result = crawler.crawl()
    return result 