import requests
from bs4 import BeautifulSoup
import time
import datetime
import re
import json
import os

class FinancialNewsCrawler:
    """中国金融新闻网爬虫，使用HTML解析DOM方式获取文章"""
    
    def __init__(self):
        self.name = "中国金融新闻网"
        self.base_url = "https://www.financialnews.com.cn/"
        self.list_url = "https://www.financialnews.com.cn/node_3003.html"
        self.list_selector = "div.list-left"
        self.article_selector = "a"
        self.content_selectors = ['div.content', 'div.article-content', 'div.cont-left']
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base_url
        }
    
    def get_html(self, url):
        """获取网页HTML内容"""
        try:
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
        """解析文章列表页，获取前5条文章的标题和链接"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找指定的列表元素
            list_elem = soup.select_one(self.list_selector)
            if not list_elem:
                print(f"未找到 {self.list_selector} 元素")
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
            print(f"解析文章列表出错: {e}")
            return None
    
    def extract_date_from_article(self, html):
        """从文章详情页提取日期（h6标签下的日期信息）"""
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 查找h6标签
            h6_tag = soup.find('h6')
            if h6_tag:
                # 获取h6下面的文本，可能包含日期
                h6_text = h6_tag.get_text(strip=True)
                print(f"找到h6标签内容: {h6_text}")
                
                # 使用正则表达式提取日期
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', h6_text)
                if date_match:
                    return date_match.group(1)
            
            # 如果没找到h6标签或h6标签下没有日期，尝试其他可能含有日期的元素
            date_div = soup.find('div', class_=lambda c: c and 'date' in c.lower())
            if date_div:
                date_text = date_div.get_text(strip=True)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    return date_match.group(1)
            
            # 尝试在整个文章页面找日期
            date_patterns = [
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{4}/\d{2}/\d{2})'
            ]
            
            for pattern in date_patterns:
                date_match = re.search(pattern, soup.get_text())
                if date_match:
                    date_str = date_match.group(1)
                    # 统一转换为yyyy-mm-dd格式
                    if '年' in date_str:
                        date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
                    elif '/' in date_str:
                        date_str = date_str.replace('/', '-')
                    return date_str
            
            print("未找到文章日期")
            return None
        
        except Exception as e:
            print(f"提取文章日期出错: {e}")
            return None
    
    def parse_article_content(self, html):
        """解析文章内容，提取正文段落"""
        if not html:
            return "无法获取文章内容"
        
        print("开始解析文章内容...")
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 尝试打印页面标题，帮助确认页面是否正确加载
            title_elem = soup.find('title')
            if title_elem:
                print(f"页面标题: {title_elem.text.strip()}")
            
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
                    print(f"找到内容区域: {selector}")
                    break
            
            # 如果上面的选择器没找到，尝试更通用的方法
            if not content_element:
                print("尝试查找可能包含文章内容的元素...")
                
                # 查找可能包含文章的 div（通过类名关键词）
                content_divs = soup.find_all('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'text', 'body', 'main']))
                
                for div in content_divs:
                    # 查找有足够文本内容且包含多个段落的div
                    p_tags = div.find_all('p')
                    if len(p_tags) >= 2:
                        total_text = div.get_text(strip=True)
                        if len(total_text) > 100:  # 假设内容至少有100个字符
                            content_element = div
                            print(f"找到可能的内容区域: {div.name}, class: {div.get('class')}")
                            break
            
            if not content_element:
                # 最后的尝试：打印页面结构并查找主要区域
                print("常规方法未找到内容，分析页面结构...")
                main_div = soup.find('div', class_='main')
                if main_div:
                    print(f"页面主区域: div.main")
                    center_div = main_div.find('div', class_='center')
                    if center_div:
                        print(f"找到中心区域: div.center")
                        content_element = center_div
                
                # 直接搜索页面中的段落
                if not content_element:
                    all_p = soup.find_all('p')
                    if len(all_p) > 5:  # 如果页面有一定数量的段落
                        print(f"直接提取页面中的段落，共 {len(all_p)} 个")
                        paragraphs = []
                        for p in all_p:
                            text = p.get_text(strip=True)
                            if text and len(text) > 10:  # 筛选出有意义的段落
                                paragraphs.append(text)
                        
                        if paragraphs:
                            print(f"直接提取到 {len(paragraphs)} 个段落")
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
                print("未找到段落，尝试获取所有文本")
                text = content_element.get_text(separator="\n", strip=True)
                if text:
                    paragraphs = [line for line in text.split('\n') if line.strip() and len(line.strip()) > 5]
            
            if not paragraphs:
                return "未找到文章段落"
            
            print(f"成功提取 {len(paragraphs)} 个段落")
            return '\n\n'.join(paragraphs)
        except Exception as e:
            print(f"解析文章内容出错: {e}")
            import traceback
            traceback.print_exc()
            return f"解析文章内容出错: {e}"
    
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
    print(f"开始爬取{FinancialNewsCrawler().name}内容...")
    crawler = FinancialNewsCrawler()
    result = crawler.crawl()
    
    if result:
        # 创建exports目录（如果不存在）
        if not os.path.exists('exports'):
            os.makedirs('exports')
            
        # 生成带日期的文件名
        today = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"exports/{today}_financial_news_latest.json"
        
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