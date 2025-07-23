#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CCTV反诈新闻爬虫
"""

import requests
import json
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
import re
from bs4 import BeautifulSoup
import urllib.parse
import random
import os
import pickle
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from fake_useragent import UserAgent
import threading

# 配置日志
logging.basicConfig(
    level=logging.CRITICAL,  # 设置日志级别为CRITICAL，实质上关闭大部分日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 移除文件日志处理器，只保留控制台日志
    ]
)
logger = logging.getLogger("CCTVAntifraudCrawler")

# 创建蓝图
eastmoney_antifraud_bp = Blueprint('eastmoney_antifraud', __name__)

# 用户代理池
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0'
]

# 线程局部存储，确保每个线程有自己的会话对象
thread_local = threading.local()

class CCTVAntifraudCrawler:
    """
    CCTV反诈新闻爬虫类 - 优化版，减少日志输出和文件I/O
    """

    def __init__(self):
        """
        初始化
        """
        self.name = "CCTV反诈新闻"
        self.search_url = "https://search.cctv.cn/search.php"
        # 添加备用URL
        self.backup_urls = [
            "https://www.cctv.com/2019/07/gaoxiao/antifraud.shtml",
            "https://news.cctv.com/anti-fraud/",
            "https://news.cctv.com/special/special/index.shtml?topic=anti"
        ]
        
        # 初始化fake_useragent
        try:
            self.ua = UserAgent(fallback=random.choice(USER_AGENTS))
        except:
            # 如果无法初始化fake_useragent，使用预定义的用户代理
            self.ua = None
        
        # 请求头设置 - 更加真实的浏览器请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Referer': 'https://search.cctv.cn/',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 初始化cookies
        self.cookies = {}
        # 尝试加载cookies，但不显示日志
        self.load_cookies()
        
        # 上次成功请求的时间
        self.last_request_time = 0
        # 请求之间的最小间隔(秒)
        self.min_request_interval = 3
        # 最大重试次数
        self.max_retries = 5
        # 实际使用的备用URL索引
        self.current_backup_url_index = 0
        # 搜索参数
        self.search_params = {
            'qtext': '防骗 反诈',  # 搜索关键词
            'page': '1',
            'type': 'web',
            'sort': 'date',
            'datepid': '1',  # 只获取今天的内容
            'channel': '',
            'vtime': '-1',
            'is_search': '1',
            'pageSize': '20'  # 搜索结果数量
        }
        
        # 新闻缓存
        self.news_cache = {}
        self.cache_expiry = 900  # 缓存有效期15分钟
        self.last_cache_time = 0
        
        # 初始化logger
        self.logger = logger
    
    def get_session(self):
        """
        获取或创建一个带有重试机制的requests.Session对象
        """
        if not hasattr(thread_local, "session"):
            session = requests.Session()
            
            # 配置重试策略
            retry_strategy = Retry(
                total=5,  # 总共重试5次
                backoff_factor=0.5,  # 重试间隔 = {backoff factor} * (2 ** ({number of previous retries}))
                status_forcelist=[429, 500, 502, 503, 504],  # 遇到这些状态码时重试
                allowed_methods=["GET", "POST", "HEAD"]  # 允许重试的HTTP方法
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # 设置cookies
            if self.cookies:
                session.cookies.update(self.cookies)
                
            thread_local.session = session
            
        return thread_local.session
    
    def get_random_user_agent(self):
        """
        获取随机用户代理
        """
        try:
            if self.ua:
                return self.ua.random
        except Exception:
            # 不再记录警告日志，直接使用备用方案
            pass
        
        return random.choice(USER_AGENTS)
    
    def load_cookies(self):
        """
        从文件加载cookies - 简化版，不记录日志
        """
        # 直接初始化空cookies，不从文件读取
        self.cookies = {}
        
    def save_cookies(self, cookies):
        """
        更新cookies - 简化版，只在内存中保存
        """
        try:
            self.cookies.update(cookies)
        except Exception:
            pass
    
    def wait_between_requests(self):
        """
        请求之间等待一段时间，避免请求频率过高
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            # 计算需要等待的时间
            wait_time = self.min_request_interval - elapsed
            # 增加一些随机性
            wait_time += random.uniform(0.5, 2.0)
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def prepare_headers(self):
        """
        准备请求头，包括随机用户代理和其他动态头信息
        """
        headers = self.headers.copy()
        
        # 设置随机用户代理
        headers['User-Agent'] = self.get_random_user_agent()
        
        # 添加随机Accept-Language
        languages = [
            'zh-CN,zh;q=0.9,en;q=0.8',
            'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'zh-CN,zh;q=0.9',
            'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7'
        ]
        headers['Accept-Language'] = random.choice(languages)
        
        # 添加时间戳防止缓存
        headers['X-Timestamp'] = str(int(time.time()))
        
        return headers
    
    def is_content_valid(self, content):
        """
        检查获取的内容是否有效，例如是否包含验证码页面或空响应
        """
        if not content:
            return False
            
        # 检查内容长度
        if len(content) < 500:  # 内容太短可能不是有效页面
            return False
            
        # 检查是否包含验证码关键词
        captcha_keywords = ["验证码", "captcha", "验证", "安全验证", "人机识别"]
        for keyword in captcha_keywords:
            if keyword in content:
                return False
                
        # 检查是否包含错误页面关键词
        error_keywords = ["访问受限", "请求频繁", "请稍后再试", "服务暂时不可用", "blocked", "forbidden"]
        for keyword in error_keywords:
            if keyword in content:
                return False
                
        return True
        
    def get_current_backup_url(self):
        """
        获取当前备用URL，如果所有URL都尝试过，则重置索引
        """
        if self.current_backup_url_index >= len(self.backup_urls):
            self.current_backup_url_index = 0
            
        backup_url = self.backup_urls[self.current_backup_url_index]
        self.current_backup_url_index += 1
        return backup_url
    
    def check_cache_valid(self):
        """
        检查缓存是否有效
        """
        if not self.news_cache:
            return False
            
        current_time = time.time()
        if (current_time - self.last_cache_time) > self.cache_expiry:
            return False
            
        return True
        
    def search_antifraud_news(self):
        """
        搜索反诈相关新闻 - 优化版，减少日志输出
        """
        # 先检查缓存
        if self.check_cache_valid():
            return self.news_cache.get("news_items", [])
            
        # 初始化重试计数器
        retry_count = 0
        base_sleep_time = 1  # 基础等待时间(秒)
        
        while retry_count < self.max_retries:
            try:
                # 等待请求间隔
                self.wait_between_requests()
                
                # 随机化查询参数
                params = self.search_params.copy()
                params['t'] = int(time.time())  # 添加时间戳
                params['r'] = random.random()   # 添加随机数
                
                # 构建URL
                url = f"{self.search_url}?qtext={urllib.parse.quote('反诈')}&page=1&type=web&sort=date&datepid=1&channel=&vtime=-1&is_search=1&t={params['t']}&r={params['r']}"
                
                # 准备请求头
                headers = self.prepare_headers()
                
                # 获取session
                session = self.get_session()
                
                # 获取搜索结果页面
                response = session.get(
                    url, 
                    headers=headers, 
                    timeout=20,
                    allow_redirects=True
                )
                
                # 更新cookies
                self.save_cookies(response.cookies.get_dict())
                
                # 设置正确的编码
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    # 检查内容是否有效
                    if not self.is_content_valid(response.text):
                        # 不再输出警告日志
                        # logger.warning("响应内容无效，尝试使用备用URL")
                        retry_count += 1
                        time.sleep(base_sleep_time * (2 ** retry_count))  # 指数退避
                        continue
                    
                    # 解析HTML内容
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 找到所有的新闻条目（li class='image'）
                    li_elements = soup.find_all('li', class_='image')
                    
                    if not li_elements:
                        # 不再输出警告日志
                        # logger.warning("未找到新闻条目，尝试使用不同的选择器")
                        # 尝试其他可能的选择器
                        li_elements = (
                            soup.find_all('li', class_='item') or 
                            soup.find_all('div', class_='text_center') or
                            soup.find_all('div', class_='news-item')
                        )
                        
                        if not li_elements:
                            # 不再输出警告日志
                            # logger.warning("所有选择器均未找到新闻条目，尝试下一个重试")
                            retry_count += 1
                            time.sleep(base_sleep_time * (2 ** retry_count))  # 指数退避
                            continue
                    
                    # 提取新闻信息并按发布时间排序
                    news_items = []
                    for idx, li in enumerate(li_elements):
                        try:
                            # 查找标题部分，使用更通用的选择器
                            h3_element = li.find(['h3', 'h2', 'h4'], class_=['tit', 'title'])
                            a_element = None
                            
                            if h3_element:
                                # 尝试找到span和a元素
                                span_element = h3_element.find('span')
                                if span_element:
                                    a_element = span_element.find('a')
                                else:
                                    # 直接在h3中查找a
                                    a_element = h3_element.find('a')
                            else:
                                # 如果找不到h3，直接在li中查找a
                                a_element = li.find('a')
                            
                            if not a_element:
                                continue
                            
                            # 获取标题
                            title = a_element.get_text(strip=True) or a_element.get('title', '')
                            if not title:
                                continue
                            
                            # 获取链接
                            link = a_element.get('href')
                            if not link:
                                continue
                            
                            # 处理跳转链接
                            if 'link_p.php' in link:
                                target_match = re.search(r'targetpage=([^&]+)', link)
                                if target_match:
                                    real_url = urllib.parse.unquote(target_match.group(1))
                                    link = real_url
                            
                            # 获取内容预览
                            content_preview = ""
                            p_element = li.find('p', class_=['bre', 'desc', 'summary'])
                            if p_element:
                                # 获取所有文本内容，忽略图片
                                for element in p_element.contents:
                                    if isinstance(element, str):
                                        content_preview += element.strip()
                                    elif element.name != 'img':
                                        content_preview += element.get_text().strip()
                            
                            # 获取发布时间和来源
                            src_tim_div = li.find(['div', 'span'], class_=['src-tim', 'time', 'meta', 'info'])
                            publish_time = ""
                            source = ""
                            
                            if src_tim_div:
                                # 获取来源
                                src_span = src_tim_div.find(['span', 'div'], class_=['src', 'source'])
                                if src_span:
                                    source_text = src_span.get_text(strip=True)
                                    if '来源：' in source_text:
                                        source = source_text.replace('来源：', '')
                                    else:
                                        source = source_text
                                
                                # 获取发布时间
                                tim_span = src_tim_div.find(['span', 'div'], class_=['tim', 'time', 'date'])
                                if tim_span:
                                    time_text = tim_span.get_text(strip=True)
                                    # 尝试多种时间格式
                                    time_patterns = [
                                        r'发布时间：(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
                                        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
                                        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})',
                                        r'(\d{4}-\d{2}-\d{2})',
                                        r'(\d{2}-\d{2} \d{2}:\d{2})'
                                    ]
                                    
                                    for pattern in time_patterns:
                                        match = re.search(pattern, time_text)
                                        if match:
                                            time_str = match.group(1)
                                            # 处理不完整的时间格式
                                            if len(time_str) <= 10:  # 只有日期
                                                time_str += " 08:00:00"
                                            elif len(time_str) <= 16:  # 没有秒
                                                time_str += ":00"
                                                
                                            publish_time = time_str
                                            break
                            
                            # 如果没有找到发布时间，跳过此条目
                            if not publish_time:
                                current_year = datetime.now().year
                                # 使用当前时间作为默认时间
                                publish_time = f"{current_year}-{datetime.now().strftime('%m-%d %H:%M:%S')}"
                            
                            # 获取图片URL
                            image_url = ""
                            img_element = li.find('img')
                            if img_element and img_element.has_attr('src'):
                                image_url = img_element.get('src')
                                if not image_url.startswith('http'):
                                    image_url = f"https:{image_url}" if image_url.startswith('//') else f"https://search.cctv.cn/{image_url}"
                            
                            # 构建新闻项
                            news_item = {
                                'title': title,
                                'link': link,
                                'publish_time': publish_time,
                                'source': source,
                                'content_preview': content_preview,
                                'image_url': image_url
                            }
                            
                            news_items.append(news_item)
                            # 不再输出日志
                            # logger.info(f"成功解析第{idx+1}条新闻: {title}")
                        except Exception as e:
                            # 不再输出日志
                            # logger.error(f"解析新闻条目失败: {str(e)}")
                            continue
                    
                    # 按发布时间排序（最新的在前）
                    news_items.sort(key=lambda x: x['publish_time'], reverse=True)
                    
                    # 更新缓存
                    self.news_cache["news_items"] = news_items
                    self.last_cache_time = time.time()
                    
                    return news_items
                else:
                    # 不再输出警告日志
                    # logger.warning(f"搜索请求失败: HTTP状态码 {response.status_code}")
                    retry_count += 1
                    time.sleep(base_sleep_time * (2 ** retry_count))  # 指数退避
            except requests.exceptions.RequestException as e:
                # 不再输出日志
                # logger.error(f"请求异常: {str(e)}")
                retry_count += 1
                time.sleep(base_sleep_time * (2 ** retry_count))  # 指数退避
            except Exception as e:
                # 不再输出日志
                # logger.error(f"搜索反诈新闻失败: {str(e)}")
                retry_count += 1
                time.sleep(base_sleep_time * (2 ** retry_count))  # 指数退避
        
        # 所有重试都失败，尝试使用备用URL
        # logger.warning("主URL搜索失败，尝试使用备用URL")
        return self.search_backup_news()
    
    def is_today(self, time_str):
        """
        判断给定的时间字符串是否为今天
        
        Args:
            time_str: 时间字符串，格式为 'YYYY-MM-DD HH:MM:SS'
            
        Returns:
            bool: 是否是今天发布的
        """
        try:
            # 解析时间字符串
            publish_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            # 获取当前日期
            current_date = datetime.now()
            
            # 忽略年份，只比较月和日
            # 由于CCTV网站显示的年份是2025年，所以我们只比较月和日
            return (publish_time.month == current_date.month and 
                    publish_time.day == current_date.day)
        except Exception:
            return False
    
    def get_article_content(self, url):
        """
        获取文章详情 - 优化版，只提取正文内容
        """
        try:
            # 确保URL是完整的
            if not url.startswith('http'):
                url = f"https://{url}" if not url.startswith('//') else f"https:{url}"
            
            # 直接使用session提高连接复用效率
            session = requests.Session()
            
            # 减少重试次数，加快失败返回
            max_retries = 2
            for retry in range(max_retries):
                try:
                    # 减少随机延迟时间
                    time.sleep(0.2 + random.random() * 0.5)
                    
                    # 随机修改一些不重要的头信息，避免完全一致
                    headers = self.headers.copy()
                    if random.random() > 0.5:
                        headers['Accept-Language'] = 'zh-CN,zh;q=0.9,en;q=0.8'
                    
                    # 减少超时时间
                    response = session.get(
                        url, 
                        headers=headers, 
                        timeout=8,
                        allow_redirects=True
                    )
                    
                    if response.status_code == 200:
                        # 尝试检测编码
                        if response.encoding == 'ISO-8859-1':
                            response.encoding = 'utf-8'
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 移除导航栏、广告和无关内容
                        for nav in soup.find_all(['nav', 'header']):
                            nav.decompose()
                        
                        for ad in soup.find_all(class_=lambda x: x and ('ad' in x.lower() or 'banner' in x.lower() or 'nav' in x.lower())):
                            ad.decompose()
                        
                        # 移除可能的底部内容
                        for footer in soup.find_all(['footer', 'div'], class_=lambda x: x and ('footer' in x.lower() or 'bottom' in x.lower())):
                            footer.decompose()
                        
                        # 尝试直接找到文章内容区
                        content_div = None
                        
                        # CCTV网站特有的内容区选择器
                        main_content_selectors = [
                            '.trt_txt1', 
                            '.cnt_bd', 
                            '.col_w660',
                            '.body_area_trt',
                            '.text_con',
                            '.content'
                        ]
                        
                        for selector in main_content_selectors:
                            content_div = soup.select_one(selector)
                            if content_div:
                                # 只获取p标签内容，过滤掉其他元素
                                paragraphs = content_div.find_all('p')
                                if paragraphs:
                                    # 过滤掉太短的段落和可能的非正文内容
                                    filtered_paragraphs = []
                                    for p in paragraphs:
                                        text = p.get_text(strip=True)
                                        # 排除发布时间、来源等信息
                                        if (len(text) > 10 and 
                                            not text.startswith('发布时间') and 
                                            not text.startswith('来源') and
                                            not '编辑' in text[-15:] and
                                            not '责任编辑' in text):
                                            filtered_paragraphs.append(text)
                                    
                                    if filtered_paragraphs:
                                        return '\n\n'.join(filtered_paragraphs)
                        
                        # 如果第一种方法失败，尝试其他可能的内容区域
                        backup_selectors = [
                            'div.content_area',
                            'div.article-content',
                            'div.TRS_Editor',
                            'div.article',
                            'div#content',
                            'article'
                        ]
                        
                        for selector in backup_selectors:
                            content_div = soup.select_one(selector)
                            if content_div:
                                # 尝试获取p标签
                                paragraphs = content_div.find_all('p')
                                if paragraphs:
                                    # 过滤处理同上
                                    filtered_texts = []
                                    for p in paragraphs:
                                        text = p.get_text(strip=True)
                                        if (len(text) > 10 and 
                                            not text.startswith('发布时间') and 
                                            not text.startswith('来源') and
                                            not '编辑' in text[-15:] and
                                            not '责任编辑' in text):
                                            filtered_texts.append(text)
                                    
                                    if filtered_texts:
                                        return '\n\n'.join(filtered_texts)
                        
                        # 如果都失败了，尝试直接从body中提取可能的内容区块
                        # 通常正文区块的文本密度较高
                        if soup.body:
                            text_blocks = []
                            for div in soup.body.find_all('div'):
                                # 如果div内有多个p标签，可能是正文区域
                                p_tags = div.find_all('p')
                                if len(p_tags) >= 3:  # 至少包含3个段落
                                    p_texts = [p.get_text(strip=True) for p in p_tags if len(p.get_text(strip=True)) > 20]
                                    if p_texts:
                                        # 计算这个div的文本密度
                                        total_text = ' '.join(p_texts)
                                        if len(total_text) > 200:  # 文本足够长
                                            text_blocks.append('\n\n'.join(p_texts))
                            
                            # 返回最长的文本块
                            if text_blocks:
                                return max(text_blocks, key=len)
                        
                        # 如果什么都没找到
                        continue
                    
                    else:
                        # 减少失败重试等待时间
                        time.sleep(0.5)
                
                except Exception:
                    # 减少异常等待时间
                    time.sleep(0.5)
                    continue
            
            # 如果所有重试都失败，返回错误信息
            return "无法获取文章详情内容"
        
        except Exception as e:
            return f"获取内容时发生错误: {str(e)}"
    
    def clean_content(self, content):
        """
        清理内容，去除多余的导航栏、页眉页脚等信息
        """
        if not content:
            return content
            
        # 按行分割内容
        lines = content.split('\n')
        cleaned_lines = []
        
        # 逐行检查
        for line in lines:
            line = line.strip()
            # 排除导航栏内容
            if any(nav_item in line for nav_item in ['央视网', '网友', '登录', '注册', '首页', '新闻', '视频', '经济', '体育', '军事', '频道', '网站地图']):
                continue
                
            # 排除可能的页脚内容
            if any(footer_item in line for footer_item in ['版权所有', '公司', '工信部', '经营许可证', '京ICP备', '联系我们']):
                continue
                
            # 排除编辑信息
            if '编辑：' in line or '责任编辑' in line or line.startswith('编辑'):
                continue
                
            # 排除时间和来源行
            if line.startswith('发布时间') or line.startswith('来源：') or '年' in line and '月' in line and '日' in line and len(line) < 30:
                continue
                
            # 保留有效内容
            if line and len(line) > 5:
                cleaned_lines.append(line)
        
        # 返回清理后的内容
        return '\n\n'.join(cleaned_lines)
    
    def search_backup_news(self):
        """
        从备用页面获取反诈新闻
        """
        # 初始化重试计数器
        retry_count = 0
        base_sleep_time = 1  # 基础等待时间(秒)
        
        # 尝试所有备用URL
        for backup_url_index in range(len(self.backup_urls)):
            # 获取下一个备用URL
            backup_url = self.backup_urls[backup_url_index]
            
            # 对每个URL尝试多次
            for attempt in range(self.max_retries):
                try:
                    # 等待请求间隔
                    self.wait_between_requests()
                    
                    # 添加随机参数避免缓存
                    headers = self.prepare_headers()
                    
                    # 构建URL带随机参数避免缓存
                    random_query = f"t={int(time.time())}&r={random.random()}&nocache={random.randint(1000, 9999)}"
                    if '?' in backup_url:
                        url = f"{backup_url}&{random_query}"
                    else:
                        url = f"{backup_url}?{random_query}"
                    
                    # 获取session
                    session = self.get_session()
                    
                    # 获取页面内容
                    response = session.get(
                        url,
                        headers=headers,
                        timeout=15,
                        allow_redirects=True
                    )
                    
                    # 保存新cookies
                    self.save_cookies(response.cookies.get_dict())
                    
                    # 设置正确的编码
                    response.encoding = 'utf-8'
                    
                    if response.status_code != 200:
                        # 不再输出警告日志
                        # logger.warning(f"备用URL {backup_url} 请求失败: HTTP状态码 {response.status_code}")
                        time.sleep(base_sleep_time * (2 ** attempt))  # 指数退避
                        continue
                        
                    # 检查内容是否有效
                    if not self.is_content_valid(response.text):
                        # 不再输出警告日志
                        # logger.warning(f"备用URL {backup_url} 响应内容无效")
                        time.sleep(base_sleep_time * (2 ** attempt))  # 指数退避
                        continue
                    
                    # 解析HTML内容
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 查找反诈新闻条目
                    news_items = []
                    
                    # 尝试不同的选择器
                    article_selectors = [
                        '.article-list li', 
                        '.news-list .item', 
                        '.list-item',
                        'div.text_box',
                        '.content .item',
                        '.news-block',
                        '.article-item',
                        '.article'
                    ]
                    
                    article_elements = []
                    for selector in article_selectors:
                        elements = soup.select(selector)
                        if elements:
                            article_elements = elements
                            # 不再输出日志
                            # logger.info(f"在备用URL中找到{len(elements)}个新闻条目，使用选择器: {selector}")
                            break
                    
                    if not article_elements:
                        # 不再输出警告日志
                        # logger.warning(f"在备用URL {backup_url} 中未找到新闻条目")
                        time.sleep(base_sleep_time * (2 ** attempt))  # 指数退避
                        continue
                    
                    for article in article_elements:
                        try:
                            # 获取链接和标题
                            a_tag = article.find('a')
                            if not a_tag:
                                continue
                            
                            link = a_tag.get('href', '')
                            if not link:
                                continue
                                
                            # 确保链接是完整的
                            if not link.startswith('http'):
                                parsed_url = urllib.parse.urlparse(backup_url)
                                base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                link = f"{base_url}{link}" if link.startswith('/') else f"{base_url}/{link}"
                            
                            # 获取标题
                            title = a_tag.get_text(strip=True) or a_tag.get('title', '')
                            if not title and a_tag.find('img'):
                                # 尝试从图片alt属性获取标题
                                title = a_tag.find('img').get('alt', '')
                            
                            if not title:
                                continue
                            
                            # 如果标题中没有"反诈"或"防骗"关键词，可能不是我们需要的内容
                            if not any(keyword in title for keyword in ['反诈', '防骗', '诈骗', '电信诈骗', '网络诈骗', '安全']):
                                # 但我们仍保留，因为可能是相关内容但标题没有明确关键词
                                # logger.debug(f"标题不包含反诈关键词: {title}")
                                pass
                            
                            # 提取发布时间
                            time_selectors = ['.time', '.date', '.pub-time', '.meta-time', '.timestamp', '.datetime']
                            publish_time = None
                            
                            for selector in time_selectors:
                                time_element = article.select_one(selector)
                                if time_element:
                                    time_text = time_element.get_text(strip=True)
                                    # 尝试多种时间格式
                                    time_patterns = [
                                        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
                                        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})',
                                        r'(\d{4}-\d{2}-\d{2})',
                                        r'(\d{2}-\d{2} \d{2}:\d{2})',
                                        r'(\d{2}/\d{2}/\d{4})',
                                        r'(\d{4}年\d{2}月\d{2}日)',
                                        r'(\d{2}月\d{2}日)',
                                        r'(\d+天前)',
                                        r'(\d+小时前)',
                                        r'(\d+分钟前)'
                                    ]
                                    
                                    for pattern in time_patterns:
                                        match = re.search(pattern, time_text)
                                        if match:
                                            time_str = match.group(1)
                                            # 处理相对时间
                                            if '天前' in time_str:
                                                days = int(time_str.replace('天前', ''))
                                                publish_time = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
                                            elif '小时前' in time_str:
                                                hours = int(time_str.replace('小时前', ''))
                                                publish_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
                                            elif '分钟前' in time_str:
                                                minutes = int(time_str.replace('分钟前', ''))
                                                publish_time = (datetime.now() - timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')
                                            # 处理年月日格式
                                            elif '年' in time_str and '月' in time_str and '日' in time_str:
                                                year = int(re.search(r'(\d{4})年', time_str).group(1))
                                                month = int(re.search(r'(\d{2})月', time_str).group(1))
                                                day = int(re.search(r'(\d{2})日', time_str).group(1))
                                                publish_time = f"{year:04d}-{month:02d}-{day:02d} 08:00:00"
                                            # 处理月日格式
                                            elif '月' in time_str and '日' in time_str and '年' not in time_str:
                                                year = datetime.now().year
                                                month = int(re.search(r'(\d{2})月', time_str).group(1))
                                                day = int(re.search(r'(\d{2})日', time_str).group(1))
                                                publish_time = f"{year:04d}-{month:02d}-{day:02d} 08:00:00"
                                            # 处理其他标准格式
                                            else:
                                                # 标准化不完整的时间格式
                                                if len(time_str) <= 10:  # 只有日期
                                                    time_str += " 08:00:00"
                                                elif len(time_str) <= 16:  # 没有秒
                                                    time_str += ":00"
                                                
                                                # 处理分隔符
                                                if '/' in time_str:
                                                    parts = time_str.split('/')
                                                    if len(parts) >= 3:
                                                        # 通常美式日期格式 MM/DD/YYYY
                                                        month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
                                                        time_str = f"{year:04d}-{month:02d}-{day:02d} 08:00:00"
                                                
                                                publish_time = time_str
                                            break
                                    
                                    if publish_time:
                                        break
                            
                            # 如果没有找到发布时间，使用当前时间
                            if not publish_time:
                                publish_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # 获取内容预览
                            content_preview = ""
                            preview_selectors = ['.desc', '.summary', 'p', '.content-preview', '.article-summary']
                            for selector in preview_selectors:
                                preview_element = article.select_one(selector)
                                if preview_element:
                                    content_preview = preview_element.get_text(strip=True)
                                    if content_preview:
                                        break
                            
                            # 获取图片
                            image_url = ""
                            img_element = article.find('img')
                            if img_element and img_element.has_attr('src'):
                                image_url = img_element['src']
                                if not image_url.startswith('http'):
                                    parsed_url = urllib.parse.urlparse(backup_url)
                                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                                    image_url = f"{base_url}{image_url}" if image_url.startswith('/') else f"{base_url}/{image_url}"
                            
                            # 来源
                            source = "央视网" # 默认来源
                            source_selectors = ['.source', '.from', '.author', '.publisher']
                            for selector in source_selectors:
                                source_element = article.select_one(selector)
                                if source_element:
                                    source_text = source_element.get_text(strip=True)
                                    if source_text:
                                        if '来源：' in source_text:
                                            source = source_text.replace('来源：', '')
                                        else:
                                            source = source_text
                                        break
                            
                            # 创建新闻项
                            news_item = {
                                'title': title,
                                'link': link,
                                'publish_time': publish_time,
                                'source': source,
                                'content_preview': content_preview,
                                'image_url': image_url
                            }
                            
                            news_items.append(news_item)
                            # 不再输出日志
                            # logger.info(f"从备用URL成功解析新闻: {title}")
                            
                        except Exception as e:
                            # 不再输出日志
                            # logger.error(f"解析备用新闻条目时出错: {str(e)}")
                            continue
                    
                    if news_items:
                        # 按时间排序，最新的在前
                        news_items.sort(key=lambda x: x['publish_time'], reverse=True)
                        
                        # 更新缓存
                        self.news_cache["backup_news_items"] = news_items
                        self.last_cache_time = time.time()
                        
                        # 移除日志输出
                        # if logger.isEnabledFor(logging.INFO):
                        #     logger.info(f"从备用URL共解析到{len(news_items)}条反诈新闻")
                        return news_items
                    else:
                        # 不再输出警告日志
                        # logger.warning(f"从备用URL {backup_url} 未解析到任何新闻条目")
                        pass
                    
                except Exception as e:
                    # 不再输出日志
                    # logger.error(f"获取备用新闻失败: {str(e)}")
                    time.sleep(base_sleep_time * (2 ** attempt))  # 指数退避
        
        # 所有URL和尝试都失败了
        # logger.error("所有备用URL均未能获取到新闻")
        return []
    
    def get_latest_antifraud_news(self):
        """
        获取最新反诈新闻，优先返回今日发布的文章
        如果今日没有发布的文章，返回空结果
        """
        try:
            # 不再输出INFO日志
            # self.logger.info("开始提取CCTV反诈新闻...")
            
            # 先尝试从主要搜索源获取新闻
            news_items = self.search_antifraud_news()
            
            # 如果没有获取到新闻，尝试备用搜索方法
            if not news_items:
                # 不再输出警告日志
                # self.logger.warning("主要搜索未找到新闻，尝试备用搜索...")
                news_items = self.search_backup_news()
                
            # 如果仍然没有新闻，返回失败
            if not news_items:
                # 不再输出错误日志
                # self.logger.error("无法获取反诈新闻")
                return {"status": "error", "message": "无法获取反诈新闻", "data": []}
            
            # 过滤出今天发布的文章
            today = datetime.now().strftime("%Y-%m-%d")
            today_news = [news for news in news_items if news.get("publish_time", "").startswith(today)]
            
            # 记录今日文章数量
            if today_news:
                # 不再输出INFO日志
                # if self.logger.isEnabledFor(logging.INFO):
                #     self.logger.info(f"找到{len(today_news)}条今日发布的反诈新闻")
                pass
            else:
                # 不再输出WARNING日志
                # self.logger.warning("没有找到今日发布的反诈新闻")
                return {"status": "success", "message": "没有今日发布的反诈新闻", "data": []}
            
            # 获取今日前三条新闻的详细内容
            content_found = False
            for i in range(min(3, len(today_news))):
                news = today_news[i]
                news_url = news.get("link")
                
                # 确保URL有效
                if not news_url or not news_url.startswith("http"):
                    continue
                    
                try:
                    # 获取详细内容
                    if self.logger.isEnabledFor(logging.INFO):
                        # self.logger.info(f"尝试获取第{i+1}条新闻详细内容: {news_url}")
                        pass
                    content = self.get_article_content(news_url)
                    
                    # 清理内容
                    if content:
                        content = self.clean_content(content)
                    
                    # 确保内容有效且已清理
                    if content and len(content) > 100:
                        news["content"] = content
                        news["content_length"] = len(content)
                        content_found = True
                        # self.logger.info(f"成功获取第{i+1}条新闻详细内容，长度: {len(content)}字符")
                        break
                except Exception as e:
                    # self.logger.error(f"获取文章详细内容失败: {str(e)}")
                    continue
            
            # 如果没有获取到详细内容，使用第一条新闻的预览内容
            if not content_found and today_news:
                # self.logger.warning("未能获取详细内容，使用预览内容")
                first_news = today_news[0]
                preview = first_news.get("content_preview", "")
                if preview:
                    first_news["content"] = preview
                    first_news["content_length"] = len(preview)
                    content_found = True
            
            # 返回结果
            if content_found:
                return {"status": "success", "message": "成功获取今日反诈新闻", "data": today_news}
            else:
                return {"status": "success", "message": "未能获取有效内容的反诈新闻", "data": today_news}
            
        except Exception as e:
            # self.logger.error(f"获取最新反诈新闻时发生错误: {str(e)}")
            import traceback
            # self.logger.error(traceback.format_exc())
            return {"status": "error", "message": f"获取最新反诈新闻失败: {str(e)}", "data": []}

    def crawl(self):
        """
        执行爬取任务，返回爬取结果
        """
        try:
            result = self.get_latest_antifraud_news()
            return result
        except Exception as e:
            # self.logger.error(f"爬取失败: {str(e)}")
            import traceback
            # self.logger.error(traceback.format_exc())
            return {"status": "error", "message": f"爬取失败: {str(e)}", "data": []}

@eastmoney_antifraud_bp.route('/eastmoney_antifraud_article', methods=['GET'])
def get_eastmoney_antifraud_article():
    """
    获取反诈新闻API端点 - 返回过去24小时内发布的最新一条新闻
    简化数据结构：只返回content、date、title、url四个字段
    """
    crawler = None
    try:
        # 计算时间范围用于显示
        now = datetime.now()
        time_24h_ago = now - timedelta(hours=24)
        time_range = f"{time_24h_ago.strftime('%Y-%m-%d %H:%M')} 至 {now.strftime('%Y-%m-%d %H:%M')}"
        
        crawler = CCTVAntifraudCrawler()
        
        # 直接获取搜索结果
        news_items = crawler.search_antifraud_news()
        
        # 如果主要来源没有结果，尝试备用来源
        if not news_items:
            # logger.warning("API端点: 主要来源未找到新闻，尝试备用来源...")
            news_items = crawler.search_backup_news()
        
        # 如果没有找到任何新闻
        if not news_items:
            # logger.warning("API端点: 所有来源均未找到新闻")
            return jsonify({
                "status": "success",
                "message": f"未找到反诈新闻",
                "data": [],
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "time_range": time_range
            })
        
        # 定义函数检查是否在过去24小时内
        def is_within_24_hours(time_str):
            try:
                # 解析时间字符串
                publish_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                # 判断发布时间是否在过去24小时内
                return time_24h_ago <= publish_time <= now
            except Exception:
                return False
        
        # 筛选过去24小时内的新闻
        recent_news = [news for news in news_items if is_within_24_hours(news['publish_time'])]
        
        # 如果没有过去24小时内的新闻，返回空结果
        if not recent_news:
            # logger.warning("API端点: 未找到过去24小时内的新闻")
            return jsonify({
                "status": "success",
                "message": f"未找到在时间范围（{time_range}）内的反诈新闻",
                "data": [],
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "time_range": time_range
            })
        
        # 获取过去24小时内发布的最新一条新闻（按发布时间排序后的第一条）
        recent_news.sort(key=lambda x: x['publish_time'], reverse=True)
        latest_recent_news = recent_news[0]
        
        try:
            # 等待请求间隔
            if crawler:
                crawler.wait_between_requests()
            
            # 获取文章详情
            content = crawler.get_article_content(latest_recent_news['link'])
            
            # 如果获取到内容，进行清理
            if content and content != "无法获取文章详情内容" and not content.startswith("获取内容时发生错误"):
                cleaned_content = crawler.clean_content(content)
                if not cleaned_content:
                    cleaned_content = content
            else:
                # 如果无法获取详细内容，使用预览内容
                cleaned_content = latest_recent_news.get('content_preview', '') + "\n\n[注意: 此为预览内容]"
            
            # 创建简化的新闻数据
            simplified_news = {
                "title": latest_recent_news.get('title', ''),
                "date": latest_recent_news.get('publish_time', ''),
                "url": latest_recent_news.get('link', ''),
                "content": cleaned_content
            }
            
            return jsonify({
                "status": "success",
                "message": f"成功获取在时间范围（{time_range}）内的反诈新闻",
                "data": simplified_news,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "time_range": time_range
            })
        except Exception as e:
            # logger.error(f"处理新闻项时出错: {str(e)}")
            # 如果处理失败，仍然返回基本信息
            simplified_news = {
                "title": latest_recent_news.get('title', ''),
                "date": latest_recent_news.get('publish_time', ''),
                "url": latest_recent_news.get('link', ''),
                "content": latest_recent_news.get('content_preview', '') + "\n\n[注意: 处理详情时出错，仅显示预览内容]"
            }
            
            return jsonify({
                "status": "partial_success",
                "message": f"获取在时间范围（{time_range}）内的反诈新闻但处理详情时出错",
                "data": simplified_news,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "time_range": time_range
            })
            
    except Exception as e:
        # logger.error(f"API端点处理请求时出错: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "data": [],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    finally:
        # 确保请求结束后释放资源
        if crawler and hasattr(crawler, 'session'):
            try:
                crawler.session.close()
            except:
                pass

if __name__ == "__main__":
    # 精简测试代码
    print("开始提取CCTV反诈新闻...")
    crawler = CCTVAntifraudCrawler()
    
    # 关闭所有日志输出
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # 只执行一次测试，不再重复多次
    try:
        # 获取搜索结果
        news_items = crawler.search_antifraud_news()
        
        if not news_items:
            print("未找到任何反诈新闻")
        else:
            # 只显示数量，不展示详情
            print(f"\n获取到{len(news_items)}条反诈新闻")
            
            # 检查是否有今天的新闻
            today_news = [news for news in news_items if crawler.is_today(news.get('publish_time', ''))]
            if today_news:
                print(f"今天发布的新闻数量: {len(today_news)}")
            else:
                print("没有今天发布的新闻")
    
    except Exception as e:
        print(f"测试时发生错误: {str(e)}")
    
    print("\n提取完成!")
