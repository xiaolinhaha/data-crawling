#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
搜狐金融快讯爬虫
"""

import time
import json
import requests
import random
from bs4 import BeautifulSoup
from datetime import datetime
import re
from flask import Blueprint, request

# 创建蓝图
sohu_finance_bp = Blueprint('sohu_finance', __name__)

class SohuFinanceCrawler:
    """
    搜狐金融快讯爬虫类
    """

    def __init__(self):
        """
        初始化
        """
        self.website_name = "搜狐金融快讯"
        self.website_url = "https://www.sohu.com/xtopic/TURBeE1qUXlNall3"
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://www.sohu.com',
            'Referer': 'https://www.sohu.com/xtopic/TURBeE1qUXlNall3',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        # 初始化cookies
        self.cookies = {}
        
    def refresh_cookies(self):
        """
        自动刷新Cookie
        """
        try:
            print("开始自动刷新搜狐金融Cookie...")
            
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
            
            # 步骤1: 访问搜狐首页
            home_url = "https://www.sohu.com/"
            print(f"1. 访问搜狐首页: {home_url}")
            
            home_response = session.get(home_url, headers=basic_headers, timeout=15)
            print(f"首页响应状态码: {home_response.status_code}")
            print(f"获取到的Cookie: {session.cookies.get_dict()}")
            
            # 随机延迟，模拟人类行为
            time.sleep(random.uniform(1, 2))
            
            # 步骤2: 访问搜狐金融快讯主题页
            print(f"2. 访问金融快讯主题页: {self.website_url}")
            
            list_response = session.get(self.website_url, headers=basic_headers, timeout=15)
            print(f"主题页响应状态码: {list_response.status_code}")
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

    def get_latest_news(self):
        """
        获取最新的财经快讯
        
        Returns:
            dict: 最新的财经快讯数据
        """
        try:
            # 爬取搜狐金融快讯
            news_data = self.crawl_sohu_finance()
            
            # 如果获取失败，尝试刷新Cookie后重试
            if not news_data or 'error' in news_data:
                print("初次获取财经快讯失败，尝试刷新Cookie...")
                if self.refresh_cookies():
                    print("使用刷新后的Cookie重新获取财经快讯...")
                    news_data = self.crawl_sohu_finance()
            
            return news_data
        except Exception as e:
            print(f"获取最新财经快讯出错: {str(e)}")
            return {
                'Website_Name': self.website_name,
                'Website_URL': self.website_url,
                'error': f'获取最新财经快讯出错: {str(e)}'
            }

    def crawl_sohu_finance(self):
        """
        爬取搜狐金融快讯
        
        Returns:
            dict: 爬取的文章数据
        """
        try:
            # 发送请求获取列表数据
            url = 'https://odin.sohu.com/odin/api/blockdata'
            payload = {
                "pvId": f"{int(time.time() * 1000)}_fwGOGoy",
                "pageId": f"{int(time.time() * 1000)}_24120412123_3p4",
                "mainContent": {
                    "productType": "15",
                    "productId": "1242260",
                    "secureScore": "100",
                    "categoryId": "15",
                    "adTags": "11111111",
                    "authorId": 120325367
                },
                "resourceList": [
                    {
                        "tplCompKey": "TPLFeed_1_1_pc_1644567115421",
                        "isServerRender": True,
                        "isSingleAd": False,
                        "content": {
                            "spm": "smpc.topic_192.block2_218_84Noj1_1_fd",
                            "productType": "15",
                            "productId": "1242260",
                            "page": 1,
                            "size": 20,
                            "pro": "0,1",
                            "innerTag": "topic",
                            "feedType": "XTOPIC_LATEST",
                            "view": "multiFeedMode",
                            "requestId": f"{int(time.time() * 1000)}lL3XqmW_1242260"
                        },
                        "adInfo": {"posCode": ""},
                        "context": {}
                    }
                ]
            }
            
            # 创建会话并设置cookies
            session = requests.Session()
            if self.cookies:
                for key, value in self.cookies.items():
                    session.cookies.set(key, value)
            
            response = session.post(url, headers=self.headers, json=payload)
            response_json = response.json()
            
            # 提取列表数据
            news_list = response_json['data']['TPLFeed_1_1_pc_1644567115421']['list']
            
            # 获取第一篇文章的数据
            if len(news_list) > 0:
                first_news = news_list[0]
                news_title = first_news['title']
                news_url = f"https://www.sohu.com{first_news['url'].split('?')[0]}"
                news_time = first_news['extraInfo']
                news_brief = first_news['brief']
                
                # 检查文章发布时间是否在24小时内
                print(f"获取到的文章发布时间: {news_time}")
                
                try:
                    # 尝试解析发布时间
                    # 搜狐时间格式通常为：'04-11 17:48' 或 '2024-04-11 17:48'
                    if re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}', news_time):
                        # 如果格式是 MM-DD HH:MM，添加当前年份
                        current_year = datetime.now().year
                        news_datetime = datetime.strptime(f"{current_year}-{news_time}", "%Y-%m-%d %H:%M")
                    elif re.match(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', news_time):
                        # 如果格式是 YYYY-MM-DD HH:MM
                        news_datetime = datetime.strptime(news_time, "%Y-%m-%d %H:%M")
                    else:
                        # 其他格式，尝试通用解析
                        news_datetime = datetime.strptime(news_time, "%Y-%m-%d %H:%M:%S")
                    
                    # 计算时间差
                    current_time = datetime.now()
                    time_diff = current_time - news_datetime
                    
                    # 如果文章发布时间超过24小时，返回空结果
                    if time_diff.days >= 1:
                        print(f"文章发布时间({news_time})不在过去24小时内，返回空结果")
                        return {
                            'Website_Name': self.website_name,
                            'Website_URL': self.website_url,
                            'not_in_24h': True
                        }
                    
                    print(f"文章发布于过去24小时内({news_time})，继续获取详情")
                except Exception as e:
                    print(f"解析发布时间出错: {str(e)}，将继续获取文章详情")
                    # 如果解析出错，继续获取详情
                
                # 获取文章详情
                detail_content = self.get_sohu_article_detail(news_url)
                
                # 如果获取详情失败，尝试刷新Cookie后重试
                if not detail_content or detail_content == "无法获取文章内容" or "获取文章详情出错" in detail_content:
                    print("获取文章详情失败，尝试刷新Cookie...")
                    if self.refresh_cookies():
                        print("使用刷新后的Cookie重新获取文章详情...")
                        detail_content = self.get_sohu_article_detail(news_url)
                
                news_data = {
                    'Website_Name': self.website_name,
                    'Website_URL': self.website_url,
                    'Article_Title': news_title,
                    'Article_URL': news_url,
                    'Article_Brief': news_brief,
                    'Article_Content': detail_content,
                    'Article_Pub_Date': news_time,
                    'Crawl_Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                return news_data
            else:
                return {
                    'Website_Name': self.website_name,
                    'Website_URL': self.website_url,
                    'error': '未获取到文章列表'
                }
        except Exception as e:
            print(f"爬取搜狐金融快讯出错: {str(e)}")
            return {
                'Website_Name': self.website_name,
                'Website_URL': self.website_url,
                'error': f'爬取过程中出错: {str(e)}'
            }

    def get_sohu_article_detail(self, url):
        """
        获取搜狐文章详情
        
        Args:
            url (str): 文章URL
            
        Returns:
            str: 文章内容
        """
        try:
            # 创建会话并设置cookies
            session = requests.Session()
            if self.cookies:
                for key, value in self.cookies.items():
                    session.cookies.set(key, value)
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9'
            }
            
            response = session.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找文章内容
            article = soup.find('article', {'class': 'article', 'id': 'mp-editor'})
            
            if article:
                # 删除文章中的图片元素
                for img in article.find_all('img'):
                    img.decompose()
                    
                # 删除返回搜狐查看更多的链接
                for a in article.find_all('a', id='backsohucom'):
                    a.decompose()
                
                # 获取文本内容
                content = article.get_text(strip=True)
                
                # 清理文本内容
                content = re.sub(r'\s+', ' ', content)
                
                return content
            else:
                return "无法获取文章内容"
        except Exception as e:
            return f"获取文章详情出错: {str(e)}"

@sohu_finance_bp.route('/sohu_finance_news', methods=['GET'])
def get_sohu_finance_news():
    """获取搜狐金融快讯"""
    try:
        crawler = SohuFinanceCrawler()
        news_data = crawler.get_latest_news()
        
        if 'error' in news_data:
            return {
                "status": "error",
                "message": news_data['error'],
                "data": None
            }
        
        # 检查是否是因为没有24小时内的文章而返回
        if 'not_in_24h' in news_data and news_data['not_in_24h']:
            return {
                "status": "success",
                "message": "没有24小时内的新文章",
                "data": None
            }
        
        result = {
            'title': news_data['Article_Title'],
            'url': news_data['Article_URL'],
            'source': news_data['Website_Name'],
            'date': news_data['Article_Pub_Date'],
            'content': news_data['Article_Content']
        }
        
        return {
            "status": "success",
            "message": "成功获取搜狐金融快讯",
            "data": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取搜狐金融快讯失败: {str(e)}",
            "data": None
        }


# 测试代码
if __name__ == "__main__":
    crawler = SohuFinanceCrawler()
    news = crawler.get_latest_news()
    print(json.dumps(news, ensure_ascii=False, indent=4)) 