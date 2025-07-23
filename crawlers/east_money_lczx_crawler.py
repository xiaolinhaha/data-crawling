import requests
from bs4 import BeautifulSoup
import json
import re
import time
import datetime
import os
from flask import Blueprint, request
from flask_restful import reqparse

class EastMoneyLczxCrawler:
    """东方财富网理财资讯爬虫，使用API获取文章列表，HTML解析获取详情"""
    
    def __init__(self):
        self.name = "东方财富网理财资讯"
        self.base_url = "https://money.eastmoney.com/"
        self.list_url = "https://money.eastmoney.com/a/clczx.html"
        self.api_url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
        self.content_selectors = ['div.article-content', 'div.newsContent', 'div.content', 'div.Body']
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Referer': 'https://money.eastmoney.com/a/clczx.html',
            'Accept': '*/*'
        }
    
    def remove_backslashes(self, text):
        """移除文本中的反斜杠"""
        if not text:
            return text
        return text.replace('\\', '')
    
    def get_api_data(self, page_index=1, page_size=20):
        """获取API数据"""
        try:
            # 请求参数
            params = {
                'client': 'web',
                'biz': 'web_news_col',
                'column': '583',  # 理财资讯栏目ID
                'order': '1',
                'needInteractData': '0',
                'page_index': str(page_index),
                'page_size': str(page_size),
                'req_trace': str(int(time.time() * 1000)),
                'fields': 'code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst',
                'types': '1,20',
                'callback': f'jQuery{int(time.time() * 1000)}',
                '_': str(int(time.time() * 1000))
            }
            
            response = requests.get(self.api_url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                # API返回的是JSONP格式，需要提取JSON部分
                json_str = re.search(r'jQuery\d+_?\d*\((.*)\)', response.text)
                if json_str:
                    data = json.loads(json_str.group(1))
                    return data
                else:
                    # 尝试直接解析为JSON
                    try:
                        data = json.loads(response.text)
                        return data
                    except:
                        pass
            
            return None
        except Exception as e:
            return None
    
    def parse_article_list(self):
        """解析文章列表，获取最新的文章标题、链接和发布时间"""
        api_data = self.get_api_data()
        if not api_data or api_data.get('code') != '1':
            return None
        
        # 获取文章列表
        articles = api_data.get('data', {}).get('list', [])
        if not articles:
            return None
        
        # 转换为统一格式，取第一条
        article_links = []
        for article in articles[:1]:
            title = article.get('title')
            url = article.get('uniqueUrl')
            summary = article.get('summary', '')
            
            # 获取发布时间
            pub_time = article.get('showTime')
            if not pub_time:
                # 如果API没有返回时间，使用当前时间
                pub_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 完整的发布时间和日期部分分开保存
            if title and url:
                article_links.append({
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'pub_time': pub_time,  # 完整时间，包含时分秒
                    'pub_date': pub_time[:10] if len(pub_time) > 10 else pub_time  # 只取日期部分 YYYY-MM-DD
                })
                break
        
        return article_links
    
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
    
    def parse_article_content(self, html):
        """解析文章内容，提取正文段落"""
        if not html:
            return "无法获取文章内容"
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找文章内容区域 - 首先查找常见内容区
            content_element = None
            
            # 东方财富网的特定选择器
            special_selectors = [
                'div.txtinfos',
                'div.article-content', 
                'div.newsContent', 
                'div.content', 
                'div.Body',
                'div.text',
                'div.post_text',
                'div#ContentBody',
                'div.detail-body'
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
                content_divs = soup.find_all('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'text', 'body', 'main', 'info']))
                
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
    
    def get_article_detail(self, url, pub_time=None):
        """获取文章详情，包括日期和内容"""
        html = self.get_html(url)
        if not html:
            return None
        
        content = self.parse_article_content(html)
        
        # 优先使用API返回的发布时间
        if pub_time:
            # 使用完整时间格式，包含时分秒
            date = pub_time
        else:
            # 从URL中尝试提取日期（东方财富的URL通常包含日期信息）
            date_match = re.search(r'/(\d{8})/', url)
            if date_match:
                date_str = date_match.group(1)
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} 00:00:00"
            else:
                # 如果URL中没有日期，尝试从HTML中提取
                soup = BeautifulSoup(html, 'html.parser')
                date_element = soup.select_one('.time, .date, .Article_time, .article-time, .article-meta')
                if date_element:
                    date_text = date_element.get_text(strip=True)
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                    if date_match:
                        date = date_match.group(1) + " 00:00:00"
                    else:
                        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # 最后使用当前日期时间
                    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            'date': date,
            'content': content
        }
    
    def is_within_24_hours(self, date_str):
        """
        判断给定的日期字符串是否在过去24小时内
        
        Args:
            date_str: 时间字符串，格式为 'YYYY-MM-DD HH:MM:SS'
            
        Returns:
            bool: 是否在过去24小时内
        """
        try:
            # 解析时间字符串
            if ' ' in date_str:
                # 如果包含时间部分
                article_date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            else:
                # 如果只有日期部分，加上默认时间
                article_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            
            # 获取当前时间
            now = datetime.datetime.now()
            
            # 计算24小时前的时间点
            time_24h_ago = now - datetime.timedelta(hours=24)
            
            # 判断文章日期是否在过去24小时内
            return time_24h_ago <= article_date <= now
        except Exception as e:
            # 如果解析失败，返回False
            return False
    
    def crawl(self):
        """执行爬虫，获取理财资讯最新文章"""
        article_links = self.parse_article_list()
        if not article_links:
            return {"status": "error", "message": "获取或解析列表页失败", "data": []}
        
        # 计算时间范围用于显示
        now = datetime.datetime.now()
        time_24h_ago = now - datetime.timedelta(hours=24)
        time_range = f"{time_24h_ago.strftime('%Y-%m-%d %H:%M')} 至 {now.strftime('%Y-%m-%d %H:%M')}"
        
        # 只处理第一条文章
        if article_links:
            first_article = article_links[0]
            
            # 获取发布时间
            pub_time = first_article.get('pub_time', '')
            
            # 检查文章是否在过去24小时内发布
            try:
                # 使用is_within_24_hours方法检查
                if not self.is_within_24_hours(pub_time):  # 不在过去24小时内
                    return {
                        "status": "success",
                        "message": f"没有在时间范围（{time_range}）内发布的新文章",
                        "source": self.name,
                        "data": []
                    }
                
            except Exception as e:
                # 如果解析出错，继续获取详情
                pass
            
            # 获取文章详情
            detail = self.get_article_detail(first_article['url'], first_article.get('pub_time'))
            if detail:
                # 移除所有内容中的反斜杠
                title = self.remove_backslashes(first_article['title'])
                url = self.remove_backslashes(first_article['url'])
                summary = self.remove_backslashes(first_article.get('summary', ''))
                date = self.remove_backslashes(detail['date'])
                content = self.remove_backslashes(detail['content'])
                
                # 再次检查详情页中的日期是否在过去24小时内
                try:
                    # 如果详情页的日期不在过去24小时内，返回空结果
                    if not self.is_within_24_hours(date):
                        return {
                            "status": "success",
                            "message": f"没有在时间范围（{time_range}）内发布的新文章",
                            "source": self.name,
                            "data": []
                        }
                except Exception as e:
                    # 如果解析出错，继续使用已获取的内容
                    pass
                
                results = [{
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'date': date,
                    'content': content
                }]
                
                # 处理返回消息中的反斜杠，添加时间范围
                message = f"成功获取{len(results)}条在时间范围（{time_range}）内发布的新闻"
                
                return {
                    "status": "success",
                    "message": message,
                    "source": self.name,
                    "data": results
                }
            else:
                return {"status": "error", "message": "获取文章详情失败", "data": []}
        
        return {"status": "error", "message": "未找到文章", "data": []}

# 集成到Flask蓝图
east_money_lczx_bp = Blueprint('east_money_lczx', __name__)

@east_money_lczx_bp.route('/east_money_lczx_news', methods=['GET'])
def get_east_money_lczx_news():
    """获取东方财富网理财资讯的最新文章"""
    crawler = EastMoneyLczxCrawler()
    result = crawler.crawl()
    return result 