import requests
from bs4 import BeautifulSoup
import datetime
import re
import os
import json
from flask import Blueprint, request, jsonify
from flask_restful import reqparse
import logging
from datetime import datetime, timedelta
import traceback

logger = logging.getLogger(__name__)

class ChinaPolicyCrawler:
    """中国政策网爬虫，爬取政策解读新闻"""
    
    def __init__(self):
        self.name = "中国政策网"
        self.base_url = "http://www.chinapolicy.net/"
        self.list_url = "http://www.chinapolicy.net/list.php?fid-40-page-1.htm"
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': self.base_url
        }
    
    def get_html(self, url):
        """获取网页HTML内容"""
        try:
            logger.info(f"开始请求URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            # 使用GBK编码来解析中文
            response.encoding = 'gbk'
            if response.status_code == 200:
                logger.info(f"成功获取页面内容，长度: {len(response.text)}")
                return response.text
            else:
                logger.error(f"获取页面失败: {url}, 状态码: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"获取页面出错: {url}, 错误: {str(e)}")
            return None
    
    def parse_article_list(self, html):
        """解析文章列表页，获取新闻列表"""
        if not html:
            logger.error("HTML内容为空，无法解析")
            return None
        
        # 保存HTML到文件进行调试
        try:
            with open("debug_list_page.html", "w", encoding="utf-8") as f:
                f.write(html)
                logger.info("已将列表页HTML保存到debug_list_page.html")
        except Exception as e:
            logger.error(f"保存调试HTML出错: {str(e)}")
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            logger.info("使用最直接的方法查找所有文章链接...")
            
            # 查找包含文章的表格，这些表格的td会包含带有float:left和float:right的span元素
            # 这种方法更精确，只获取真正的文章列表，排除页脚链接
            article_links = []
            
            # 提取所有包含文章的表格行
            article_rows = soup.find_all('td', style=lambda s: s and 'line-height:27px' in s and 'padding-left:3px' in s)
            logger.info(f"找到可能包含文章的表格行: {len(article_rows)}个")
            
            for td in article_rows:
                # 查找文章链接
                a_tag = td.find('a')
                if not a_tag:
                    continue
                
                title = a_tag.text.strip()
                link = a_tag.get('href', '')
                
                if not title or not link:
                    continue
                
                # 处理相对链接
                if not link.startswith('http'):
                    if link.startswith('/'):
                        link = self.base_url.rstrip('/') + link
                    else:
                        link = self.base_url + link
                
                # 查找右侧时间元素
                right_span = td.find('span', style=lambda s: s and 'float:right' in s)
                date_text = ""
                
                if right_span:
                    span_text = right_span.text.strip()
                    # 通常日期格式为 (yyyy-mm-dd)
                    date_match = re.search(r'\(\s*(\d{4}-\d{1,2}-\d{1,2})\s*\)', span_text)
                    if date_match:
                        date_text = self.standardize_date(date_match.group(1))
                        logger.info(f"从右浮动span中提取到日期: {date_text}")
                
                # 如果没有找到日期，使用其他方法
                if not date_text:
                    date_text = self.extract_date_nearby(a_tag)
                
                # 添加文章信息
                article_links.append({
                    'title': title,
                    'url': link,
                    'date': date_text
                })
                logger.info(f"添加文章: {title}, 日期: {date_text}")
            
            if article_links:
                logger.info(f"成功解析到 {len(article_links)} 篇文章")
                return article_links
            else:
                logger.error("未找到任何有效文章链接")
                return None
                
        except Exception as e:
            logger.error(f"解析列表页出错: {str(e)}")
            return None
    
    def extract_date_nearby(self, a_tag):
        """
        从A标签周围寻找时间信息
        """
        try:
            logger.info(f"开始寻找文章发布时间, 文章标题: {a_tag.text.strip()}")
            
            # 方法1: 检查右侧浮动元素（网站实际使用这种方式显示日期）
            logger.info("尝试查找右侧浮动的时间元素")
            parent_td = a_tag.find_parent('td')
            if parent_td:
                # 查找右浮动的span元素
                right_span = parent_td.find('span', style=lambda s: s and 'float:right' in s)
                if right_span:
                    span_text = right_span.text.strip()
                    logger.info(f"找到右浮动的span: {span_text}")
                    # 通常日期格式为 (yyyy-mm-dd)
                    date_match = re.search(r'\(\s*(\d{4}-\d{1,2}-\d{1,2})\s*\)', span_text)
                    if date_match:
                        date_str = date_match.group(1)
                        logger.info(f"从右浮动span中提取到日期: {date_str}")
                        return self.standardize_date(date_str)
            
            # 方法2: 查找同级的span标签
            date_text = self.extract_date_from_span(a_tag)
            if self.is_valid_date(date_text):
                logger.info(f"从span标签找到有效日期: {date_text}")
                return date_text
            
            # 方法3: 查找同一行的所有元素中的时间信息
            parent = a_tag.parent
            if parent:
                logger.info("尝试从同一行查找时间信息")
                all_text = parent.get_text(" ", strip=True)
                date_text = self.extract_date_from_text(all_text)
                if self.is_valid_date(date_text):
                    logger.info(f"从同一行文本中找到有效日期: {date_text}")
                    return date_text
            
            # 方法4: 查找相邻的时间元素
            logger.info("尝试查找相邻的时间元素")
            siblings = list(a_tag.next_siblings) + list(a_tag.previous_siblings)
            for sibling in siblings:
                if hasattr(sibling, 'text') and sibling.text.strip():
                    sibling_text = sibling.text.strip()
                    date_text = self.extract_date_from_text(sibling_text)
                    if self.is_valid_date(date_text):
                        logger.info(f"从相邻元素找到有效日期: {date_text}")
                        return date_text
            
            # 方法5: 检查是否有特殊的时间格式，如span[style*="float:left"]
            logger.info("尝试查找特殊样式的时间元素")
            try:
                for span in parent.find_all('span', style=lambda s: s and 'float:left' in s):
                    span_text = span.text.strip()
                    logger.info(f"找到float:left样式的span: {span_text}")
                    date_text = self.extract_date_from_text(span_text)
                    if self.is_valid_date(date_text):
                        logger.info(f"从特殊样式中找到有效日期: {date_text}")
                        return date_text
            except Exception as e:
                logger.error(f"查找特殊样式时出错: {str(e)}")
            
            # 方法6: 如果网页结构允许，尝试直接获取已格式化的日期表示
            try:
                if a_tag.has_attr('data-date'):
                    date_str = a_tag.get('data-date')
                    logger.info(f"从a标签属性找到日期: {date_str}")
                    return self.standardize_date(date_str)
                elif a_tag.has_attr('title') and re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', a_tag.get('title')):
                    date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', a_tag.get('title'))
                    if date_match:
                        logger.info(f"从a标签title找到日期: {date_match.group(1)}")
                        return self.standardize_date(date_match.group(1))
            except Exception as e:
                logger.error(f"检查标签属性时出错: {str(e)}")
            
            # 如果没有找到有效的日期信息
            logger.warning("没有找到有效的日期信息，使用当前日期")
            return datetime.datetime.now().strftime("%Y-%m-%d")
            
        except Exception as e:
            logger.error(f"提取日期出错: {str(e)}")
            return datetime.datetime.now().strftime("%Y-%m-%d")
    
    def extract_date_from_span(self, a_tag):
        """
        从A标签同级的span标签中提取发布时间
        """
        try:
            # 获取A标签的父元素
            parent = a_tag.parent
            if not parent:
                logger.error("无法获取A标签的父元素")
                return datetime.datetime.now().strftime("%Y-%m-%d")
                
            # 查找父元素中的所有span标签
            logger.info(f"查找A标签同级的span标签, 父元素: {parent.name}")
            
            # 保存父元素的HTML用于调试
            try:
                logger.info(f"父元素HTML: {parent}")
            except Exception:
                pass
                
            # 查找A标签的所有平级span标签
            spans = []
            
            # 尝试方法1：直接找同级span
            next_sibling = a_tag.find_next_sibling('span')
            if next_sibling:
                spans.append(next_sibling)
                logger.info(f"找到直接的同级span: {next_sibling.text.strip()}")
            
            # 尝试方法2：找父元素下的所有span，检查是否与A标签同级
            if not spans:
                for span in parent.find_all('span'):
                    # 检查该span是否与a_tag有相同的父元素(即同级)
                    if span.parent == a_tag.parent:
                        spans.append(span)
                        logger.info(f"找到父元素下的同级span: {span.text.strip()}")
            
            # 如果找到了span标签
            if spans:
                for span in spans:
                    span_text = span.text.strip()
                    logger.info(f"处理span文本: {span_text}")
                    
                    date_text = self.extract_date_from_text(span_text)
                    if self.is_valid_date(date_text):
                        return date_text
            
            # 如果没有找到有效的span标签或日期信息
            logger.warning("没有找到有效的span标签或日期信息")
            return ""
            
        except Exception as e:
            logger.error(f"从span提取日期出错: {str(e)}")
            return ""
    
    def extract_date_from_text(self, text):
        """从文本中提取日期信息"""
        if not text:
            return ""
        
        try:
            logger.info(f"从文本提取日期: {text}")
            
            # 1. yyyy-mm-dd 或 yyyy/mm/dd 格式
            date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', text)
            if date_match:
                date_str = date_match.group(1).replace('/', '-')
                logger.info(f"找到标准日期格式: {date_str}")
                return self.standardize_date(date_str)
            
            # 2. yyyy年mm月dd日 格式
            date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
            if date_match:
                year, month, day = date_match.groups()
                date_str = f"{year}-{month}-{day}"
                logger.info(f"找到中文日期格式: {date_str}")
                return self.standardize_date(date_str)
            
            # 3. 相对日期，如"今天"、"昨天"、"X小时前"等
            if "今天" in text:
                logger.info("找到'今天'标记")
                return datetime.datetime.now().strftime("%Y-%m-%d")
                
            if "昨天" in text:
                logger.info("找到'昨天'标记")
                yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
                return yesterday.strftime("%Y-%m-%d")
                
            hours_match = re.search(r'(\d+)\s*小时前', text)
            if hours_match:
                hours = int(hours_match.group(1))
                logger.info(f"找到'{hours}小时前'标记")
                time_ago = datetime.datetime.now() - datetime.timedelta(hours=hours)
                return time_ago.strftime("%Y-%m-%d %H:%M:%S")
                
            minutes_match = re.search(r'(\d+)\s*分钟前', text)
            if minutes_match:
                minutes = int(minutes_match.group(1))
                logger.info(f"找到'{minutes}分钟前'标记")
                time_ago = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
                return time_ago.strftime("%Y-%m-%d %H:%M:%S")
            
            # 4. mm-dd 格式（当前年份）
            date_match = re.search(r'(\d{1,2})-(\d{1,2})', text)
            if date_match:
                month, day = date_match.groups()
                year = datetime.datetime.now().year
                date_str = f"{year}-{month}-{day}"
                logger.info(f"找到月日格式，补充当前年份: {date_str}")
                return self.standardize_date(date_str)
                
            # 5. mm/dd 格式（当前年份）
            date_match = re.search(r'(\d{1,2})/(\d{1,2})', text)
            if date_match:
                month, day = date_match.groups()
                year = datetime.datetime.now().year
                date_str = f"{year}-{month}-{day}"
                logger.info(f"找到月日斜杠格式，补充当前年份: {date_str}")
                return self.standardize_date(date_str)
                
            return ""
                
        except Exception as e:
            logger.error(f"提取日期出错: {str(e)}")
            return ""
    
    def is_valid_date(self, date_str):
        """检查日期字符串是否有效"""
        if not date_str:
            return False
            
        # 判断是否包含年月日
        if re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', date_str):
            return True
            
        # 判断是否包含时间
        if ' ' in date_str and re.search(r'\d{2}:\d{2}', date_str):
            return True
            
        return False
    
    def standardize_date(self, date_str):
        """标准化日期格式为YYYY-MM-DD"""
        try:
            # 将日期字符串拆分
            parts = date_str.split('-')
            if len(parts) == 3:
                year = parts[0]
                month = parts[1].zfill(2)  # 确保月份是两位数
                day = parts[2].zfill(2)    # 确保日期是两位数
                return f"{year}-{month}-{day}"
            return date_str
        except Exception as e:
            logger.error(f"标准化日期出错: {date_str}, {str(e)}")
            return date_str
    
    def parse_article_content(self, html):
        """解析文章内容，提取正文段落"""
        if not html:
            return "无法获取文章内容"
        
        # 保存HTML到文件进行调试
        try:
            with open("debug_article_page.html", "w", encoding="utf-8") as f:
                f.write(html)
                logger.info("已将文章页HTML保存到debug_article_page.html")
        except Exception as e:
            logger.error(f"保存调试HTML出错: {str(e)}")
        
        soup = BeautifulSoup(html, 'html.parser')
        try:
            logger.info("开始解析文章内容")
            
            # 尝试寻找文章内容
            content_element = None
            
            # 在政策网站，通常文章内容会在一个大的表格中
            # 尝试找到包含文章内容的元素
            for table in soup.find_all('table'):
                # 检查表格是否包含足够的文本
                text_content = table.get_text(strip=True)
                if len(text_content) > 500:
                    content_element = table
                    logger.info(f"找到可能的内容元素: 文本长度 {len(text_content)}")
                    break
            
            if not content_element:
                # 尝试其他常见的文章内容容器
                for div in soup.find_all('div', class_=lambda c: c and 'content' in c.lower()):
                    content_element = div
                    logger.info("找到带content类的div作为内容元素")
                    break
            
            if not content_element:
                # 最后尝试直接选择页面中最长的文本块
                max_text_len = 0
                for element in soup.find_all(['div', 'td']):
                    text_len = len(element.get_text(strip=True))
                    if text_len > max_text_len and text_len > 300:
                        max_text_len = text_len
                        content_element = element
                        logger.info(f"选择最长文本元素: {text_len} 字符")
            
            if not content_element:
                return "未找到文章内容区域"
            
            # 提取文章内容
            paragraphs = []
            
            # 首先尝试从段落标签中提取
            for p in content_element.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 10:  # 忽略太短的段落
                    paragraphs.append(text)
            
            # 如果没找到段落，就按照换行分割文本
            if not paragraphs:
                text = content_element.get_text('\n', strip=True)
                # 按换行符分割
                lines = text.split('\n')
                # 过滤空行和太短的行
                paragraphs = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
            
            if not paragraphs:
                return "未找到有效的文章内容"
            
            # 合并段落
            content = '\n\n'.join(paragraphs)
            logger.info(f"成功提取文章内容，长度: {len(content)}")
            
            return content
            
        except Exception as e:
            logger.error(f"解析文章内容出错: {str(e)}")
            return f"解析文章内容出错: {e}"
    
    def get_article_detail(self, url):
        """获取文章详情，包括标题和内容"""
        html = self.get_html(url)
        if not html:
            return None
        
        content = self.parse_article_content(html)
        
        return {
            'content': content
        }
    
    def is_recent_article(self, date_text, days=1):
        """
        判断文章是否是最近days天内发布的
        
        Args:
            date_text: 日期文本，格式为 yyyy-mm-dd
            days: 天数，默认为1天
            
        Returns:
            bool: 是否是最近days天内发布的文章
        """
        try:
            # 解析日期文本
            article_date = datetime.strptime(date_text.strip(), '%Y-%m-%d')
            # 设置为当天结束时间 23:59:59
            article_date = datetime.combine(article_date.date(), datetime.max.time())
            
            # 获取当前时间
            now = datetime.now()
            # 计算几天前的时间点
            days_ago = now - timedelta(days=days)
            
            logger.info(f"解析了日期，并设置为当天结束时间: {article_date}")
            logger.info(f"文章日期: {article_date}, 当前时间: {now}, {days}天前: {days_ago}, 是否在{days}天内: {article_date > days_ago}")
            
            # 判断文章是否是最近days天内发布的
            return article_date > days_ago
        except Exception as e:
            logger.error(f"日期解析错误: {e}")
            return False
    
    def crawl(self, days=1):
        """
        爬取中国政策网 (chinapolicy.net) 最近days天内的政策解读新闻
        
        Args:
            days: 获取最近几天的新闻，默认为1天
            
        Returns:
            list: 包含新闻信息的字典列表，每个字典包含title、url、date和content
        """
        logger.info(f"开始爬取 中国政策网 的最新新闻")
        
        # 获取文章列表页面内容
        list_url = "http://www.chinapolicy.net/list.php?fid-40-page-1.htm"
        logger.info(f"开始请求URL: {list_url}")
        
        try:
            response = requests.get(list_url, headers=self.headers, timeout=10)
            response.encoding = 'gbk'  # 设置编码
            html_content = response.text
            logger.info(f"成功获取页面内容，长度: {len(html_content)}")
            
            # 保存列表页HTML到文件，用于调试
            with open("debug_list_page.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("已将列表页HTML保存到debug_list_page.html")
            
            # 解析文章列表
            articles = self.parse_article_list(html_content)
            
            # 按日期排序，最新的在前面
            articles.sort(key=lambda x: x.get('date', ''), reverse=True)
            logger.info("已按日期排序文章")
            
            # 获取最近days天内发布的文章，最多返回2条
            recent_articles = []
            for article in articles:
                logger.info(f"检查文章: {article['title']}, 日期: {article['date']}")
                if self.is_recent_article(article['date'], days):
                    # 获取文章详情
                    article_detail = self.get_article_detail(article['url'])
                    
                    article_info = {
                        'title': article['title'],
                        'url': article['url'],
                        'date': article['date'],
                        'content': article_detail['content'] if article_detail else "无法获取文章内容"
                    }
                    recent_articles.append(article_info)
                    logger.info(f"添加最近文章: {article['title']}")
                    
                    # 最多返回2条
                    if len(recent_articles) >= 2:
                        break
            
            if not recent_articles:
                logger.info(f"未找到{days}天内发布的新闻")
            else:
                logger.info(f"找到{len(recent_articles)}条{days}天内的新闻")
            
            return recent_articles
        except Exception as e:
            logger.error(f"爬取中国政策网失败: {e}")
            traceback.print_exc()
            return []

# 集成到Flask蓝图
chinapolicy_bp = Blueprint('chinapolicy', __name__)

@chinapolicy_bp.route('/chinapolicy_news')
def chinapolicy_news():
    """
    获取中国政策网最近1天内的新闻
    
    Query Parameters:
        days: 获取最近几天的新闻，默认为1天
        
    Returns:
        JSON: 包含新闻信息的列表，格式为 {data, message, status}
    """
    days = request.args.get('days', 1, type=int)
    crawler = ChinaPolicyCrawler()
    print(f"开始爬取中国政策网内容...")
    articles = crawler.crawl(days)
    
    result = {
        "data": articles,
        "status": "success",
    }
    
    if not articles:
        result["message"] = f"未找到{days}天内的新闻"
        print(result["message"])
    else:
        result["message"] = f"成功获取到{len(articles)}条{days}天内的新闻"
        print(result["message"])
        
    return jsonify(result)

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print(f"开始爬取{ChinaPolicyCrawler().name}内容...")
    crawler = ChinaPolicyCrawler()
    result = crawler.crawl()
    
    if result and result['data']:
        # 创建exports目录（如果不存在）
        if not os.path.exists('exports'):
            os.makedirs('exports')
            
        # 生成带日期的文件名
        today = datetime.datetime.now().strftime("%Y%m%d")
        filename = f"exports/{today}_chinapolicy_latest.json"
        
        # 保存为JSON文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        print("爬取成功!")
        print(f"获取到{len(result['data'])}条文章")
        print(f"数据已保存到: {filename}")
    else:
        print("未找到24小时内的新闻") 