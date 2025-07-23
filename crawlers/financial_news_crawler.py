import requests
from bs4 import BeautifulSoup
import time
import datetime
import re
import json
import os
from flask import Blueprint, request
from flask_restful import reqparse

class FinancialNewsCrawler:
    """中国金融新闻网爬虫，使用HTML解析DOM方式获取文章"""
    
    def __init__(self):
        self.name = "中国金融新闻网"
        self.base_url = "https://www.financialnews.com.cn/"
        self.list_url = "https://www.financialnews.com.cn/node_3003.html"
        self.list_selector = "div.list-left"
        self.article_selector = "a"
        self.content_selectors = ['div.content', 'div.article-content', 'div.cont-left']
        
        # 添加随机性，避免缓存影响
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base_url,
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        # 添加更多日期相关选择器
        self.date_selectors = [
            'h6',
            'div.date', 
            'span.date', 
            'div.time', 
            'span.time', 
            'div.article-date', 
            'div.article-time',
            'div.pub-date',
            'div.publish-time',
            'div.publish-date'
        ]
    
    def remove_backslashes(self, text):
        """移除文本中的反斜杠"""
        if not text:
            return text
        return text.replace('\\', '')
    
    def get_html(self, url):
        """获取网页HTML内容"""
        try:
            # 添加随机的查询参数，避免缓存
            random_param = f"nocache={int(time.time() * 1000)}"
            if '?' in url:
                full_url = f"{url}&{random_param}"
            else:
                full_url = f"{url}?{random_param}"
                
            response = requests.get(
                full_url, 
                headers=self.headers, 
                timeout=15,
                # 禁用会话缓存
                verify=True,
                allow_redirects=True
            )
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as e:
            return None
    
    def parse_article_list(self, html):
        """解析文章列表页，获取前5条文章的标题和链接"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找指定的列表元素
            list_elem = soup.select_one(self.list_selector)
            if not list_elem:
                return None
            
            # 获取所有文章链接
            article_links = []
            links = list_elem.select(self.article_selector)
            
            # 只处理前5条
            count = 0
            for a in links:
                if count >= 5:
                    break
                
                title = a.text.strip()
                link = a.get('href', '')
                
                if not title or not link:
                    continue
                
                # 处理相对链接
                if not link.startswith('http'):
                    if link.startswith('/'):
                        link = self.base_url.rstrip('/') + link
                    else:
                        link = self.base_url + link
                
                article_links.append({
                    'title': title,
                    'url': link
                })
                count += 1
            
            return article_links
        except Exception as e:
            return None
    
    def extract_date_nearby(self, soup, target_tag):
        """在目标标签附近寻找日期信息"""
        if not target_tag:
            return None
            
        # 检查父元素及同级元素
        parent = target_tag.parent
        if parent:
            # 检查父元素文本
            parent_text = parent.get_text(strip=True)
            date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?(\s+\d{1,2}:\d{1,2}(:\d{1,2})?)?)', parent_text)
            if date_match:
                return self.standardize_date(date_match.group(1))
                
            # 检查同级元素
            for sibling in parent.find_all(recursive=False):
                if 'date' in sibling.get('class', '') or 'time' in sibling.get('class', ''):
                    return self.standardize_date(sibling.get_text(strip=True))
                    
        # 寻找附近的日期元素
        for selector in self.date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem and date_elem != target_tag:
                date_text = date_elem.get_text(strip=True)
                date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?(\s+\d{1,2}:\d{1,2}(:\d{1,2})?)?)', date_text)
                if date_match:
                    return self.standardize_date(date_match.group(1))
        
        return None
        
    def standardize_date(self, date_str):
        """将各种日期格式标准化为YYYY-MM-DD HH:MM:SS格式"""
        if not date_str:
            return None
            
        # 处理相对时间格式
        if '小时前' in date_str:
            hours = int(re.search(r'(\d+)\s*小时前', date_str).group(1))
            current_time = datetime.datetime.now()
            article_time = current_time - datetime.timedelta(hours=hours)
            return article_time.strftime("%Y-%m-%d %H:%M:%S")
            
        if '分钟前' in date_str:
            minutes = int(re.search(r'(\d+)\s*分钟前', date_str).group(1))
            current_time = datetime.datetime.now()
            article_time = current_time - datetime.timedelta(minutes=minutes)
            return article_time.strftime("%Y-%m-%d %H:%M:%S")
            
        if '刚刚' in date_str:
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        if '今天' in date_str:
            # 尝试提取时间部分
            time_match = re.search(r'(\d{1,2}):(\d{1,2})', date_str)
            current_time = datetime.datetime.now()
            if time_match:
                hour, minute = map(int, time_match.groups())
                article_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return article_time.strftime("%Y-%m-%d %H:%M:%S")
            return current_time.strftime("%Y-%m-%d")
            
        # 处理标准日期格式
        date_formats = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{1,2})(:(\d{1,2}))?',  # 2023年4月12日 12:30:45
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2023年4月12日
            r'(\d{4})-(\d{1,2})-(\d{1,2})\s*(\d{1,2}):(\d{1,2})(:(\d{1,2}))?',  # 2023-04-12 12:30:45
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2023-04-12
            r'(\d{4})/(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{1,2})(:(\d{1,2}))?',  # 2023/04/12 12:30:45
            r'(\d{4})/(\d{1,2})/(\d{1,2})'  # 2023/04/12
        ]
        
        for pattern in date_formats:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                year = int(groups[0])
                month = int(groups[1])
                day = int(groups[2])
                
                # 检查是否有时间部分
                if len(groups) > 3 and groups[3] is not None:
                    hour = int(groups[3])
                    minute = int(groups[4])
                    second = int(groups[6]) if len(groups) > 6 and groups[6] is not None else 0
                    try:
                        dt = datetime.datetime(year, month, day, hour, minute, second)
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                
                # 只有日期部分
                try:
                    dt = datetime.datetime(year, month, day)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    pass
        
        # 如果无法解析，返回原始字符串
        return date_str
        
    def extract_date_from_article(self, html):
        """从文章详情页提取日期，增强版，检查更多可能包含日期的元素"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 1. 首先检查常见的日期容器
            for selector in self.date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get_text(strip=True)
                    # 标准化日期
                    result = self.standardize_date(date_text)
                    if result:
                        return result
            
            # 2. 检查元数据中是否有日期
            meta_date = soup.find('meta', {'name': ['date', 'publish_date', 'publication_date']})
            if meta_date and 'content' in meta_date.attrs:
                return self.standardize_date(meta_date['content'])
                
            # 3. 检查结构化数据
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if 'datePublished' in data:
                        return self.standardize_date(data['datePublished'])
                except:
                    pass
            
            # 4. 查找类似"发布时间"附近的日期字符串
            time_labels = ['发布时间', '发布日期', '发表时间', '创建时间', '时间']
            for label in time_labels:
                label_elem = soup.find(text=re.compile(label))
                if label_elem:
                    # 查找该元素附近的日期文本
                    parent = label_elem.parent
                    if parent:
                        date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?(\s+\d{1,2}:\d{1,2}(:\d{1,2})?)?)', parent.get_text())
                        if date_match:
                            return self.standardize_date(date_match.group(1))
                            
                    # 检查下一个兄弟元素
                    next_sibling = label_elem.next_sibling
                    if next_sibling:
                        if isinstance(next_sibling, str):
                            date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?(\s+\d{1,2}:\d{1,2}(:\d{1,2})?)?)', next_sibling)
                            if date_match:
                                return self.standardize_date(date_match.group(1))
            
            # 5. 尝试在整个页面文本中查找日期
            entire_text = soup.get_text()
            date_patterns = [
                r'(\d{4}年\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{1,2}(:\d{1,2})?)',
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}-\d{2}-\d{2}\s*\d{1,2}:\d{1,2}(:\d{1,2})?)',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{4}/\d{2}/\d{2}\s*\d{1,2}:\d{1,2}(:\d{1,2})?)',
                r'(\d{4}/\d{2}/\d{2})'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, entire_text)
                if date_match:
                    return self.standardize_date(date_match.group(1))
                    
            # 6. 检查相对时间表达式
            relative_patterns = [
                r'(\d+)\s*小时前',
                r'(\d+)\s*分钟前',
                r'今天\s*(\d{1,2}):(\d{1,2})'
            ]
            
            for pattern in relative_patterns:
                match = re.search(pattern, entire_text)
                if match:
                    if '小时前' in pattern:
                        hours = int(match.group(1))
                        now = datetime.datetime.now()
                        article_time = now - datetime.timedelta(hours=hours)
                        return article_time.strftime("%Y-%m-%d %H:%M:%S")
                    elif '分钟前' in pattern:
                        minutes = int(match.group(1))
                        now = datetime.datetime.now()
                        article_time = now - datetime.timedelta(minutes=minutes)
                        return article_time.strftime("%Y-%m-%d %H:%M:%S")
                    elif '今天' in pattern:
                        hour, minute = map(int, match.groups()[1:3])
                        now = datetime.datetime.now()
                        article_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        return article_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 7. 如果找不到日期，默认使用当前日期
            return datetime.datetime.now().strftime("%Y-%m-%d")
            
        except Exception as e:
            # 发生异常时，返回当前日期作为默认值
            return datetime.datetime.now().strftime("%Y-%m-%d")
    
    def parse_article_content(self, html):
        """解析文章内容，提取正文段落"""
        if not html:
            return "无法获取文章内容"
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找文章内容区域
            content_element = None
            
            # 针对中国金融新闻网的特定选择器
            special_selectors = [
                'div.cont-left', 
                'div#ContentBody',
                'div.zw-con',
                'div.article-content',
                'div.content',
                'div#zoom',
                'div.TRS_Editor'
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
                content_divs = soup.find_all('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'text', 'body', 'main']))
                
                for div in content_divs:
                    # 查找有足够文本内容且包含多个段落的div
                    p_tags = div.find_all('p')
                    if len(p_tags) >= 2:
                        total_text = div.get_text(strip=True)
                        if len(total_text) > 100:  # 假设内容至少有100个字符
                            content_element = div
                            break
            
            if not content_element:
                # 最后的尝试：分析页面结构并查找主要区域
                main_div = soup.find('div', class_='main')
                if main_div:
                    center_div = main_div.find('div', class_='center')
                    if center_div:
                        content_element = center_div
                
                # 直接搜索页面中的段落
                if not content_element:
                    all_p = soup.find_all('p')
                    if len(all_p) > 5:  # 如果页面有一定数量的段落
                        paragraphs = []
                        for p in all_p:
                            text = p.get_text(strip=True)
                            if text and len(text) > 10:  # 筛选出有意义的段落
                                paragraphs.append(text)
                        
                        if paragraphs:
                            return '\n\n'.join(paragraphs)
            
            if not content_element:
                return "未找到文章内容区域"
            
            # 移除脚本和样式元素
            for script in content_element.select('script, style'):
                script.decompose()
            
            # 获取段落文本
            paragraphs = []
            for p in content_element.find_all(['p']):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            
            # 如果没有找到段落，尝试获取所有文本
            if not paragraphs:
                text = content_element.get_text(separator="\n", strip=True)
                if text:
                    paragraphs = [line for line in text.split('\n') if line.strip() and len(line.strip()) > 5]
            
            if not paragraphs:
                return "未找到文章段落"
            
            return '\n\n'.join(paragraphs)
        except Exception as e:
            return f"解析文章内容出错: {e}"
    
    def get_article_detail(self, url):
        """获取文章详情，包括标题、日期和内容"""
        html = self.get_html(url)
        if not html:
            return None
        
        date = self.extract_date_from_article(html)
        content = self.parse_article_content(html)
        
        return {
            'date': date,
            'content': content
        }
    
    def is_recent_article(self, date_str):
        """
        判断文章是否是今天发布的（只看今天，不看昨天）
        """
        if not date_str:
            return False
            
        try:
            # 解析日期字符串
            if ' ' in date_str:  # 包含时间部分
                article_date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:  # 只有日期部分
                article_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                
            # 获取当前时间
            now = datetime.datetime.now()
            
            # 判断文章日期是否为今天（只看今天，不考虑昨天）
            return article_date.date() == now.date()
                    
        except Exception:
            # 如果日期格式无法解析，返回False
            return False
    
    def crawl(self):
        """执行爬虫，获取最新的一条当天发布的新闻"""
        html = self.get_html(self.list_url)
        if not html:
            return {"status": "error", "message": "获取列表页失败", "data": []}
        
        article_links = self.parse_article_list(html)
        if not article_links:
            return {"status": "error", "message": "解析列表页失败", "data": []}
        
        results = []
        # 检查所有文章，直到找到一篇今天发布的
        for article in article_links:
            detail = self.get_article_detail(article['url'])
            if detail:
                # 移除所有内容中的反斜杠
                title = self.remove_backslashes(article['title'])
                url = self.remove_backslashes(article['url'])
                date = self.remove_backslashes(detail['date'])
                content = self.remove_backslashes(detail['content'])
                
                # 检查文章是否为今天发布
                if self.is_recent_article(date):
                    results.append({
                        'title': title,
                        'url': url,
                        'date': date,
                        'content': content
                    })
                    # 找到一篇今天的文章后就停止
                    break
        
        # 如果没有找到今天的文章，返回空结果
        if not results:
            return {
                "status": "success",
                "message": "未找到今天发布的新闻",
                "data": []
            }
        
        return {
            "status": "success",
            "message": f"成功获取{len(results)}条今日新闻",
            "data": results
        }

# 集成到Flask蓝图
financial_news_bp = Blueprint('financial_news', __name__)

@financial_news_bp.route('/financial_news', methods=['GET'])
def get_financial_news():
    """获取中国金融新闻网的最新新闻"""
    crawler = FinancialNewsCrawler()
    result = crawler.crawl()
    return result

# 测试代码
if __name__ == "__main__":
    print(f"开始爬取{FinancialNewsCrawler().name}内容...")
    crawler = FinancialNewsCrawler()
    result = crawler.crawl()
    
    # 打印结果
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result and result.get("data") and len(result["data"]) > 0:
        article = result["data"][0]
        print("\n获取到的文章信息:")
        print(f"标题: {article.get('title', 'N/A')}")
        print(f"链接: {article.get('url', 'N/A')}")
        print(f"发布日期: {article.get('date', 'N/A')}")
        print(f"内容长度: {len(article.get('content', ''))}")
        
        # 创建exports目录（如果不存在）
        if not os.path.exists('exports'):
            os.makedirs('exports')
            
        # 生成带日期的文件名
        today = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"exports/{today}_financial_news_latest.json"
        
        # 保存为JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print(f"数据已保存到: {filename}")
    else:
        print("未找到今天发布的文章") 