#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
中国金融网风险揭示新闻爬虫
"""

import requests
import json
import re
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
import random
from bs4 import BeautifulSoup

# 创建蓝图
cnfin_risk_bp = Blueprint('cnfin_risk', __name__)

class CnfinRiskCrawler:
    """
    中国金融网风险揭示新闻爬虫类
    """

    def __init__(self):
        """
        初始化
        """
        self.name = "中国金融网风险揭示"
        self.list_url = "https://edu.cnfin.com/tj/1352083692251512832.html"
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def get_news_list(self):
        """
        获取风险揭示列表页的新闻
        """
        try:
            # 添加随机延迟
            time.sleep(random.uniform(0.5, 1))
            
            # 发送请求获取列表页
            response = requests.get(self.list_url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return []
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取新闻列表
            news_items = []
            
            # 查找列表区域下的文章项
            list_box = soup.select_one('.list_box')
            if list_box:
                article_items = list_box.select('.article-item')
                
                if article_items:
                    # 只处理第一条（最新的）文章
                    item = article_items[0]
                    try:
                        # 查找a标签
                        link_tag = item.select_one('a')
                        if link_tag:
                            # 从a标签中提取信息
                            url = link_tag.get('href', '')
                            title = ''
                            
                            # 优先从data-title属性获取标题
                            if link_tag.has_attr('data-title'):
                                title = link_tag.get('data-title', '')
                            # 其次从h2标签获取标题
                            elif link_tag.select_one('h2'):
                                title = link_tag.select_one('h2').get_text().strip()
                            # 最后直接获取a标签文本
                            else:
                                title = link_tag.get_text().strip()
                            
                            # 获取日期和来源
                            pub_date = link_tag.get('data-publishDate', '')
                            source = link_tag.get('data-externalSource', '')
                            
                            # 确保URL是完整的
                            if url and not url.startswith('http'):
                                if url.startswith('/'):
                                    url = f"https://edu.cnfin.com{url}"
                                else:
                                    url = f"https://edu.cnfin.com/{url}"
                            
                            news_items.append({
                                'title': title,
                                'url': url,
                                'date': pub_date,
                                'source': source
                            })
                    except Exception:
                        pass
            
            # 如果没有找到新闻，尝试旧的方法
            if not news_items:
                # 查找所有article-item元素
                article_items = soup.select('.article-item')
                
                if article_items and len(article_items) > 0:
                    # 只处理第一条（最新的）文章
                    item = article_items[0]
                    try:
                        # 查找a标签
                        link_tag = item.select_one('a')
                        if link_tag:
                            # 从a标签中提取信息
                            url = link_tag.get('href', '')
                            title = ''
                            
                            # 优先从data-title属性获取标题
                            if link_tag.has_attr('data-title'):
                                title = link_tag.get('data-title', '')
                            # 其次从h2标签获取标题
                            elif link_tag.select_one('h2'):
                                title = link_tag.select_one('h2').get_text().strip()
                            # 最后直接获取a标签文本
                            else:
                                title = link_tag.get_text().strip()
                            
                            # 获取日期和来源
                            pub_date = link_tag.get('data-publishDate', '')
                            source = link_tag.get('data-externalSource', '')
                            
                            # 确保URL是完整的
                            if url and not url.startswith('http'):
                                if url.startswith('/'):
                                    url = f"https://edu.cnfin.com{url}"
                                else:
                                    url = f"https://edu.cnfin.com/{url}"
                            
                            news_items.append({
                                'title': title,
                                'url': url,
                                'date': pub_date,
                                'source': source
                            })
                    except Exception:
                        pass
            
            return news_items
            
        except Exception:
            return []
    
    def get_article_detail(self, url):
        """
        获取文章详情
        """
        if not url:
            return None
        
        try:
            # 添加随机延迟
            time.sleep(random.uniform(0.5, 1))
            
            # 发送请求获取详情页
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return None
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文章内容
            article_info = {}
            
            # 标题 - 尝试从title-text类获取标题
            title_tag = soup.select_one('.title-text') or soup.select_one('.article h1') or soup.select_one('h1.title')
            if title_tag:
                article_info['title'] = title_tag.get_text().strip()
            
            # 发布日期和来源 - 从source-msg中提取
            source_msg = soup.select_one('.source-msg')
            if source_msg:
                text = source_msg.get_text().strip()
                
                # 提取来源
                source_match = re.search(r'来源：(.+?)[\s\d]', text)
                if source_match:
                    article_info['source'] = source_match.group(1).strip()
                
                # 提取日期
                date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', text)
                if not date_match:
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', text)
                if date_match:
                    article_info['date'] = date_match.group(1).strip()
            
            # 如果上面没有找到来源，使用默认值
            if 'source' not in article_info:
                article_info['source'] = '中国金融网'
            
            # 如果上面没有找到日期，尝试其他方法
            if 'date' not in article_info:
                # 在HTML内容中查找日期
                date_patterns = [
                    r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
                    r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})',
                    r'(\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{1,2})',
                    r'(\d{4}-\d{2}-\d{2})'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        article_info['date'] = match.group(1)
                        break
            
            # 正文内容 - 尝试从detail-contents获取
            content_div = soup.select_one('.detail-contents')
            if content_div:
                # 移除不需要的元素
                for element in content_div.select('.title-text, .source-msg, .share-article, .article-images, script, style'):
                    element.extract()
                
                # 获取剩余文本内容
                content_text = content_div.get_text().strip()
                article_info['content'] = content_text
            else:
                # 尝试其他可能的内容选择器
                content_div = soup.select_one('.article-cont') or soup.select_one('.article-content') or soup.select_one('.content')
                if content_div:
                    # 移除不需要的元素
                    for element in content_div.select('script, style'):
                        element.extract()
                    
                    content_text = content_div.get_text().strip()
                    article_info['content'] = content_text
            
            return article_info
            
        except Exception:
            return None
    
    def is_within_24_hours(self, date_str):
        """
        判断给定的日期字符串是否在当前时间的过去24小时内
        """
        if not date_str:
            return False
        
        try:
            # 尝试解析多种日期格式
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%Y年%m月%d日 %H:%M:%S',
                '%Y年%m月%d日 %H:%M',
                '%Y年%m月%d日',
                '%m-%d %H:%M'
            ]
            
            parsed_date = None
            for date_format in date_formats:
                try:
                    if '%Y' not in date_format and date_str.count('-') == 1:
                        # 对于只有月日的格式，添加当前年份
                        current_year = datetime.now().year
                        date_str_with_year = f"{current_year}-{date_str}"
                        parsed_date = datetime.strptime(date_str_with_year, date_format.replace('%m', '%Y-%m'))
                    else:
                        parsed_date = datetime.strptime(date_str, date_format)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                # 尝试匹配"X小时前"、"X分钟前"等相对时间格式
                if '小时前' in date_str:
                    hours = int(re.search(r'(\d+)\s*小时前', date_str).group(1))
                    parsed_date = datetime.now() - timedelta(hours=hours)
                elif '分钟前' in date_str:
                    minutes = int(re.search(r'(\d+)\s*分钟前', date_str).group(1))
                    parsed_date = datetime.now() - timedelta(minutes=minutes)
                elif '刚刚' in date_str:
                    parsed_date = datetime.now()
                elif '昨天' in date_str:
                    time_part = re.search(r'昨天\s*(\d+:\d+)', date_str)
                    if time_part:
                        time_str = time_part.group(1)
                        hour, minute = map(int, time_str.split(':'))
                        parsed_date = datetime.now() - timedelta(days=1)
                        parsed_date = parsed_date.replace(hour=hour, minute=minute)
                    else:
                        parsed_date = datetime.now() - timedelta(days=1)
                else:
                    # 如果以上都不匹配，则尝试从字符串中提取日期部分
                    date_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', date_str)
                    if date_match:
                        date_part = date_match.group(1)
                        parsed_date = datetime.strptime(date_part, '%Y-%m-%d')
            
            if not parsed_date:
                return False
            
            # 获取当前日期(年月日)
            today = datetime.now().date()
            # 获取文章日期(年月日)
            article_date = parsed_date.date()
            
            # 判断是否为当天发布
            return article_date == today
            
        except Exception:
            return False
    
    def get_latest_news(self):
        """
        获取最新的一条新闻
        """
        try:
            news_list = self.get_news_list()
            
            if not news_list:
                return None
            
            # 获取第一条新闻（最新的一条）
            latest_news = news_list[0]
            
            # 检查日期是否是当天发布的
            if 'date' in latest_news and latest_news['date']:
                is_today = self.is_within_24_hours(latest_news['date'])
                
                if not is_today:
                    return None
            
            # 获取文章详情
            if 'url' in latest_news and latest_news['url']:
                article_detail = self.get_article_detail(latest_news['url'])
                
                if article_detail:
                    # 整合信息
                    result = {
                        'title': article_detail.get('title', latest_news['title']),
                        'url': latest_news['url'],
                        'source': article_detail.get('source', '中国金融网'),
                        'date': article_detail.get('date', latest_news.get('date', '')),
                        'content': article_detail.get('content', '')
                    }
                    
                    # 再次检查详情页的日期是否是当天发布的
                    if 'date' in result and result['date'] and not self.is_within_24_hours(result['date']):
                        return None
                    
                    return result
            
            return None
        except Exception:
            return None
    
    def crawl(self):
        """
        执行爬虫，获取最新的风险揭示新闻
        """
        try:
            latest_news = self.get_latest_news()
            
            if not latest_news:
                # 如果没有找到当天发布的新闻，返回空数据
                return {
                    "status": "success",
                    "message": "未找到当天发布的风险揭示新闻",
                    "data": None
                }
            
            return {
                "status": "success",
                "message": "成功获取中国金融网风险揭示新闻",
                "data": latest_news
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }

@cnfin_risk_bp.route('/cnfin_risk_news', methods=['GET'])
def get_cnfin_risk_news():
    """获取中国金融网风险揭示新闻"""
    try:
        crawler = CnfinRiskCrawler()
        result = crawler.crawl()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": None
        })

# 测试代码
if __name__ == "__main__":
    # 创建爬虫实例
    crawler = CnfinRiskCrawler()
    
    # 获取并打印最新的风险揭示新闻
    result = crawler.crawl()
    print(json.dumps(result, ensure_ascii=False, indent=2))