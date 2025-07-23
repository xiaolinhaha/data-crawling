#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
股票指数爬虫
"""

import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random
from flask import Blueprint, request, jsonify

# 创建蓝图
stock_index_bp = Blueprint('stock_index', __name__)

class StockIndexCrawler:
    """
    股票指数爬虫类
    """

    def __init__(self):
        """
        初始化
        """
        self.name = "股票指数爬虫"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive'
        }
        
    def read_indices(self):
        """
        返回硬编码的指数列表，替代从Excel读取
        
        Returns:
            list: 股票指数信息列表，每个元素包含类型和URL
        """
        # 硬编码指数列表，替代从Excel读取
        indices = [
            {'type': '上证指数', 'url': 'https://quote.eastmoney.com/zs000001.html'},
            {'type': '深证成指', 'url': 'https://quote.eastmoney.com/zs399001.html'},
            {'type': '创业板指', 'url': 'https://quote.eastmoney.com/zs399006.html'},
            {'type': '上证50', 'url': 'https://quote.eastmoney.com/zs000016.html'},
            {'type': '科创50', 'url': 'https://quote.eastmoney.com/zs000688.html'},
            {'type': '北证50', 'url': 'https://quote.eastmoney.com/zs899050.html'},
            {'type': '沪深300', 'url': 'https://quote.eastmoney.com/zs000300.html'},
            {'type': '恒生指数', 'url': 'https://quote.eastmoney.com/gb/zsHSI.html'},
            {'type': '道琼斯指数', 'url': 'https://quote.eastmoney.com/gb/zsDJIA.html'},
            {'type': '标普500', 'url': 'https://quote.eastmoney.com/us/IVV.html'},
            {'type': '纳斯达克指数', 'url': 'https://quote.eastmoney.com/gb/zsNDX.html'},
            {'type': 'COMEX黄金', 'url': 'https://quote.eastmoney.com/globalfuture/GC00Y.html'}
        ]
        
        return indices
    
    def crawl_index_data(self, url):
        """
        爬取指定URL的股票指数数据
        
        Args:
            url: 股票指数页面URL
            
        Returns:
            dict: 股票指数数据
        """
        try:
            # 发送请求获取页面内容
            response = requests.get(url, headers=self.headers, timeout=10)
            
            # 检查响应状态
            if response.status_code != 200:
                return None
                
            # 将响应内容解析为HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取股票名称
            stock_name = None
            stock_code = None
            if soup.title:
                match = re.search(r'(.+?)\((\d+)\)', soup.title.text)
                if match:
                    stock_name = match.group(1).strip()
                    stock_code = match.group(2).strip()
            
            if not stock_name:
                # 尝试从其他位置提取股票名称
                name_elem = soup.select_one('.quote_title_name')
                if name_elem:
                    stock_name = name_elem.text.strip()
            
            # 提取quotecode和market变量
            quote_code = None
            market = None
            
            scripts = soup.find_all('script')
            var_pattern = re.compile(r'var\s+(quotecode|market|code)\s*=\s*["\']?([^"\';\s]+)["\']?;')
            
            for script in scripts:
                if script.string:
                    for var_name, var_value in var_pattern.findall(script.string):
                        if var_name == 'quotecode':
                            quote_code = var_value
                        elif var_name == 'market':
                            market = var_value
                        elif var_name == 'code' and not stock_code:
                            stock_code = var_value
            
            # 判断是否为特殊市场商品（黄金等）
            is_special_commodity = False
            if 'globalfuture' in url or 'future' in url:
                is_special_commodity = True
            
            # 如果提取到了quotecode且不是特殊商品，尝试使用东方财富网API获取实时数据
            if (quote_code or (market and stock_code)) and not is_special_commodity:
                if quote_code:
                    api_data = self.get_stock_data_from_api(quote_code)
                else:
                    full_code = f"{market}.{stock_code}"
                    api_data = self.get_stock_data_from_api(full_code)
                
                if api_data:
                    # 使用页面标题或URL中的名称，如果API返回的名称不明确
                    display_name = api_data.get("name", "未知股票")
                    if display_name == "-" or display_name == "未知股票":
                        if stock_name:
                            display_name = stock_name
                
                    return {
                        "name": display_name,
                        "url": url,
                        "current_price": api_data.get("current_price", "N/A"),
                        "price_change": api_data.get("price_change", "N/A"),
                        "price_change_percent": api_data.get("price_change_percent", "N/A"),
                        "market": api_data.get("market", "未知市场"),
                        "code": api_data.get("code", "")
                    }
            
            # 如果无法通过API获取数据，回退到从页面中提取数据
            # 从页面中提取数据
            current_price = None
            price_change = None
            price_change_percent = None
            
            # 1. 尝试从页面直接提取价格数据
            # 东方财富网通常将价格放在.zxj元素中
            zxj_elem = soup.select_one('.zxj')
            if zxj_elem:
                # 价格通常在第一个span中
                price_span = zxj_elem.select_one('span')
                if price_span:
                    current_price = price_span.text.strip()
            
            # 东方财富网通常将涨跌信息放在.zd元素中
            zd_elem = soup.select_one('.zd')
            if zd_elem:
                # 涨跌额和涨跌幅分别在不同的span中
                zd_spans = zd_elem.select('span')
                if len(zd_spans) >= 2:
                    price_change = zd_spans[0].text.strip()
                    price_change_percent = zd_spans[1].text.strip()
            
            # 2. 如果上面方法失败，尝试从页面中的脚本变量中提取数据
            if not current_price or not price_change or not price_change_percent:
                # 提取页面中的JavaScript变量
                scripts = soup.find_all('script')
                stock_data = {}
                
                # 查找包含价格数据的变量
                price_pattern = re.compile(r'var\s+(f43|f44|f45|f48|price|zxj|zde|zdf)\s*=\s*["\']?([^"\';\s]+)["\']?;')
                
                for script in scripts:
                    if script.string:
                        for var_name, var_value in price_pattern.findall(script.string):
                            stock_data[var_name] = var_value
                
                # 从提取的变量中获取价格数据
                if 'f43' in stock_data:  # 当前价格
                    current_price = stock_data['f43']
                elif 'price' in stock_data:
                    current_price = stock_data['price']
                elif 'zxj' in stock_data:
                    current_price = stock_data['zxj']
                
                if 'f44' in stock_data:  # 涨跌额
                    price_change = stock_data['f44']
                elif 'zde' in stock_data:
                    price_change = stock_data['zde']
                
                if 'f45' in stock_data:  # 涨跌幅
                    price_change_percent = stock_data['f45']
                elif 'zdf' in stock_data:
                    price_change_percent = stock_data['zdf']
                    # 确保涨跌幅包含百分号
                    if price_change_percent and '%' not in price_change_percent:
                        price_change_percent = price_change_percent + '%'
            
            # 3. 如果仍然无法获取数据，尝试从页面中查找具有特定class的元素
            if not current_price:
                # 尝试查找常见的价格元素
                price_selectors = [
                    '.price_down', '.price_up', '.stock-current', '.new_price', 
                    '.last_price', '#price9', '.em_item_price', '.cur', '.last'
                ]
                for selector in price_selectors:
                    elements = soup.select(selector)
                    if elements:
                        current_price = elements[0].text.strip()
                        break
            
            # 尝试通过不同选择器提取涨跌信息
            if not price_change or not price_change_percent:
                change_selectors = [
                    '.change', '.cbl_change', '.cbl_differs', '.cbl_deal', 
                    '.change-up', '.change-down', '.chl_change', '.last_change'
                ]
                for selector in change_selectors:
                    elements = soup.select(selector)
                    if elements and len(elements) >= 1:
                        change_text = elements[0].text.strip()
                        if '(' in change_text and ')' in change_text:
                            # 一些网站将涨跌额和涨跌幅放在一个元素中，如：+20.00 (+1.5%)
                            parts = change_text.split('(')
                            if len(parts) == 2:
                                price_change = parts[0].strip()
                                price_change_percent = '(' + parts[1].strip()
                        else:
                            price_change = change_text
                        break
            
            # 4. 尝试从brief_info部分提取数据
            if not current_price or not price_change or not price_change_percent:
                brief_info = soup.select_one('.brief_info')
                if brief_info:
                    info_items = brief_info.select('li')
                    for item in info_items:
                        text = item.text.strip()
                        if '涨跌幅' in text:
                            price_change_percent = text.split(':', 1)[1].strip()
                        elif '涨跌额' in text:
                            price_change = text.split(':', 1)[1].strip()
                        elif '最新价' in text or '现价' in text:
                            current_price = text.split(':', 1)[1].strip()
            
            # 对于期货和商品市场，还可以尝试提取特定位置的数据
            if is_special_commodity:
                # 尝试从.quoteboard元素提取数据
                quoteboard = soup.select_one('.quoteboard')
                if quoteboard:
                    price_elem = quoteboard.select_one('.cur')
                    if price_elem:
                        current_price = price_elem.text.strip()
                    
                    change_elems = quoteboard.select('.change')
                    if len(change_elems) >= 2:
                        price_change = change_elems[0].text.strip()
                        price_change_percent = change_elems[1].text.strip()
            
            # 确保我们至少有股票名称
            if not stock_name:
                stock_name = "未知股票"
            
            # 获取市场信息
            market_info = "商品期货" if is_special_commodity else "未知市场"
            
            # 构建返回数据
            stock_data = {
                "name": stock_name,
                "url": url,
                "current_price": current_price or "N/A",
                "price_change": price_change or "N/A",
                "price_change_percent": price_change_percent or "N/A",
                "market": market_info,
                "code": stock_code or ""
            }
            
            return stock_data
        except Exception as e:
            return None
    
    def get_stock_data_from_api(self, quote_code):
        """
        从东方财富网API获取股票数据
        
        Args:
            quote_code: 股票代码，例如 "1.000001"（上证指数）或 "0.399001"（深证成指）
            
        Returns:
            dict: 股票数据
        """
        try:
            # 使用东方财富网的API获取股票数据
            api_url = f"https://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": quote_code,
                # API字段说明:
                # f43: 最新价(乘以100)
                # f44: 最新价(乘以100，用于比较)
                # f45: 涨跌幅，未格式化(乘以100)
                # f46: 最高价(乘以100)
                # f47: 成交量
                # f48: 成交额
                # f49: 量比
                # f50: 涨速(%)
                # f57: 代码
                # f58: 名称
                # f60: 昨收价(乘以100)
                # f107: 市场代码(0:深市, 1:沪市, 3:港股)
                # f162: 换手率
                # f168: 涨跌额(乘以100)
                # f169: 涨跌幅，格式化(乘以100)
                # f170: 最高涨幅(乘以100)
                "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f107,f162,f168,f169,f170,f171,f116,f117,f58",
                "ut": "e1e6871893c6386c5ff6967026016627",
                "_": int(time.time() * 1000)
            }
            
            response = requests.get(api_url, params=params, headers=self.headers)
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if data and "data" in data:
                stock_data = data["data"]
                
                if not stock_data:
                    return None
                
                # 解析API返回的数据
                result = {}
                
                # 获取名称
                if "f58" in stock_data:
                    result["name"] = stock_data["f58"]
                elif "f14" in stock_data:
                    result["name"] = stock_data["f14"]
                
                # 获取市场信息
                if "f107" in stock_data:
                    market_code = stock_data["f107"]
                    market_name = "未知市场"
                    if market_code == 0:
                        market_name = "深交所"
                    elif market_code == 1:
                        market_name = "上交所"
                    elif market_code == 3:
                        market_name = "港交所"
                    elif market_code == 100:
                        market_name = "国际指数"
                    elif market_code == 107:
                        market_name = "美股ETF"
                    elif market_code == 102:
                        market_name = "商品期货"
                    result["market"] = market_name
                
                # 获取股票代码
                if "f57" in stock_data:
                    result["code"] = stock_data["f57"]
                
                # 获取当前价格 (f43) - 价格需要除以100
                if "f43" in stock_data:
                    price_value = stock_data["f43"]
                    # 价格需要除以100
                    price_value = price_value / 100.0
                    result["current_price"] = f"{price_value:.2f}"
                
                # 获取涨跌额 (f169) - 需要除以100
                if "f169" in stock_data:
                    change_value = stock_data["f169"]
                    # 涨跌额需要除以100
                    change_value = change_value / 100.0
                    result["price_change"] = f"{change_value:.2f}"
                # 如果f169不存在，使用f44-f60计算
                elif "f44" in stock_data and "f60" in stock_data:
                    change_value = stock_data["f44"] - stock_data["f60"]
                    # 涨跌额需要除以100
                    change_value = change_value / 100.0
                    result["price_change"] = f"{change_value:.2f}"
                
                # 获取涨跌幅 (f170) - 需要除以100
                if "f170" in stock_data:
                    percent_value = stock_data["f170"]
                    # 涨跌幅需要除以100
                    percent_value = percent_value / 100.0
                    # 确保格式正确，正值不显示加号
                    result["price_change_percent"] = f"{percent_value:.2f}%"
                # 如果f170不存在，尝试使用f45
                elif "f45" in stock_data:
                    percent_value = stock_data["f45"]
                    # 涨跌幅需要除以100
                    percent_value = percent_value / 100.0
                    # 确保格式正确，正值不显示加号
                    result["price_change_percent"] = f"{percent_value:.2f}%"
                
                return result
            else:
                return None
        except Exception as e:
            return None
    
    def crawl(self, index=None):
        """
        爬取股票指数数据
        
        Args:
            index: 要爬取的股票指数索引，None表示获取全部
            
        Returns:
            dict: 包含股票数据的响应
        """
        # 读取指数列表
        indices = self.read_indices()
        
        if not indices:
            return {
                "status": "error",
                "message": "未能读取到股票指数信息",
                "data": []
            }
        
        try:
            # 如果不指定索引，爬取所有指数
            if index is None:
                # 分离COMEX黄金和其他指数
                comex_gold_indices = []
                other_indices = []
                
                for idx, index_info in enumerate(indices):
                    if 'COMEX黄金' in index_info['type'] or 'globalfuture' in index_info['url']:
                        comex_gold_indices.append((idx, index_info))
                    else:
                        other_indices.append((idx, index_info))
                
                # 使用批量API获取其他指数数据
                all_data = []
                if other_indices:
                    batch_data = self.batch_get_indices(other_indices)
                    if batch_data:
                        all_data.extend(batch_data)
                
                # 单独处理COMEX黄金
                for i, (idx, index_info) in enumerate(comex_gold_indices):
                    # 使用专门的API获取COMEX黄金数据
                    stock_data = self.get_comex_gold_data()
                    
                    if stock_data:
                        # 添加类型信息
                        stock_data["type"] = index_info['type']
                        
                        # 对于COMEX黄金指数，优先使用Excel中的类型作为名称
                        if stock_data.get("name") == "-" or "未知" in stock_data.get("name", ""):
                            stock_data["name"] = index_info['type']
                        
                        all_data.append(stock_data)
                
                # 确保结果消息反映实际获取到的数据数量
                success_count = len(all_data)
                return {
                    "status": "success",
                    "message": f"成功获取{success_count}个股票指数数据",
                    "data": all_data
                }
            else:
                # 爬取指定索引的指数
                if index < 0 or index >= len(indices):
                    index = 0
                    
                # 获取指定索引的指数信息
                index_info = indices[index]
                url = index_info['url']
                
                # 爬取数据
                stock_data = self.crawl_index_data(url)
                
                if stock_data:
                    # 添加类型信息
                    stock_data["type"] = index_info['type']
                    
                    # 对于国际指数，优先使用Excel中的类型作为名称
                    if stock_data.get("name") == "-" or "未知" in stock_data.get("name", ""):
                        stock_data["name"] = index_info['type']
                    
                    return {
                        "status": "success",
                        "message": f"成功获取股票指数数据: {stock_data['name']}",
                        "data": [stock_data]
                    }
                else:
                    return {
                        "status": "error",
                        "message": "爬取股票数据失败",
                        "data": []
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"爬取过程中出错: {str(e)}",
                "data": []
            }
    
    def batch_get_indices(self, index_list):
        """
        批量获取多个股票指数数据
        
        Args:
            index_list: 指数信息列表，每项为(索引, 指数信息)元组
            
        Returns:
            list: 股票指数数据列表
        """
        try:
            # 构建secids参数
            secids = []
            url_to_index_info = {}
            
            for idx, index_info in index_list:
                url = index_info['url']
                
                # 从URL中提取股票代码信息
                quote_code = None
                
                if 'zs000001' in url:
                    quote_code = '1.000001'  # 上证指数
                elif 'zs399001' in url:
                    quote_code = '0.399001'  # 深证成指
                elif 'zs399006' in url:
                    quote_code = '0.399006'  # 创业板指
                elif 'zs000016' in url:
                    quote_code = '1.000016'  # 上证50
                elif 'zs000688' in url:
                    quote_code = '1.000688'  # 科创50
                elif 'zs899050' in url:
                    quote_code = '0.899050'  # 北证50
                elif 'zs000300' in url:
                    quote_code = '1.000300'  # 沪深300
                elif 'zsHSI' in url:
                    quote_code = '100.HSI'   # 恒生指数
                elif 'zsDJIA' in url:
                    quote_code = '100.DJIA'  # 道琼斯指数
                elif 'us/IVV' in url:
                    quote_code = '107.IVV'   # 标普500ETF
                elif 'zsNDX' in url:
                    quote_code = '100.NDX'   # 纳斯达克指数
                
                if quote_code:
                    secids.append(quote_code)
                    url_to_index_info[quote_code] = index_info
            
            if not secids:
                return []
            
            # 构建批量API请求
            secids_str = ','.join(secids)
            
            # 使用正确的批量API接口
            api_url = "https://push2.eastmoney.com/api/qt/ulist/get"
            params = {
                "fltt": 1,
                "invt": 2,
                "fields": "f12,f13,f14,f1,f2,f3,f4,f152,f6,f104,f105,f106,f43,f44,f45,f46,f47,f48,f49,f50,f57,f58,f60,f107,f168,f169,f170,f171",
                "secids": secids_str,
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "pn": 1,
                "np": 1,
                "pz": 20,
                "dect": 1,
                "wbp2u": "|0|0|0|web",
                "_": int(time.time() * 1000)
            }
            
            # 随机生成Cookie参数，确保请求不被缓存
            cookies = {
                'qgqp_b_id': f'{random.randint(1000000000, 9999999999)}',
                'st_si': f'{random.randint(10000000000000, 99999999999999)}',
                'st_pvi': f'{random.randint(10000000000000, 99999999999999)}',
                'st_sp': f'{int(time.time())}'
            }
            
            # 更新headers，增加随机性
            headers = self.headers.copy()
            headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            headers['Pragma'] = 'no-cache'
            headers['Expires'] = '0'
            
            response = requests.get(api_url, params=params, headers=headers, cookies=cookies)
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            if data and "data" in data and "diff" in data["data"]:
                stocks_data = data["data"]["diff"]
                result = []
                
                # 字段映射，将API返回字段映射到我们需要的字段
                field_map = {
                    "f12": "code",        # 股票代码
                    "f14": "name",        # 股票名称
                    "f13": "market_id",   # 市场代码
                    "f2": "current_price",# 最新价
                    "f4": "price_change", # 涨跌额
                    "f3": "price_change_percent"  # 涨跌幅
                }
                
                # 遍历返回的股票数据
                for stock_item in stocks_data:
                    parsed_data = {}
                    
                    # 根据字段映射提取数据
                    for api_field, our_field in field_map.items():
                        if api_field in stock_item and stock_item[api_field] is not None:
                            parsed_data[our_field] = stock_item[api_field]
                    
                    # 获取市场类型
                    if "market_id" in parsed_data:
                        market_code = parsed_data["market_id"]
                        market_name = self.get_market_name(market_code)
                        parsed_data["market"] = market_name
                        
                    # 格式化价格和涨跌幅
                    if "current_price" in parsed_data:
                        price = parsed_data["current_price"]
                        # 东方财富API返回的价格需要除以100
                        price = price / 100.0
                        parsed_data["current_price"] = f"{price:.2f}"
                    
                    if "price_change" in parsed_data:
                        price_change = parsed_data["price_change"]
                        # 涨跌额也需要除以100
                        price_change = price_change / 100.0
                        parsed_data["price_change"] = f"{price_change:.2f}"
                    
                    if "price_change_percent" in parsed_data:
                        percent = parsed_data["price_change_percent"]
                        # 涨跌幅也需要除以100
                        percent = percent / 100.0
                        parsed_data["price_change_percent"] = f"{percent:.2f}%"
                    
                    # 获取对应的指数信息
                    secid = None
                    if "code" in parsed_data and "market_id" in parsed_data:
                        code = parsed_data["code"]
                        market_id = parsed_data["market_id"]
                        secid = f"{market_id}.{code}"
                    
                    if secid and secid in url_to_index_info:
                        index_info = url_to_index_info[secid]
                        parsed_data["url"] = index_info["url"]
                        parsed_data["type"] = index_info["type"]
                        
                        # 如果名称不存在或为空，使用Excel中的类型名称
                        if "name" not in parsed_data or not parsed_data["name"]:
                            parsed_data["name"] = index_info["type"]
                        
                        result.append(parsed_data)
                    else:
                        # 尝试根据名称匹配
                        for code, info in url_to_index_info.items():
                            if "name" in parsed_data and parsed_data["name"] in info["type"]:
                                parsed_data["url"] = info["url"]
                                parsed_data["type"] = info["type"]
                                result.append(parsed_data)
                                break
                
                return result
            else:
                # 如果批量API失败，回退到单个请求
                result = []
                
                for idx, index_info in index_list:
                    url = index_info['url']
                    
                    # 爬取数据
                    stock_data = self.crawl_index_data(url)
                    
                    if stock_data:
                        # 添加类型信息
                        stock_data["type"] = index_info['type']
                        
                        # 对于国际指数，优先使用Excel中的类型作为名称
                        if stock_data.get("name") == "-" or "未知" in stock_data.get("name", ""):
                            stock_data["name"] = index_info['type']
                        
                        result.append(stock_data)
                        
                        # 添加随机延迟，避免请求过快
                        if idx < len(index_list) - 1:
                            delay = random.uniform(0.5, 1.0)
                            time.sleep(delay)
                
                return result
                
        except Exception as e:
            return []
    
    def get_market_name(self, market_code):
        """获取市场名称"""
        market_name = "未知市场"
        if market_code == 0:
            market_name = "深交所"
        elif market_code == 1:
            market_name = "上交所"
        elif market_code == 3:
            market_name = "港交所"
        elif market_code == 100:
            market_name = "国际指数"
        elif market_code == 107:
            market_name = "美股ETF"
        elif market_code == 102:
            market_name = "商品期货"
        return market_name

    def get_comex_gold_data(self):
        """
        获取COMEX黄金数据的专用API
        
        Returns:
            dict: 黄金价格数据
        """
        try:
            # 使用静态API接口获取COMEX黄金数据
            api_url = "https://futsseapi.eastmoney.com/static/101_GC00Y_qt"
            
            # 生成随机的jQuery回调名和时间戳，避免缓存
            current_timestamp = int(time.time() * 1000)
            random_jquery = f"jQuery{random.randint(10000000000000000000, 99999999999999999999)}_{current_timestamp}"
            
            params = {
                "callbackName": random_jquery,
                "field": "name,sc,dm,p,zsjd,zdf,zde,utime,o,zjsj,qrspj,h,l,mrj,mcj,vol,cclbh,zt,dt,np,wp,ccl,rz,cje,mcl,mrl,jjsj,j,lb,zf",
                "token": "1101ffec61617c99be287c1bec3085ff",
                "_": current_timestamp
            }
            
            # 生成随机Cookie，确保每次请求获取最新数据
            cookies = {
                'qgqp_b_id': f'{random.randint(1000000000, 9999999999)}',
                'st_si': f'{random.randint(10000000000000, 99999999999999)}',
                'st_pvi': f'{random.randint(10000000000000, 99999999999999)}',
                'st_sp': f'{int(time.time())}',
                'HAList': f'ty-101-GC00Y-COMEX%u9EC4%u91D1,ty-{int(time.time() * 100)}'
            }
            
            # 更新headers，避免缓存
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Referer': 'https://quote.eastmoney.com/globalfuture/GC00Y.html',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
            
            response = requests.get(api_url, params=params, headers=headers, cookies=cookies)
            
            if response.status_code != 200:
                return None
            
            # 解析JSONP响应
            content = response.text
            
            # 从JSONP响应中提取JSON部分
            match = re.search(r'jQuery[^(]*\((.*)\)', content)
            if not match:
                return None
                
            json_str = match.group(1)
            data = json.loads(json_str)
            
            # 解析API返回的数据 - 数据在qt子对象中
            if data and "qt" in data:
                qt_data = data["qt"]
                result = {
                    "name": "COMEX黄金",
                    "code": "GC00Y",
                    "url": "https://quote.eastmoney.com/globalfuture/GC00Y.html",
                    "market": "商品期货"
                }
                
                # 提取价格和涨跌信息
                if "p" in qt_data:  # 最新价
                    result["current_price"] = f"{qt_data['p']:.2f}" if isinstance(qt_data['p'], (int, float)) else qt_data['p']
                
                if "zde" in qt_data:  # 涨跌额
                    result["price_change"] = f"{qt_data['zde']:.2f}" if isinstance(qt_data['zde'], (int, float)) else qt_data['zde']
                
                if "zdf" in qt_data:  # 涨跌幅
                    percent_value = qt_data['zdf']
                    if isinstance(percent_value, (int, float)):
                        result["price_change_percent"] = f"{percent_value:.2f}%"
                    else:
                        result["price_change_percent"] = percent_value
                
                return result
            else:
                return None
        except Exception as e:
            return None

@stock_index_bp.route('/stock_index')
def get_stock_index():
    """
    获取股票指数数据的API接口
    
    Returns:
        JSON: 包含股票数据的响应
    """
    # 创建爬虫实例并爬取数据
    crawler = StockIndexCrawler()
    result = crawler.crawl()
    
    # 返回完整响应，包含status和message字段
    return jsonify(result)

# 测试代码
if __name__ == "__main__":
    crawler = StockIndexCrawler()
    result = crawler.crawl()
    print(json.dumps(result, ensure_ascii=False, indent=2)) 