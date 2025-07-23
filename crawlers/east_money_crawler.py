import requests
from bs4 import BeautifulSoup
import json
import re
import time
import datetime
import os
import random
from flask import Blueprint, request
from flask_restful import reqparse

# 创建蓝图
east_money_bp = Blueprint('east_money', __name__)

class EastMoneyCrawler:
    """东方财富网爬虫，使用API获取文章列表，HTML解析获取详情"""
    
    def __init__(self):
        self.name = "东方财富网"
        self.base_url = "https://finance.eastmoney.com/"
        self.list_url = "https://finance.eastmoney.com/a/cpljh.html"
        self.api_url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"
        self.content_selectors = ['div.article-content', 'div.newsContent', 'div.content', 'div.Body']
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://finance.eastmoney.com/',
            'Accept': '*/*'
        }
        
        # 初始化cookies
        self.cookies = {}
    
    def refresh_cookies(self):
        """自动刷新Cookie"""
        try:
            print("开始自动刷新东方财富网Cookie...")
            
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
            
            # 步骤1: 访问东方财富网首页
            home_url = self.base_url
            print(f"1. 访问东方财富网首页: {home_url}")
            
            home_response = session.get(home_url, headers=basic_headers, timeout=15)
            print(f"首页响应状态码: {home_response.status_code}")
            print(f"获取到的Cookie: {session.cookies.get_dict()}")
            
            # 随机延迟，模拟人类行为
            time.sleep(random.uniform(1, 2))
            
            # 步骤2: 访问列表页面
            print(f"2. 访问列表页面: {self.list_url}")
            
            list_response = session.get(self.list_url, headers=basic_headers, timeout=15)
            print(f"列表页面响应状态码: {list_response.status_code}")
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
    
    def get_api_data(self, page_index=1, page_size=20):
        """获取API数据"""
        try:
            # 请求参数
            params = {
                'client': 'web',
                'biz': 'web_news_col',
                'column': '370',  # 评论精华栏目ID
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
            
            # 创建会话并设置cookies
            session = requests.Session()
            if self.cookies:
                for key, value in self.cookies.items():
                    session.cookies.set(key, value)
            
            response = session.get(self.api_url, headers=self.headers, params=params)
            
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
            print(f"获取API数据出错: {str(e)}")
            return None
    
    def parse_article_list(self):
        """解析文章列表，获取前5条文章标题、链接和发布时间"""
        api_data = self.get_api_data()
        if not api_data or api_data.get('code') != '1':
            return None
        
        # 获取文章列表
        articles = api_data.get('data', {}).get('list', [])
        if not articles:
            return None
        
        # 转换为统一格式，只取前5条
        article_links = []
        for article in articles[:5]:
            title = article.get('title')
            url = article.get('uniqueUrl')
            summary = article.get('summary', '')
            
            # 获取发布时间
            pub_time = article.get('showTime')
            if not pub_time:
                # 如果API没有返回时间，使用当前时间
                pub_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 提取日期部分
            if len(pub_time) > 10:
                pub_date = pub_time[:10]  # 只取日期部分 YYYY-MM-DD
            else:
                pub_date = pub_time
            
            if title and url:
                article_links.append({
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'pub_date': pub_date
                })
        
        # 按发布时间排序，最新的在前
        article_links.sort(key=lambda x: x['pub_date'], reverse=True)
        return article_links
    
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
                return None
        except Exception as e:
            print(f"获取HTML内容出错: {str(e)}")
            return None
    
    def parse_article_content(self, html):
        """解析文章内容，提取正文段落"""
        if not html:
            return "无法获取文章内容"
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找文章内容区域 - 首先查找 mainleft 下的 txtinfos
            mainleft = soup.find('div', class_='mainleft')
            
            if mainleft:
                txtinfos = mainleft.find('div', class_='txtinfos')
                
                if txtinfos:
                    content_element = txtinfos
                else:
                    # 尝试查找 mainleft 下的其他可能包含内容的区域
                    content_div = mainleft.find('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'text', 'info']))
                    if content_div:
                        content_element = content_div
                    else:
                        content_element = mainleft  # 如果找不到更具体的区域，就用 mainleft
            else:
                # 如果找不到 mainleft，回退到常规方法
                content_element = None
                
                # 东方财富网的特定选择器
                special_selectors = [
                    'div.txtinfos',  # 优先尝试 txtinfos
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
    
    def get_article_detail(self, url):
        """获取文章详情，包括日期和内容"""
        html = self.get_html(url)
        if not html:
            return None
        
        content = self.parse_article_content(html)
        # 从URL中尝试提取日期（东方财富的URL通常包含日期信息）
        date_match = re.search(r'/(\d{8})/', url)
        if date_match:
            date_str = date_match.group(1)
            date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        else:
            # 如果URL中没有日期，使用当前日期
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        return {
            'date': date,
            'content': content
        }
    
    def crawl(self):
        """获取东方财富网评论精华文章"""
        try:
            # 解析文章列表
            article_links = self.parse_article_list()
            
            # 如果获取失败，尝试刷新Cookie后重试
            if not article_links:
                print("初次获取文章列表失败，尝试刷新Cookie...")
                if self.refresh_cookies():
                    print("使用刷新后的Cookie重新获取文章列表...")
                    article_links = self.parse_article_list()
            
            if not article_links:
                return {
                    "status": "error",
                    "message": "未能获取到文章列表",
                    "data": None
                }
            
            # 只取第一篇文章
            first_article = article_links[0]
            
            # 检查文章是否在过去24小时内发布
            pub_date = first_article.get('pub_date', '')
            print(f"获取到的文章发布日期: {pub_date}")
            
            try:
                # 解析发布日期
                if not pub_date or len(pub_date) < 8:
                    # 如果没有日期信息，从URL提取
                    date_match = re.search(r'/(\d{8})/', first_article['url'])
                    if date_match:
                        date_str = date_match.group(1)
                        pub_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        print(f"从URL中提取的发布日期: {pub_date}")
                
                # 解析日期为日期时间对象
                if '-' in pub_date:
                    # 标准格式 YYYY-MM-DD
                    if len(pub_date) > 10 and ':' in pub_date:  # 包含时间
                        if pub_date.count(':') == 2:  # 包含秒
                            pub_datetime = datetime.datetime.strptime(pub_date, "%Y-%m-%d %H:%M:%S")
                        else:  # 只有时分
                            pub_datetime = datetime.datetime.strptime(pub_date, "%Y-%m-%d %H:%M")
                    else:  # 只有日期
                        pub_datetime = datetime.datetime.strptime(pub_date, "%Y-%m-%d")
                elif '/' in pub_date:
                    # 格式 YYYY/MM/DD
                    if len(pub_date) > 10 and ':' in pub_date:  # 包含时间
                        if pub_date.count(':') == 2:  # 包含秒
                            pub_datetime = datetime.datetime.strptime(pub_date, "%Y/%m/%d %H:%M:%S")
                        else:  # 只有时分
                            pub_datetime = datetime.datetime.strptime(pub_date, "%Y/%m/%d %H:%M")
                    else:  # 只有日期
                        pub_datetime = datetime.datetime.strptime(pub_date, "%Y/%m/%d")
                else:
                    # 未知格式，默认使用当前时间
                    pub_datetime = datetime.datetime.now()
                    
                # 计算时间差
                current_time = datetime.datetime.now()
                time_diff = current_time - pub_datetime
                
                # 检查是否在24小时内
                if time_diff.days >= 1:  # 超过24小时
                    print(f"文章发布时间({pub_date})不在过去24小时内，返回空结果")
                    return {
                        "status": "success",
                        "message": "没有24小时内的新文章",
                        "data": None
                    }
                
                print(f"文章发布于过去24小时内({pub_date})，继续获取详情")
            except Exception as e:
                print(f"解析发布时间出错: {str(e)}，将继续获取文章详情")
                # 发生错误时继续获取详情
            
            # 获取文章详情
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
                    "message": "未能获取到文章详情",
                    "data": None
                }
            
            # 整合结果
            result = {
                'title': self.remove_backslashes(first_article['title']),
                'url': self.remove_backslashes(first_article['url']),
                'source': self.name,
                'date': self.remove_backslashes(article_detail['date']),
                'content': self.remove_backslashes(article_detail['content'])
            }
            
            return {
                "status": "success",
                "message": "成功获取东方财富网评论精华文章",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"爬虫执行出错: {str(e)}",
                "data": None
            }

@east_money_bp.route('/east_money_news', methods=['GET'])
def get_east_money_news():
    """获取东方财富网的最新新闻"""
    crawler = EastMoneyCrawler()
    result = crawler.crawl()
    return result 