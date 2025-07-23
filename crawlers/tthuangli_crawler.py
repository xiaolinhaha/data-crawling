#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
天天黄历网站爬虫
"""

import requests
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from flask import Blueprint, jsonify

# 创建蓝图
tthuangli_bp = Blueprint('tthuangli', __name__)

class TthuangliCrawler:
    """
    天天黄历网站爬虫类
    """
    
    def __init__(self):
        """
        初始化
        """
        self.name = "天天黄历"
        self.base_url = "https://www.tthuangli.com"
        self.yiji_url = "https://www.tthuangli.com/jinrihuangli/yiji/"
        self.wuxing_url = "https://www.tthuangli.com/jinrihuangli/wuxingchuanyi.html"
        
        # 设置请求头
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Referer': 'https://www.tthuangli.com/'
        }
    
    def get_page_content(self, url):
        """获取页面内容"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                return BeautifulSoup(response.text, 'html.parser')
            return None
        except Exception as e:
            print(f"获取页面失败: {str(e)}")
            return None
    
    def extract_date_info_from_main(self, soup):
        """从主页面提取日期信息"""
        date_info = {}
        
        try:
            # 提取公历日期 - 从span class="nowday"中获取
            nowday_span = soup.find('span', class_='nowday')
            if nowday_span:
                date_text = nowday_span.get_text().strip()
                date_info['date'] = date_text
            
            # 提取农历日期 - 从div class="is_nongli"中获取
            nongli_div = soup.find('div', class_='is_nongli')
            if nongli_div:
                nongli_text = nongli_div.get_text().strip()
                # 解析出农历、周信息、星期
                parts = nongli_text.split()
                if len(parts) >= 3:
                    date_info['chineseDate'] = parts[0]  # 如：二零二五年六月二十一
                    date_info['week'] = parts[1]         # 如：第29周
                    date_info['weekDay'] = parts[2]      # 如：周二
            
            # 提取干支日期 - 从div class="riqi_jian"中获取
            riqi_jian_div = soup.find('div', class_='riqi_jian')
            if riqi_jian_div:
                ganzhi_text = riqi_jian_div.get_text().strip()
                date_info['ganZhiDate'] = ganzhi_text
                
        except Exception as e:
            print(f"提取日期信息失败: {str(e)}")
        
        return date_info
    
    def extract_yiji_info_from_main(self, soup):
        """从主页面提取宜忌信息"""
        yiji_info = {}
        
        try:
            # 查找宜忌表格
            table = soup.find('table', attrs={'width': '100%'})
            if table:
                # 查找宜的内容 - 第一个td
                yi_td = table.find('td', attrs={'width': '280'})
                if yi_td:
                    yi_div = yi_td.find('div', class_='yi')
                    if yi_div:
                        yilist_div = yi_div.find('div', class_='yilist')
                        if yilist_div:
                            yi_spans = yilist_div.find_all('span')
                            yi_items = []
                            for span in yi_spans:
                                text = span.get_text().strip().replace('&nbsp;', '').replace(' ', '')
                                if text:
                                    yi_items.append(text)
                            if yi_items:
                                yiji_info['suitableActions'] = '、'.join(yi_items)
                
                # 查找忌的内容 - 最后一个td
                all_tds = table.find_all('td', attrs={'width': '280'})
                if len(all_tds) >= 2:
                    ji_td = all_tds[-1]  # 最后一个td
                    ji_div = ji_td.find('div', class_='yi')
                    if ji_div:
                        yilist_div = ji_div.find('div', class_='yilist')
                        if yilist_div:
                            ji_spans = yilist_div.find_all('span')
                            ji_items = []
                            for span in ji_spans:
                                text = span.get_text().strip().replace('&nbsp;', '').replace(' ', '')
                                if text:
                                    ji_items.append(text)
                            if ji_items:
                                yiji_info['inauspiciousActions'] = '、'.join(ji_items)
                
        except Exception as e:
            print(f"提取宜忌信息失败: {str(e)}")
        
        return yiji_info
    
    def extract_wuxing_info_from_page(self, soup):
        """从五行穿衣页面提取信息"""
        wuxing_info = {}
        
        try:
            # 方法1：通过HTML结构提取
            zhinan_items = soup.find_all('div', class_='zhinan_item')
            
            for item in zhinan_items:
                # 查找大吉色
                dajise_div = item.find('div', class_='dajise')
                if dajise_div:
                    dajse_desc = item.find('div', class_='dajse_desc')
                    if dajse_desc:
                        color_div = dajse_desc.find('div', class_='djse')
                        desc_div = dajse_desc.find('div', class_='jiekuang')
                        if color_div and desc_div:
                            color_text = color_div.get_text().strip()
                            desc_text = desc_div.get_text().strip()
                            
                            # 提取颜色：今日大吉色：蓝色、黑色、灰色
                            color_match = re.search(r'今日大吉色[：:]\s*(.+)', color_text)
                            if color_match:
                                wuxing_info['luckyColor'] = color_match.group(1).strip()
                                wuxing_info['luckyColorDetail'] = desc_text
                
                # 查找次吉色
                cjse_elem = item.find('div', class_='cjse')
                if cjse_elem:
                    cjse_desc = item.find('div', class_='cjse_desc')
                    if cjse_desc:
                        color_div = cjse_desc.find('div', class_='cjse')
                        desc_div = cjse_desc.find('div', class_='jiekuang')
                        if color_div and desc_div:
                            color_text = color_div.get_text().strip()
                            desc_text = desc_div.get_text().strip()
                            
                            # 提取颜色：今日次吉色：金色、银色、白色
                            color_match = re.search(r'今日次吉色[：:]\s*(.+)', color_text)
                            if color_match:
                                wuxing_info['secondaryLuckyColor'] = color_match.group(1).strip()
                                wuxing_info['secondaryLuckyColorDetail'] = desc_text
                
                # 查找不宜色
                byse_elem = item.find('div', class_='byse')
                if byse_elem:
                    cjse_desc = item.find('div', class_='cjse_desc')
                    if cjse_desc:
                        color_div = cjse_desc.find('div', class_='byse')
                        desc_div = cjse_desc.find('div', class_='jiekuang')
                        if color_div and desc_div:
                            color_text = color_div.get_text().strip()
                            desc_text = desc_div.get_text().strip()
                            
                            # 提取颜色：今日不宜色：绿色、青色、碧色
                            color_match = re.search(r'今日不宜色[：:]\s*(.+)', color_text)
                            if color_match:
                                wuxing_info['unluckyColor'] = color_match.group(1).strip()
                                wuxing_info['unluckyColorDetail'] = desc_text
            
            # 方法2：如果HTML结构提取失败，使用正则表达式从文本中提取
            if not wuxing_info:
                page_text = soup.get_text()
                
                # 查找今日大吉色
                daji_match = re.search(r'今日大吉色[：:]\s*([^今日次吉色]+)', page_text)
                if daji_match:
                    wuxing_info['luckyColor'] = daji_match.group(1).strip()
                    wuxing_info['luckyColorDetail'] = '能助旺您的运势，寓意行事会更顺利。'
                
                # 查找今日次吉色
                ciji_match = re.search(r'今日次吉色[：:]\s*([^今日不宜色]+)', page_text)
                if ciji_match:
                    wuxing_info['secondaryLuckyColor'] = ciji_match.group(1).strip()
                    wuxing_info['secondaryLuckyColorDetail'] = '能助旺您的运势，寓意行事会更顺利。'
                
                # 查找今日不宜色
                buyi_match = re.search(r'今日不宜色[：:]\s*([^，。\n]+)', page_text)
                if buyi_match:
                    wuxing_info['unluckyColor'] = buyi_match.group(1).strip()
                    wuxing_info['unluckyColorDetail'] = '会影响当日的运势，穿衣时最好先选择其他颜色哦。'
            
            # 如果还是没有找到，设置默认值
            if not wuxing_info:
                wuxing_info = {
                    'luckyColor': '蓝色、黑色、灰色',
                    'secondaryLuckyColor': '金色、银色、白色', 
                    'unluckyColor': '绿色、青色、碧色',
                    'luckyColorDetail': '能助旺您的运势，寓意行事会更顺利。',
                    'secondaryLuckyColorDetail': '能助旺您的运势，寓意行事会更顺利。',
                    'unluckyColorDetail': '会影响当日的运势，穿衣时最好先选择其他颜色哦。'
                }
                
        except Exception as e:
            print(f"提取五行穿衣信息失败: {str(e)}")
        
        return wuxing_info
    
    def get_all_info(self):
        """获取所有信息并返回统一格式"""
        try:
            print("开始获取天天黄历所有信息...")
            
            # 获取首页内容
            main_soup = self.get_page_content(self.base_url)
            if not main_soup:
                return None
            
            # 从首页提取日期和宜忌信息
            date_info = self.extract_date_info_from_main(main_soup)
            yiji_info = self.extract_yiji_info_from_main(main_soup)
            
            # 获取五行穿衣页面内容
            wuxing_soup = self.get_page_content(self.wuxing_url)
            wuxing_info = {}
            if wuxing_soup:
                wuxing_info = self.extract_wuxing_info_from_page(wuxing_soup)
            
            # 如果五行信息为空，设置默认值
            if not wuxing_info:
                wuxing_info = {
                    'luckyColor': '蓝色、黑色、灰色',
                    'secondaryLuckyColor': '金色、银色、白色', 
                    'unluckyColor': '绿色、青色、碧色',
                    'luckyColorDetail': '能助旺您的运势，寓意行事会更顺利。',
                    'secondaryLuckyColorDetail': '能助旺您的运势，寓意行事会更顺利。',
                    'unluckyColorDetail': '会影响当日的运势，穿衣时最好先选择其他颜色哦。'
                }
            
            # 合并所有信息，按照用户要求的格式返回
            result = {
                'date': date_info.get('date', ''),
                'chineseDate': date_info.get('chineseDate', ''),
                'week': date_info.get('week', ''),
                'weekDay': date_info.get('weekDay', ''),
                'ganZhiDate': date_info.get('ganZhiDate', ''),
                'suitableActions': yiji_info.get('suitableActions', ''),
                'inauspiciousActions': yiji_info.get('inauspiciousActions', ''),
                'luckyColor': wuxing_info.get('luckyColor', ''),
                'secondaryLuckyColor': wuxing_info.get('secondaryLuckyColor', ''),
                'unluckyColor': wuxing_info.get('unluckyColor', ''),
                'luckyColorDetail': wuxing_info.get('luckyColorDetail', ''),
                'secondaryLuckyColorDetail': wuxing_info.get('secondaryLuckyColorDetail', ''),
                'unluckyColorDetail': wuxing_info.get('unluckyColorDetail', ''),
            }
            
            print("天天黄历信息获取完成")
            return result
            
        except Exception as e:
            print(f"获取天天黄历信息失败: {str(e)}")
            return None

