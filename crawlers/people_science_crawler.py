#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
人民网科普版块爬虫
"""

import requests
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Blueprint

# 创建蓝图
people_science_bp = Blueprint('people_science', __name__)

class PeopleScienceCrawler:
    """
    人民网科普版块爬虫类
    """
    
    def __init__(self):
        """
        初始化
        """
        self.name = "人民网科普版块"
        self.base_url = "http://kpzg.people.com.cn/"
        
        # 设置请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Referer': 'http://kpzg.people.com.cn/'
        }
        
        # 初始化Cookies
        self.cookies = {}
    
    def get_main_headline(self):
        """获取首页mainNews下的大标题"""
        try:
            # 发送请求
            print(f"正在获取人民网科普版块首页: {self.base_url}")
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
            
            # 查找首页mainNews下的大标题
            main_news = soup.select_one('.mainNews') or soup.select_one('#mainNews')
            
            if not main_news:
                print("未找到mainNews区域")
                # 如果没找到mainNews，尝试找其他特殊标记或位置的大标题
                headline = soup.select_one('.headline') or soup.select_one('h1') or soup.select_one('h2.title')
            else:
                # 从mainNews区域中查找大标题
                headline = main_news.select_one('h1') or main_news.select_one('h2') or main_news.select_one('a.title')
                
                # 如果在mainNews中没找到明确的标题标签，尝试提取第一个明显的链接
                if not headline:
                    links = main_news.select('a')
                    for link in links:
                        if link.get_text(strip=True) and len(link.get_text(strip=True)) > 10:
                            headline = link
                            break
            
            # 如果还是没找到大标题，尝试根据页面当前结构中看到的特征寻找
            if not headline:
                print("尝试查找页面特征...")
                # 根据网页搜索结果显示的标题位置特征查找
                headline = soup.select_one('h1.title') or soup.select_one('div.front-title a')
            
            # 如果仍然没有找到大标题，返回None
            if not headline:
                print("未找到首页大标题")
                return None
            
            # 提取标题文本和链接
            title_text = None
            title_url = None
            
            # 如果标题本身就是链接
            if headline.name == 'a':
                title_text = headline.get_text(strip=True)
                title_url = headline.get('href')
            # 如果标题包含链接
            elif headline.find('a'):
                title_link = headline.find('a')
                title_text = title_link.get_text(strip=True)
                title_url = title_link.get('href')
            # 如果只有标题文本
            else:
                title_text = headline.get_text(strip=True)
                # 尝试在父元素中找链接
                parent = headline.parent
                if parent and parent.name == 'a':
                    title_url = parent.get('href')
                elif parent and parent.find('a'):
                    title_url = parent.find('a').get('href')
            
            # 确保URL是绝对路径
            if title_url and not title_url.startswith('http'):
                if title_url.startswith('//'):
                    title_url = 'http:' + title_url
                elif title_url.startswith('/'):
                    title_url = f"http://kpzg.people.com.cn{title_url}"
                else:
                    title_url = f"http://kpzg.people.com.cn/{title_url}"
            
            # 如果找到标题，返回结果
            if title_text:
                print(f"找到大标题: {title_text}")
                return {
                    'title': title_text,
                    'url': title_url
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
            title = soup.select_one('h1.title, h1.article_title, div.text_title h1, .title_con h1')
            if title:
                article_data['title'] = title.get_text(strip=True)
            
            # 提取文章日期和来源
            # 尝试多种常见格式
            source_info = None
            for selector in ['.box01_title .fl', '.artOri', '.article_info .date', '.page_c .fl', '.info']:
                source_info = soup.select_one(selector)
                if source_info:
                    break
            
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
                    for selector in ['.box01_title .source', '.article_info .source', '.info .source', '.page_c .source']:
                        source_elem = soup.select_one(selector)
                        if source_elem:
                            article_data['source'] = source_elem.get_text(strip=True).replace('来源：', '')
                            break
                    if 'source' not in article_data:
                        article_data['source'] = '人民网科普'
            else:
                article_data['date'] = datetime.now().strftime('%Y-%m-%d')
                article_data['source'] = '人民网科普'
            
            # 提取文章内容
            content = ""
            
            # 尝试多种可能的内容选择器
            content_selectors = [
                '.box_con p',        # 常见内容区域
                '#rwb_zw p',         # 人民网常用ID
                '.content p',        # 通用类名
                '.article_content p', # 文章内容
                '.artDet p',         # 另一种常见类名
                '.text_con p',       # 人民网常见类名
                '.rm_txt_con p',     # 人民网另一种内容区域
                '.arttext p',        # 另一种文章区域
                'div.text p'         # 通用内容
            ]
            
            for selector in content_selectors:
                content_elements = soup.select(selector)
                if content_elements:
                    for p in content_elements:
                        p_text = p.get_text(strip=True)
                        if p_text:
                            content += p_text + "\n\n"
                    # 找到内容后跳出循环
                    if content.strip():
                        break
            
            # 如果常规选择器没有找到内容，尝试整体获取
            if not content.strip():
                print("尝试其他方法获取文章内容...")
                # 尝试获取整个内容区域的文本
                content_area = None
                for selector in ['#rwb_zw', '.text_con', '.content', '.article_content', '.artDet']:
                    content_area = soup.select_one(selector)
                    if content_area:
                        # 获取内容区域中的所有文本，过滤掉脚本和样式
                        for tag in content_area.find_all(['script', 'style']):
                            tag.decompose()
                        
                        # 获取内容
                        content = content_area.get_text(separator="\n", strip=True)
                        # 去除多余的空行
                        content = re.sub(r'\n{3,}', '\n\n', content)
                        break
            
            article_data['content'] = content.strip()
            
            return article_data
            
        except Exception as e:
            print(f"获取文章详情出错: {str(e)}")
            return None
    
    def crawl(self):
        """爬取文章主函数"""
        try:
            # 获取首页大标题
            headline = self.get_main_headline()
            
            if not headline:
                return {
                    "status": "success",
                    "message": "未找到人民网科普版块首页大标题",
                    "data": {}
                }
            
            # 获取文章详情
            article_url = headline.get('url')
            article_detail = self.get_article_detail(article_url)
            
            # 整合信息
            result = headline
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
                "message": "成功获取人民网科普版块首页大标题",
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"爬取人民网科普版块首页大标题出错: {str(e)}",
                "data": {}
            }

@people_science_bp.route('/people_science_headline', methods=['GET'])
def get_people_science_headline():
    """获取人民网科普版块首页大标题接口"""
    try:
        crawler = PeopleScienceCrawler()
        result = crawler.crawl()
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"获取人民网科普版块首页大标题失败: {str(e)}",
            "data": {}
        }

# 测试代码
if __name__ == "__main__":
    crawler = PeopleScienceCrawler()
    result = crawler.crawl()
    print(json.dumps(result, ensure_ascii=False, indent=2)) 