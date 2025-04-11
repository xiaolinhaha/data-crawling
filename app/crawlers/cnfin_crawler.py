import requests
from bs4 import BeautifulSoup
import time
import datetime
import re
import json
import os

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
            
            print(f"正在获取页面: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                print(f"成功获取页面: {url}")
                return response.text
            else:
                print(f"获取页面失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取HTML出错: {e}")
            return None
    
    def parse_article_list(self, html):
        """解析文章列表页，获取文章链接和时间"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 首先尝试打印页面标题，确认页面加载正确
            title_elem = soup.find('title')
            if title_elem:
                print(f"页面标题: {title_elem.text.strip()}")
            
            # 查找目标元素
            print("开始查找新闻列表...")
            target_ul = soup.select_one('ul.cjmh-gdxw-cont')
            
            if not target_ul:
                print("未找到<ul class='cjmh-gdxw-cont'>元素")
                return None
            
            print("找到<ul class='cjmh-gdxw-cont'>元素，开始提取内容...")
            
            # 查找所有文章项目 div.ui-zxlist-item
            news_items = target_ul.select('div.ui-zxlist-item')
            print(f"找到 {len(news_items)} 个新闻项目")
            
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
            
            print(f"共解析到 {len(article_links)} 条新闻")
            for idx, article in enumerate(article_links):
                print(f"{idx+1}. {article['title']} [{article['pub_time']}]")
                
            return article_links
            
        except Exception as e:
            print(f"解析文章列表出错: {e}")
            import traceback
            traceback.print_exc()
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
            print("未找到文章日期，使用当前日期")
            return datetime.datetime.now().strftime("%Y-%m-%d")
            
        except Exception as e:
            print(f"提取文章日期出错: {e}")
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
                    print(f"找到内容区域: {selector}")
                    break
            
            # 如果没找到，尝试查找主要内容区
            if not content_element:
                print("没有找到指定的内容区域，尝试查找其他可能包含内容的元素...")
                
                # 尝试找带有"article"、"content"等关键词的类
                content_divs = soup.find_all('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'body', 'main']))
                
                for div in content_divs:
                    # 查找有足够文本内容且包含多个段落的div
                    paragraphs = div.find_all('p')
                    if len(paragraphs) >= 2:
                        content_element = div
                        print(f"找到可能的内容区域: {div.get('class', ['未知类名'])}")
                        break
            
            # 如果仍然没有找到，直接找页面中的段落
            if not content_element:
                print("未找到内容区域，尝试直接提取页面段落...")
                paragraphs = soup.find_all('p')
                if paragraphs:
                    all_text = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        if text and len(text) > 10:  # 只保留有意义的段落
                            all_text.append(text)
                    
                    if all_text:
                        return '\n\n'.join(all_text)
                    else:
                        return "未找到有效的文章内容"
            
            # 从找到的内容区域提取文本
            if content_element:
                # 移除所有script和style元素
                for script in content_element.find_all(['script', 'style']):
                    script.decompose()
                
                # 提取所有段落
                paragraphs = []
                for p in content_element.find_all('p'):
                    text = p.get_text(strip=True)
                    if text:
                        paragraphs.append(text)
                
                # 如果没有找到段落，获取所有文本
                if not paragraphs:
                    text = content_element.get_text(separator="\n", strip=True)
                    paragraphs = [line for line in text.split('\n') if line.strip()]
                
                if paragraphs:
                    return '\n\n'.join(paragraphs)
            
            return "未能提取到文章内容"
            
        except Exception as e:
            print(f"解析文章内容出错: {e}")
            return f"解析文章内容时出错: {e}"
    
    def get_article_detail(self, url):
        """获取文章详情内容和日期"""
        html = self.get_html(url)
        if html:
            content = self.parse_article_content(html)
            pub_date = self.extract_date_from_article(html)
            return content, pub_date
        return "获取文章详情失败", None
    
    def crawl(self):
        """爬取前5条文章并获取详情和日期"""
        # 获取文章列表页
        list_html = self.get_html(self.list_url)
        if not list_html:
            print("获取文章列表页失败")
            return None
        
        # 解析文章列表，获取前5条
        article_links = self.parse_article_list(list_html)
        if not article_links or len(article_links) == 0:
            print("解析文章列表失败")
            return None
        
        # 获取每篇文章的详情和日期
        articles_with_date = []
        
        for article in article_links:
            print(f"处理文章: {article['title']}")
            print(f"详情链接: {article['url']}")
            
            # 获取文章内容和日期
            time.sleep(1)  # 避免请求过快
            content, pub_date = self.get_article_detail(article['url'])
            
            # 如果没有提取到日期，使用列表页的时间
            if not pub_date and 'pub_time' in article:
                pub_date = article['pub_time'].split(' ')[0]  # 只取日期部分
                print(f"使用列表页日期: {pub_date}")
            
            if pub_date:
                print(f"文章日期: {pub_date}")
                articles_with_date.append({
                    "title": article['title'],
                    "url": article['url'],
                    "content": content,
                    "pub_date": pub_date
                })
            else:
                print(f"未找到文章日期，使用当前日期")
                # 使用爬取的时间作为默认日期
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                articles_with_date.append({
                    "title": article['title'],
                    "url": article['url'],
                    "content": content,
                    "pub_date": today
                })
        
        # 按日期排序，选择最新的
        if articles_with_date:
            articles_with_date.sort(key=lambda x: x['pub_date'], reverse=True)
            latest_article = articles_with_date[0]
            
            # 记录当前爬取时间
            crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            result = {
                "Website_Name": self.name,
                "Website_URL": self.list_url,
                "Article_Title": latest_article['title'],
                "Article_URL": latest_article['url'],
                "Article_Content": latest_article['content'],
                "Article_Pub_Date": latest_article['pub_date'],
                "Crawl_Time": crawl_time
            }
            
            return result
        
        return None

# 测试代码
if __name__ == "__main__":
    print(f"开始爬取{CnfinCrawler().name}内容...")
    crawler = CnfinCrawler()
    result = crawler.crawl()
    
    if result:
        # 创建exports目录（如果不存在）
        if not os.path.exists('exports'):
            os.makedirs('exports')
            
        # 生成带日期的文件名
        today = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"exports/{today}_cnfin_latest.json"
        
        # 保存为JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print("爬取成功!")
        print(f"标题: {result['Article_Title']}")
        print(f"链接: {result['Article_URL']}")
        print(f"发布日期: {result['Article_Pub_Date']}")
        print(f"内容长度: {len(result['Article_Content'])}")
        print(f"数据已保存到: {filename}")
    else:
        print("爬取失败!") 