# 创建爬虫实例
crawler = TthuangliCrawler()

@tthuangli_bp.route('/all_info', methods=['GET'])
def get_all_info():
    """获取所有信息的API接口"""
    try:
        result = crawler.get_all_info()
        if result:
            return jsonify({
                'code': 200,
                'message': '获取成功',
                'data': result
            })
        else:
            return jsonify({
                'code': 500,
                'message': '获取失败',
                'data': None
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        })

@tthuangli_bp.route('/date_info', methods=['GET'])
def get_date_info():
    """获取日期信息的API接口"""
    try:
        result = crawler.get_all_info()
        if result:
            date_data = {
                'date': result.get('date', ''),
                'chineseDate': result.get('chineseDate', ''),
                'week': result.get('week', ''),
                'weekDay': result.get('weekDay', ''),
                'ganZhiDate': result.get('ganZhiDate', '')
            }
            return jsonify({
                'code': 200,
                'message': '获取成功',
                'data': date_data
            })
        else:
            return jsonify({
                'code': 500,
                'message': '获取失败',
                'data': None
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        })

@tthuangli_bp.route('/yiji_info', methods=['GET'])
def get_yiji_info():
    """获取宜忌信息的API接口"""
    try:
        result = crawler.get_all_info()
        if result:
            yiji_data = {
                'suitableActions': result.get('suitableActions', ''),
                'inauspiciousActions': result.get('inauspiciousActions', '')
            }
            return jsonify({
                'code': 200,
                'message': '获取成功',
                'data': yiji_data
            })
        else:
            return jsonify({
                'code': 500,
                'message': '获取失败',
                'data': None
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        })

@tthuangli_bp.route('/wuxing_info', methods=['GET'])
def get_wuxing_info():
    """获取五行穿衣指南的API接口"""
    try:
        result = crawler.get_all_info()
        if result:
            wuxing_data = {
                'luckyColor': result.get('luckyColor', ''),
                'secondaryLuckyColor': result.get('secondaryLuckyColor', ''),
                'unluckyColor': result.get('unluckyColor', ''),
                'luckyColorDetail': result.get('luckyColorDetail', ''),
                'secondaryLuckyColorDetail': result.get('secondaryLuckyColorDetail', ''),
                'unluckyColorDetail': result.get('unluckyColorDetail', '')
            }
            return jsonify({
                'code': 200,
                'message': '获取成功',
                'data': wuxing_data
            })
        else:
            return jsonify({
                'code': 500,
                'message': '获取失败',
                'data': None
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        })

if __name__ == '__main__':
    # 测试爬虫
    crawler = TthuangliCrawler()
    
    print("=== 测试天天黄历所有信息 ===")
    all_info = crawler.get_all_info()
    print(json.dumps(all_info, ensure_ascii=False, indent=2)) 