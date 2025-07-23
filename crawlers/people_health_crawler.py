#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
人民网健康栏目爬虫
"""

import requests
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Blueprint

# 创建蓝图
people_health_bp = Blueprint('people_health', __name__)

class PeopleHealthCrawler:
    """
    人民网健康栏目爬虫类
    """
    
    def __init__(self):
        """
        初始化
        """
        self.name = "人民网健康栏目"
        self.base_url = "http://health.people.com.cn/"
        
        # 设置请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Referer': 'http://health.people.com.cn/'
        }
        
        # 初始化Cookies
        self.cookies = {}
    
    def get_topic_news(self):
        """获取首页topicNews下的大标题"""
        try:
            # 发送请求
            print(f"正在获取人民网健康首页: {self.base_url}")
            response = requests.get(
                self.base_url,
                headers=self.headers,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"获取首页失败，状态码: {response.status_code}")
                return None
            
            # 设置正确的编码
            response.encoding = 'utf-8'
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找topicNews区域下的大标题
            # 可能有多种选择器，根据实际HTML结构调整
            topic_title = None
            topic_url = None
            
            # 方法1: 通过页面结构定位大标题
            # 根据人民网健康页面特征，大标题通常位于显著位置
            headline_tags = soup.select('h1 a, h2 a, h3 a, div.headLine a')
            for headline in headline_tags:
                if headline and headline.text.strip():
                    topic_title = headline.text.strip()
                    topic_url = headline.get('href')
                    # 找到第一个非空标题就退出
                    break
            
            # 另一种尝试：针对人民网特定结构
            if not topic_title:
                front_titles = soup.select('.front-title a, .focus-title a')
                if front_titles:
                    for title in front_titles:
                        if title and title.text.strip():
                            topic_title = title.text.strip()
                            topic_url = title.get('href')
                            break
            
            # 直接查找首页大标题栏目
            if not topic_title:
                headline_div = soup.find('div', id='rmw_headline') or soup.find('div', class_='rmw_headline')
                if headline_div:
                    headline_link = headline_div.find('a')
                    if headline_link:
                        topic_title = headline_link.text.strip() 
                        topic_url = headline_link.get('href')
            
            # 确保URL是绝对路径
            if topic_url and not topic_url.startswith('http'):
                if topic_url.startswith('//'):
                    topic_url = 'http:' + topic_url
                elif topic_url.startswith('/'):
                    topic_url = f"http://health.people.com.cn{topic_url}"
                else:
                    topic_url = f"http://health.people.com.cn/{topic_url}"
            
            # 如果找到标题，返回结果
            if topic_title:
                return {
                    'title': topic_title,
                    'url': topic_url
                }
            
            # 如果没有找到任何标题，返回None
            return None
            
        except Exception as e:
            print(f"获取首页大标题出错: {str(e)}")
            return None
    
    def get_article_detail(self, article_url):
        """获取文章详细内容"""
        if not article_url:
            return None
            
        try:
            print(f"正在获取文章详情: {article_url}")
            
            # 发送请求
            response = requests.get(
                article_url,
                headers=self.headers,
                timeout=15
            )
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"获取文章详情失败，状态码: {response.status_code}")
                return None
            
            # 设置正确的编码
            response.encoding = 'utf-8'
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章详情
            article_data = {}
            
            # 提取文章标题
            title = soup.select_one('h1.title, h1.article_title')
            if title:
                article_data['title'] = title.get_text(strip=True)
            
            # 提取文章日期和来源
            source_info = soup.select_one('.box01_title .fl, .artOri, .article_info .date')
            if source_info:
                info_text = source_info.get_text(strip=True)
                
                # 尝试提取日期
                date_match = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', info_text)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        # 将日期转换为标准格式
                        date = datetime.strptime(date_str, '%Y年%m月%d日')
                        article_data['date'] = date.strftime('%Y-%m-%d')
                    except:
                        article_data['date'] = date_str
                
                # 尝试提取来源
                source_match = re.search(r'来源[:：]\s*(.+?)(?=\d|$)', info_text)
                if source_match:
                    article_data['source'] = source_match.group(1).strip()
                else:
                    # 尝试其他方式获取来源
                    source_elem = soup.select_one('.box01_title .source, .article_info .source')
                    if source_elem:
                        article_data['source'] = source_elem.get_text(strip=True).replace('来源：', '')
                    else:
                        article_data['source'] = '人民网健康'
            else:
                article_data['date'] = datetime.now().strftime('%Y-%m-%d')
                article_data['source'] = '人民网健康'
            
            # 提取文章内容
            content = ""
            
            # 尝试多种可能的内容选择器
            content_selectors = [
                '.box_con p',  # 常见内容区域
                '#rwb_zw p',   # 人民网常用ID
                '.content p',  # 通用类名
                '.article_content p',  # 文章内容
                '.artDet p'    # 另一种常见类名
            ]
            
            for selector in content_selectors:
                content_elements = soup.select(selector)
                if content_elements:
                    for p in content_elements:
                        p_text = p.get_text(strip=True)
                        if p_text:
                            content += p_text + "\n\n"
                    break  # 找到内容后跳出循环
            
            article_data['content'] = content.strip()
            
            return article_data
            
        except Exception as e:
            print(f"获取文章详情出错: {str(e)}")
            return None
    
    def crawl(self):
        """爬取文章主函数"""
        try:
            # 获取topicNews大标题
            topic_news = self.get_topic_news()
            
            if not topic_news:
                return {
                    "status": "success",
                    "message": "未找到人民网健康首页大标题",
                    "data": {}
                }
            
            # 获取文章详情
            article_url = topic_news.get('url')
            article_detail = self.get_article_detail(article_url)
            
            # 整合信息
            result = topic_news
            if article_detail:
                # 使用详情页的标题（可能更完整）
                if 'title' in article_detail:
                    result['title'] = article_detail['title']
                
                # 添加日期、来源和内容
                if 'date' in article_detail:
                    result['date'] = article_detail['date']
                if 'source' in article_detail:
                    result['source'] = article_detail['source']
                if 'content' in article_detail:
                    result['content'] = article_detail['content']
            
            return {
                "status": "success",
                "message": "成功获取人民网健康首页大标题",
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"爬取人民网健康首页大标题出错: {str(e)}",
                "data": {}
            }

@people_health_bp.route('/people_health_topic', methods=['GET'])
def get_people_health_topic():
    """获取人民网健康首页大标题接口"""
    try:
        crawler = PeopleHealthCrawler()
        result = crawler.crawl()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取人民网健康首页大标题失败: {str(e)}",
            "data": {}
        }

# 测试代码
if __name__ == "__main__":
    crawler = PeopleHealthCrawler()
    result = crawler.crawl()
    print(json.dumps(result, ensure_ascii=False, indent=2)) 