import requests
from bs4 import BeautifulSoup
import json
import re
import time
import datetime
import os

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
            
            print(f"正在请求东方财富网API...")
            response = requests.get(self.api_url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                print(f"API请求成功，正在解析数据...")
                
                # API返回的是JSONP格式，需要提取JSON部分
                json_str = re.search(r'jQuery\d+_?\d*\((.*)\)', response.text)
                if json_str:
                    data = json.loads(json_str.group(1))
                    print(f"成功解析API数据")
                    return data
                else:
                    print(f"解析JSONP数据失败，尝试直接解析...")
                    # 尝试直接解析为JSON
                    try:
                        data = json.loads(response.text)
                        print(f"直接解析JSON成功")
                        return data
                    except:
                        print(f"直接解析JSON失败")
            else:
                print(f"API请求失败，状态码: {response.status_code}")
            
            return None
        except Exception as e:
            print(f"获取API数据出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_article_list(self):
        """解析文章列表，获取前5条文章标题、链接和发布时间"""
        api_data = self.get_api_data()
        if not api_data or api_data.get('code') != '1':
            print("API返回数据无效")
            return None
        
        # 获取文章列表
        articles = api_data.get('data', {}).get('list', [])
        if not articles:
            print("未获取到文章列表")
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
    
    def parse_article_content(self, html):
        """解析文章内容，提取正文段落"""
        if not html:
            return "无法获取文章内容"
        
        print("开始解析东方财富网文章内容...")
        soup = BeautifulSoup(html, 'html.parser')
        try:
            # 尝试打印页面标题，帮助确认页面是否正确加载
            title_elem = soup.find('title')
            if title_elem:
                print(f"页面标题: {title_elem.text.strip()}")
            
            # 查找文章内容区域 - 根据提示直接查找 mainleft 下的 txtinfos
            print("尝试查找 mainleft 下的 txtinfos 区域...")
            mainleft = soup.find('div', class_='mainleft')
            
            if mainleft:
                print("找到 mainleft 区域")
                txtinfos = mainleft.find('div', class_='txtinfos')
                
                if txtinfos:
                    print("找到 txtinfos 区域")
                    content_element = txtinfos
                else:
                    print("未找到 txtinfos 区域，尝试其他方法...")
                    # 尝试查找 mainleft 下的其他可能包含内容的区域
                    content_div = mainleft.find('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'text', 'info']))
                    if content_div:
                        print(f"在 mainleft 下找到内容区域: {content_div.get('class')}")
                        content_element = content_div
                    else:
                        content_element = mainleft  # 如果找不到更具体的区域，就用 mainleft
            else:
                # 如果找不到 mainleft，回退到常规方法
                print("未找到 mainleft 区域，尝试常规选择器...")
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
                        print(f"找到内容区域: {selector}")
                        break
            
            # 如果上面的选择器没找到，尝试更通用的方法
            if not content_element:
                print("尝试查找可能包含文章内容的元素...")
                
                # 查找可能包含文章的 div（通过类名关键词）
                content_divs = soup.find_all('div', class_=lambda c: c and any(key in c.lower() for key in ['content', 'article', 'text', 'body', 'main', 'info']))
                
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
                # 最后的尝试：直接查找页面中所有有意义的段落
                print("常规方法未找到内容，尝试直接查找段落...")
                
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
                
                # 如果还是没找到，打印页面结构
                print("无法提取段落，分析页面结构...")
                body_classes = soup.body.get('class', []) if soup.body else []
                print(f"Body 类: {body_classes}")
                
                main_divs = soup.find_all('div', class_=lambda c: c and ('article' in c or 'content' in c or 'main' in c))
                if main_divs:
                    for div in main_divs[:3]:  # 只打印前三个
                        print(f"可能的内容区域: {div.name}, 类: {div.get('class')}")
                    
                    # 使用第一个可能的内容区域
                    content_element = main_divs[0]
                    print(f"使用第一个找到的内容区域")
                else:
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
                    lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 5]
                    # 过滤掉一些可能的噪音
                    paragraphs = [line for line in lines if not any(noise in line for noise in ['责任编辑', '免责声明', '原标题'])]
            
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
        """获取文章详情内容"""
        html = self.get_html(url)
        if html:
            content = self.parse_article_content(html)
            return content
        return "获取文章详情失败"
    
    def crawl(self):
        """爬取前5条文章，提取最新的一条详情"""
        # 获取文章列表
        article_links = self.parse_article_list()
        if not article_links or len(article_links) == 0:
            print("获取文章列表失败")
            return None
        
        # 按日期排序后，获取第一篇（最新）文章的详情
        latest_article = article_links[0]
        print(f"最新文章: {latest_article['title']}")
        print(f"发布日期: {latest_article['pub_date']}")
        print(f"详情链接: {latest_article['url']}")
        
        # 获取文章内容
        time.sleep(1)  # 避免请求过快
        content = self.get_article_detail(latest_article['url'])
        
        # 记录当前时间
        crawl_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result = {
            "Website_Name": self.name,
            "Website_URL": self.list_url,
            "Article_Title": latest_article['title'],
            "Article_URL": latest_article['url'],
            "Article_Summary": latest_article.get('summary', ''),
            "Article_Content": content,
            "Article_Pub_Date": latest_article['pub_date'],
            "Crawl_Time": crawl_time
        }
        
        return result

# 测试代码
if __name__ == "__main__":
    print(f"开始爬取{EastMoneyCrawler().name}内容...")
    crawler = EastMoneyCrawler()
    result = crawler.crawl()
    
    if result:
        # 创建exports目录（如果不存在）
        if not os.path.exists('exports'):
            os.makedirs('exports')
            
        # 生成带日期的文件名
        today = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"exports/{today}_east_money_latest.json"
        
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