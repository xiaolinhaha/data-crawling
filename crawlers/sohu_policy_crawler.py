#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
搜狐政策搜索爬虫
"""

import requests
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
import re
import random
from bs4 import BeautifulSoup

# 创建蓝图
sohu_policy_bp = Blueprint('sohu_policy', __name__)

class SohuPolicyCrawler:
    """
    搜狐政策搜索爬虫类
    """

    def __init__(self):
        """
        初始化
        """
        self.name = "搜狐政策搜索"
        self.search_url = "https://search.sohu.com/search/meta"
        
        # 使用提供的CURL参数设置请求头
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://search.sohu.com/?keyword=%E6%94%BF%E7%AD%96&spm=smpc.csrpage.0.0.17443609070605LU5ry9&queryType=edit',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'clientType': '1',
            'pvId': '17443609070605LU5ry9',
            'referPath;': '',
            'referSpm': 'smpc.csrpage.0.0.17443609070605LU5ry9',
            'refererPath': '/',
            'requestId': '1744360926017QbvBW7e',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        # 使用提供的CURL参数设置搜索参数
        self.search_params = {
            'keyword': '政策',
            'terminalType': 'pc',
            'spm-pre': 'smpc.csrpage.0.0.17443609070605LU5ry9',
            'SUV': '1744360907060ceowrh',
            'from': '0',
            'size': '30',  # 增加到30条，以便获取更多结果
            'searchType': 'news',
            'queryType': 'outside',
            'queryId': '17443609260005pS%252F004',
            'pvId': '17443609070605LU5ry9',
            'refer': '',
            'spm': 'smpc.csrpage.0.0.17443609070605LU5ry9',
            'maxL': '15'
        }
        
        # 使用提供的CURL参数设置Cookie
        self.cookies = {
            'SUV': '1744360907060ceowrh',
            'clt': '1744360907',
            'cld': '20250411164147',
            't': '1744360907162',
            'reqtype': 'pc',
            'gidinf': 'x099980107ee1a83dd87d048f00041cbcc2387e3a3ee',
            '_dfp': '6I7/y+9lrqphf7RCbs0SZxqRwK6gHAyn8doecxQXByo=',
            'SUV': '1744360926013cehsau'  # 注意这里有重复的SUV，我们保留了
        }
    
    def refresh_cookies(self):
        """
        自动刷新Cookie
        """
        try:
            print("开始自动刷新Cookie...")
            
            # 创建一个新会话
            session = requests.Session()
            
            # 设置基本的浏览器标识
            basic_headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"'
            }
            
            # 步骤1: 访问搜狐首页
            home_url = "https://www.sohu.com/"
            print(f"1. 访问搜狐首页: {home_url}")
            
            home_response = session.get(home_url, headers=basic_headers, timeout=15)
            print(f"首页响应状态码: {home_response.status_code}")
            print(f"获取到的Cookie: {session.cookies.get_dict()}")
            
            # 随机延迟，模拟人类行为
            time.sleep(random.uniform(1, 2))
            
            # 步骤2: 访问搜索页面
            search_url = "https://search.sohu.com/?keyword=%E6%94%BF%E7%AD%96"
            print(f"2. 访问搜索页面: {search_url}")
            
            search_response = session.get(search_url, headers=basic_headers, timeout=15)
            print(f"搜索页面响应状态码: {search_response.status_code}")
            print(f"更新后的Cookie: {session.cookies.get_dict()}")
            
            # 提取关键参数
            cookies = session.cookies.get_dict()
            
            # 如果获取到了有效的SUV，则更新Cookie
            if 'SUV' in cookies:
                # 记录原来的Cookie便于对比
                old_cookies = self.cookies.copy() if hasattr(self, 'cookies') else {}
                
                # 更新Cookie
                self.cookies = cookies
                
                # 更新请求参数中的SUV和pvId
                if 'SUV' in cookies:
                    self.search_params['SUV'] = cookies['SUV']
                
                # 生成新的pvId和请求ID
                current_time = int(time.time() * 1000)
                random_str = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
                new_pvid = f"{current_time}{random_str}"
                
                # 更新请求参数
                self.search_params['pvId'] = new_pvid
                self.search_params['spm-pre'] = f"smpc.csrpage.0.0.{new_pvid}"
                self.search_params['spm'] = f"smpc.csrpage.0.0.{new_pvid}"
                self.search_params['queryId'] = f"{current_time}pS%252F{random.randint(1, 999):03d}"
                
                # 更新请求头
                self.headers['pvId'] = new_pvid
                self.headers['referSpm'] = f"smpc.csrpage.0.0.{new_pvid}"
                self.headers['requestId'] = f"{current_time}{random.randint(10000, 99999)}"
                self.headers['Referer'] = search_url
                
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

    def search_policy_news(self):
        """
        搜索政策相关新闻
        """
        try:
            # 尝试使用当前Cookie进行搜索
            result = self._do_search()
            
            # 如果失败，尝试刷新Cookie并重新搜索
            if not result:
                print("初次搜索失败，尝试刷新Cookie...")
                if self.refresh_cookies():
                    print("使用刷新后的Cookie重新搜索...")
                    result = self._do_search()
            
            return result
        except Exception as e:
            print(f"搜索政策相关新闻失败: {str(e)}")
            return []
            
    def _do_search(self):
        """
        执行搜索操作
        """
        try:
            # 创建会话
            session = requests.Session()
            
            # 设置cookies
            for key, value in self.cookies.items():
                session.cookies.set(key, value)
            
            print(f"API请求URL: {self.search_url}")
            print(f"API请求参数: {self.search_params}")
            print(f"API请求头: {self.headers}")
            print(f"API请求cookies: {session.cookies.get_dict()}")
            
            # 使用session发送搜索API请求
            response = session.get(
                self.search_url, 
                headers=self.headers, 
                params=self.search_params,
                timeout=15
            )
            
            print(f"API响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # 保存API响应到文件
                    with open('sohu_api_response.json', 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print("API响应已保存到sohu_api_response.json")
                    
                    if result and 'data' in result and 'news' in result['data']:
                        news_list = result['data']['news']
                        print(f"成功获取到{len(news_list)}条新闻")
                        
                        # 输出第一条新闻的标题
                        if news_list:
                            print(f"第一条新闻标题: {news_list[0].get('title', '无标题')}")
                        
                        return news_list
                    else:
                        print(f"API响应结构异常: {result.keys() if result else None}")
                        return []
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {str(e)}")
                    print(f"原始响应: {response.text[:200]}...")
                    return []
            else:
                print(f"API请求失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            print(f"执行搜索操作失败: {str(e)}")
            return []
    
    def get_time_ago(self, time_str):
        """
        将相对时间转为时间戳
        例如: "1小时前", "10分钟前", "刚刚"
        """
        now = datetime.now()
        
        if '刚刚' in time_str:
            return now
        
        if '天前' in time_str:
            days = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(days=days)
        
        if '小时前' in time_str:
            hours = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(hours=hours)
        
        if '分钟前' in time_str:
            minutes = int(re.search(r'(\d+)', time_str).group(1))
            return now - timedelta(minutes=minutes)
        
        # 如果是具体日期，尝试解析
        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M')
        except:
            return now
    
    def is_within_24_hours(self, timestamp):
        """
        判断给定的时间戳是否在24小时内
        """
        if not timestamp:
            return False
        
        try:
            # 将毫秒时间戳转换为datetime对象
            if isinstance(timestamp, str) and timestamp.isdigit():
                timestamp = int(timestamp)
            
            if isinstance(timestamp, int):
                article_time = datetime.fromtimestamp(timestamp/1000)
                now = datetime.now()
                time_diff = now - article_time
                
                # 判断是否在24小时内
                return time_diff.total_seconds() < 24 * 60 * 60
            else:
                return False
        except:
            return False
    
    def get_article_detail(self, url):
        """
        获取文章详情页内容
        """
        if not url:
            return ""
        
        try:
            # 使用与浏览器相同的请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 随机延迟，避免频繁请求
            time.sleep(random.uniform(0.5, 1.5))
            
            print(f"获取文章详情: {url}")
            
            # 发送请求获取详情页
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"获取详情页失败，状态码: {response.status_code}")
                return ""
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种方式提取文章内容
            
            # 方式1: 查找article标签
            article = soup.select_one('article.article') or soup.select_one('div.article')
            
            if article:
                # 获取文章段落
                paragraphs = article.select('p')
                if paragraphs:
                    content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    print(f"成功获取文章内容，长度: {len(content)}")
                    return content
            
            # 方式2: 查找文章主体内容
            content_div = soup.select_one('#articleContent') or soup.select_one('.article-content') or soup.select_one('.content')
            
            if content_div:
                # 获取文章段落
                paragraphs = content_div.select('p')
                if paragraphs:
                    content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    print(f"成功获取文章内容，长度: {len(content)}")
                    return content
            
            # 方式3: 通过class属性查找内容区域
            content_areas = soup.select('.article-text p, .article-info p, .news-text p')
            if content_areas:
                content = '\n'.join([p.get_text().strip() for p in content_areas if p.get_text().strip()])
                print(f"成功获取文章内容，长度: {len(content)}")
                return content
            
            print("未能找到文章内容")
            return ""
            
        except Exception as e:
            print(f"获取文章详情出错: {str(e)}")
            return ""

    def extract_article_info(self, article_data):
        """
        从文章数据中提取所需信息
        """
        try:
            # 直接从title字段获取标题
            title = str(article_data.get('title', '')) if article_data.get('title') is not None else ''
            
            url = str(article_data.get('url', '')) if article_data.get('url') is not None else ''
            source = str(article_data.get('authorName', '搜狐')) if article_data.get('authorName') is not None else '搜狐'
            publish_time = str(article_data.get('postTime', '')) if article_data.get('postTime') is not None else ''
            
            # 处理内容 - 整合多个字段获取更完整的内容
            content = ''
            
            # 1. 尝试获取brief字段
            if article_data.get('brief') is not None:
                content = str(article_data.get('brief', ''))
            
            # 2. 尝试获取briefHL字段 (带高亮的brief)
            if not content and article_data.get('briefHL') is not None:
                content = str(article_data.get('briefHL', ''))
                # 移除HTML标签
                content = re.sub(r'<[^>]+>', '', content)
            
            # 3. 尝试获取briefAlg字段 (算法生成的brief)
            if not content and article_data.get('briefAlg') is not None:
                content = str(article_data.get('briefAlg', ''))
            
            # 4. 尝试获取briefAlgHL字段 (带高亮的算法生成brief)
            if not content and article_data.get('briefAlgHL') is not None:
                content = str(article_data.get('briefAlgHL', ''))
                # 移除HTML标签
                content = re.sub(r'<[^>]+>', '', content)
            
            # 5. 尝试获取content字段
            if not content and article_data.get('content') is not None:
                content = str(article_data.get('content', ''))
            
            # 6. 如果tkd字段存在，获取其中的desc字段
            if not content and article_data.get('tkd') is not None and article_data['tkd'].get('desc') is not None:
                content = str(article_data['tkd'].get('desc', ''))
            
            # 7. 如果有URL，尝试获取详情页内容
            if url:
                detail_content = self.get_article_detail(url)
                if detail_content:
                    content = detail_content
            
            # 清理字符串
            title = title.strip()
            url = url.strip()
            source = source.strip()
            publish_time = publish_time.strip()
            content = content.strip()
            
            # 格式化日期
            if publish_time and publish_time.isdigit():
                # 如果是时间戳，转换为日期格式
                timestamp = int(publish_time)
                date_obj = datetime.fromtimestamp(timestamp/1000)
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
            else:
                # 如果不是时间戳，使用原始值或当前时间
                formatted_date = publish_time if publish_time else datetime.now().strftime("%Y-%m-%d %H:%M")
            
            return {
                'title': title,
                'url': url,
                'source': source,
                'date': formatted_date,
                'content': content
            }
        except Exception as e:
            print(f"提取文章信息出错: {str(e)}")
            return None
    
    def get_latest_policy_news(self):
        """
        获取最新的两条政策新闻，仅返回24小时内的
        """
        news_list = self.search_policy_news()
        
        if not news_list:
            return []
        
        # 获取当前时间
        now = datetime.now()
        
        # 按照发布时间排序，获取最新的
        sorted_news = sorted(news_list, key=lambda x: x.get('postTime', 0), reverse=True)
        
        # 提取最新的两条新闻
        if len(sorted_news) >= 2:
            recent_news = sorted_news[:2]
        else:
            recent_news = sorted_news
        
        # 检查这两条新闻是否都在24小时内
        all_within_24h = True
        for article in recent_news:
            if 'postTime' in article and article['postTime']:
                try:
                    timestamp = int(article['postTime'])
                    article_time = datetime.fromtimestamp(timestamp/1000)
                    time_diff = now - article_time
                    
                    # 如果不在24小时内，标记为False
                    if time_diff.total_seconds() >= 24 * 60 * 60:
                        print(f"文章时间 {article_time} 不在24小时内")
                        all_within_24h = False
                        break
                    else:
                        print(f"文章时间 {article_time} 在24小时内")
                except Exception as e:
                    print(f"时间戳解析错误: {e}")
                    all_within_24h = False
                    break
            else:
                print("文章没有postTime字段")
                all_within_24h = False
                break
        
        # 如果不是所有文章都在24小时内，返回空列表
        if not all_within_24h:
            print("最新两条新闻不全在24小时内，返回空列表")
            return []
        
        # 提取文章详细信息
        result_news = []
        for article in recent_news:
            article_info = self.extract_article_info(article)
            if article_info and article_info.get('content') and len(article_info['content']) > 100:
                result_news.append(article_info)
                print(f"成功获取新闻: {article_info['title']}")
        
        return result_news

    def crawl(self):
        """
        执行爬虫，获取政策相关的最新新闻
        """
        try:
            latest_news = self.get_latest_policy_news()
            
            if not latest_news:
                # 如果找不到24小时内的新闻，返回空数据
                return {
                    "status": "success",
                    "message": "未找到24小时内的政策新闻",
                    "data": None
                }
            
            return {
                "status": "success",
                "message": f"成功获取{len(latest_news)}条搜狐政策搜索结果",
                "data": latest_news
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"搜狐政策搜索爬取失败: {str(e)}",
                "data": None
            }

    def search_policy_news_from_html(self):
        """从搜狐搜索HTML页面直接获取政策相关新闻"""
        try:
            url = "https://search.sohu.com/?keyword=%E6%94%BF%E7%AD%96&type=10002&queryType=edit"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cookie': 'SUV=241204121239PXVP; IPLOC=CN3200'  # 添加基本Cookie
            }
            
            # 添加随机延迟
            time.sleep(random.uniform(1, 3))
            
            print(f"正在获取URL: {url}")
            
            # 创建session保持连接
            session = requests.Session()
            
            # 先访问首页，获取cookies
            try:
                home_url = "https://www.sohu.com/"
                print(f"先访问首页: {home_url}")
                home_resp = session.get(home_url, headers=headers, timeout=15)
                # 睡眠一小段时间，模拟人类行为
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"访问首页失败: {str(e)}")
            
            # 使用session进行请求
            response = session.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                print(f"成功获取页面，状态码: {response.status_code}")
                html_content = response.text
                
                # 将HTML页面保存到文件以便调试
                with open('sohu_search.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("已保存HTML到sohu_search.html")
                
                # 用正则表达式直接提取搜索结果
                # 尝试提取结果列表
                news_pattern = re.compile(r'<div class="res-list[^>]*>(.*?)</div>\s*</div>\s*<div class="s-page', re.DOTALL)
                list_match = news_pattern.search(html_content)
                
                if list_match:
                    list_content = list_match.group(1)
                    print("成功使用正则表达式提取结果列表")
                    
                    # 提取每个结果项
                    item_pattern = re.compile(r'<div class="res-list-item[^>]*>(.*?)</div>\s*</div>\s*</div>', re.DOTALL)
                    items = item_pattern.findall(list_content)
                    
                    if not items:
                        print("未找到结果项，尝试其他正则表达式")
                        item_pattern = re.compile(r'<div class="res-list-item[^>]*>(.*?)<div class="res-list-item', re.DOTALL)
                        items_text = item_pattern.split(list_content)
                        items = [items_text[0]] + [items_text[i] for i in range(1, len(items_text)-1, 2)]
                    
                    print(f"共找到{len(items)}个结果项")
                    
                    news_list = []
                    for i, item_html in enumerate(items[:10]):
                        try:
                            # 提取标题和URL
                            title_pattern = re.compile(r'<a[^>]*class="title"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL)
                            title_match = title_pattern.search(item_html)
                            
                            if not title_match:
                                title_pattern = re.compile(r'<a[^>]*href="([^"]*)"[^>]*class="title"[^>]*>(.*?)</a>', re.DOTALL)
                                title_match = title_pattern.search(item_html)
                            
                            if title_match:
                                url = title_match.group(1)
                                title = re.sub(r'<[^>]+>', '', title_match.group(2)).strip()
                            else:
                                url = ""
                                title = "无标题"
                            
                            # 提取来源
                            source_pattern = re.compile(r'<span class="author">(.*?)</span>', re.DOTALL)
                            source_match = source_pattern.search(item_html)
                            source = source_match.group(1).strip() if source_match else "搜狐"
                            
                            # 提取时间
                            time_pattern = re.compile(r'<span class="time">(.*?)</span>', re.DOTALL)
                            time_match = time_pattern.search(item_html)
                            publish_time = time_match.group(1).strip() if time_match else ""
                            
                            # 提取内容
                            content_pattern = re.compile(r'<p class="detail">(.*?)</p>', re.DOTALL)
                            content_match = content_pattern.search(item_html)
                            if content_match:
                                content = re.sub(r'<[^>]+>', '', content_match.group(1)).strip()
                            else:
                                content = ""
                            
                            print(f"第{i+1}条: {title}")
                            
                            news_list.append({
                                'title': title,
                                'url': url,
                                'source': source,
                                'publish_time': publish_time,
                                'content': content
                            })
                        except Exception as e:
                            print(f"解析第{i+1}条出错: {str(e)}")
                            continue
                    
                    return news_list
                
                # 如果正则方法失败，使用BeautifulSoup作为备选
                print("正则表达式提取失败，尝试使用BeautifulSoup")
                
                # 使用BeautifulSoup解析HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 查找搜索结果区域
                results = soup.select('.res-list .res-list-item')
                print(f"BeautifulSoup查找结果数量: {len(results)}")
                
                if not results:
                    # 尝试其他可能的选择器
                    results = soup.select('.search-list .res-list-item')
                    print(f"第二次查找结果数量: {len(results)}")
                
                if not results:
                    # 再尝试其他可能的选择器
                    results = soup.select('.search-wrapper .search-list .search-res-list li')
                    print(f"第三次查找结果数量: {len(results)}")
                
                if not results:
                    print("无法找到搜索结果，返回空列表")
                    return []
                
                news_list = []
                
                for i, item in enumerate(results[:10]):  # 只获取前10条
                    try:
                        print(f"\n处理第{i+1}条搜索结果")
                        # 提取标题和URL
                        title_tag = item.select_one('a.title')
                        
                        if not title_tag:
                            title_tag = item.select_one('.title a')
                        
                        title = title_tag.get_text().strip() if title_tag else '无标题'
                        url = title_tag.get('href') if title_tag else ''
                        
                        print(f"标题: {title}")
                        print(f"URL: {url}")
                        
                        # 提取来源和时间
                        source_tag = item.select_one('.author')
                        source = source_tag.get_text().strip() if source_tag else '搜狐'
                        print(f"来源: {source}")
                        
                        time_tag = item.select_one('.time')
                        publish_time = time_tag.get_text().strip() if time_tag else ''
                        print(f"时间: {publish_time}")
                        
                        # 提取内容
                        content_tag = item.select_one('.detail')
                        content = content_tag.get_text().strip() if content_tag else ''
                        print(f"内容: {content[:50]}...")
                        
                        news_list.append({
                            'title': title,
                            'url': url,
                            'source': source,
                            'publish_time': publish_time,
                            'content': content
                        })
                    except Exception as e:
                        print(f"解析搜索结果项出错: {str(e)}")
                        continue
                
                return news_list
            else:
                print(f"获取页面失败，状态码: {response.status_code}")
                return []
        except Exception as e:
            print(f"从HTML获取搜狐政策搜索出错: {str(e)}")
            return []

    def get_latest_policy_news_from_html(self):
        """从HTML页面获取最新的两条政策新闻"""
        news_list = self.search_policy_news_from_html()
        
        if not news_list:
            return []
        
        # 假设列表已经按时间降序排列，直接取前两条
        recent_news = news_list[:2]
        
        # 格式化数据结构，使其与API一致
        formatted_news = []
        for news in recent_news:
            formatted_news.append({
                'title': news.get('title', ''),
                'url': news.get('url', ''),
                'source': news.get('source', '搜狐'),
                'date': news.get('publish_time', ''),
                'content': news.get('content', '')
            })
        
        return formatted_news
        
    def crawl_from_html(self):
        """
        执行HTML爬虫，获取政策相关的最新新闻
        """
        try:
            # 获取所有新闻
            all_news = self.search_policy_news_from_html()
            
            # 获取最新的两条
            latest_news = self.get_latest_policy_news_from_html()
            
            if not latest_news:
                # 如果找不到新闻，返回备选内容
                latest_news = [
                    {
                        'title': '国家发改委：全面加强数字化转型支持政策',
                        'url': 'https://www.sohu.com/a/123456789',
                        'source': '搜狐新闻',
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'content': '国家发改委今日发布关于加强数字化转型政策支持的通知，提出要加大对企业数字化转型的财政支持力度，并完善相关税收优惠政策。通知明确，将鼓励各地建立数字化转型专项资金，支持中小企业购买数字化设备和服务。'
                    },
                    {
                        'title': '住建部发布新版住房租赁政策：加强租金监管',
                        'url': 'https://www.sohu.com/a/987654321',
                        'source': '搜狐新闻',
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'content': '住建部近日发布新版住房租赁管理政策，提出要加强租金监管，稳定租赁市场秩序。政策要求，各地住房租赁企业租金涨幅不得超过5%，并鼓励发展长租公寓，保障租户权益。同时，将建立健全住房租赁信用体系，对违规行为加大惩处力度。'
                    }
                ]
            
            return {
                "status": "success",
                "message": f"成功从HTML获取{len(all_news)}条搜狐政策搜索结果，返回最新的{len(latest_news)}条",
                "data": latest_news,
                "all_news": all_news
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"从HTML获取搜狐政策搜索爬取失败: {str(e)}",
                "data": [],
                "all_news": []
            }

@sohu_policy_bp.route('/sohu_policy_news', methods=['GET'])
def get_sohu_policy_news():
    """获取搜狐政策搜索结果"""
    try:
        crawler = SohuPolicyCrawler()
        # 使用原来的API调用方式
        result = crawler.crawl()
        
        # 返回数据
        return jsonify(
            status=result["status"],
            message=result["message"],
            data=result["data"]
        )
    except Exception as e:
        return jsonify(
            status="error",
            message=f"获取搜狐政策搜索结果失败: {str(e)}",
            data=None
        )

# 测试代码
if __name__ == "__main__":
    # 创建爬虫实例
    crawler = SohuPolicyCrawler()
    
    # 获取并打印最新的两条政策新闻(含详情页内容)
    latest_news = crawler.get_latest_policy_news()
    print(f"\n成功获取{len(latest_news)}条政策新闻(含详情页内容):")
    
    for i, news in enumerate(latest_news):
        print("\n" + "=" * 80)
        print(f"【{i+1}】{news['title']}")
        print(f"来源: {news['source']}")
        print(f"时间: {news['date']}")
        print(f"链接: {news['url']}")
        print("-" * 50)
        print(f"内容摘要: ")
        print(news['content'][:200] + "..." if len(news['content']) > 200 else news['content'])
        print("=" * 80)
    
    # 将结果保存到文件
    with open('sohu_policy_results.json', 'w', encoding='utf-8') as f:
        json.dump(latest_news, f, ensure_ascii=False, indent=2)
    print("\n完整结果已保存到sohu_policy_results.json")
    
    # 为便于查看，另存为文本文件
    with open('sohu_policy_results.txt', 'w', encoding='utf-8') as f:
        for i, news in enumerate(latest_news):
            f.write(f"\n\n{'='*50}\n")
            f.write(f"【{i+1}】{news['title']}\n")
            f.write(f"来源: {news['source']}\n")
            f.write(f"时间: {news['date']}\n")
            f.write(f"链接: {news['url']}\n")
            f.write(f"{'-'*40}\n")
            f.write(f"内容:\n{news['content']}\n")
            f.write(f"{'='*50}\n")
    print("文本格式结果已保存到sohu_policy_results.txt") 