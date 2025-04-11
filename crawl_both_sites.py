import pandas as pd
import os
import datetime
from app.crawlers.financial_news_crawler import FinancialNewsCrawler
from app.crawlers.east_money_crawler import EastMoneyCrawler
from app.crawlers.cnfin_crawler import CnfinCrawler

def save_to_excel(data, filename=None):
    """将爬取的数据保存到Excel文件"""
    if not data:
        print("没有数据可保存")
        return None
    
    # 确保导出目录存在
    export_dir = "exports"
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    # 如果没有指定文件名，使用当前日期和网站名
    if not filename:
        today = datetime.datetime.now().strftime("%Y%m%d")
        site_name = data.get("Website_Name", "").replace(" ", "_")
        filename = f"{today}_{site_name}_latest.xlsx"
    
    filepath = os.path.join(export_dir, filename)
    
    # 创建DataFrame
    df = pd.DataFrame([data])  # 把单个字典转换为包含一行的DataFrame
    
    # 保存到Excel
    df.to_excel(filepath, index=False, engine='openpyxl')
    print(f"数据已保存到 {filepath}")
    return filepath

def parse_date(date_str):
    """解析日期字符串为日期对象"""
    try:
        # 尝试解析 YYYY-MM-DD 格式
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            # 尝试解析 YYYY-MM-DD HH:MM:SS 格式
            return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            # 返回当前日期
            print(f"无法解析日期: {date_str}")
            return datetime.datetime.now().date()

def crawl_all_sites():
    """爬取所有站点的内容，分别保存每个站点的结果到独立Excel文件"""
    saved_files = []
    today = datetime.datetime.now().strftime("%Y%m%d")
    
    try:
        # 1. 爬取中国金融新闻网
        print("\n爬取中国金融新闻网内容...")
        fn_crawler = FinancialNewsCrawler()
        fn_data = fn_crawler.crawl()
        if fn_data:
            fn_date = fn_data.get("Article_Pub_Date")
            if fn_date:
                print(f"中国金融新闻网最新文章日期: {fn_date}")
                
            # 保存到独立Excel文件
            filename = f"{today}_financial_news_latest.xlsx"
            file_path = save_to_excel(fn_data, filename)
            if file_path:
                saved_files.append(file_path)
                
            print("成功爬取中国金融新闻网")
        else:
            print("爬取中国金融新闻网失败")
        
        # 2. 爬取东方财富网
        print("\n爬取东方财富网内容...")
        em_crawler = EastMoneyCrawler()
        em_data = em_crawler.crawl()
        if em_data:
            em_date = em_data.get("Article_Pub_Date")
            if em_date:
                print(f"东方财富网最新文章日期: {em_date}")
                
            # 保存到独立Excel文件
            filename = f"{today}_east_money_latest.xlsx"
            file_path = save_to_excel(em_data, filename)
            if file_path:
                saved_files.append(file_path)
                
            print("成功爬取东方财富网")
        else:
            print("爬取东方财富网失败")
            
        # 3. 爬取中国金融信息网(Cnfin)
        print("\n爬取中国金融信息网内容...")
        cn_crawler = CnfinCrawler()
        cn_data = cn_crawler.crawl()
        if cn_data:
            cn_date = cn_data.get("Article_Pub_Date")
            if cn_date:
                print(f"中国金融信息网最新文章日期: {cn_date}")
                
            # 保存到独立Excel文件
            filename = f"{today}_cnfin_latest.xlsx"
            file_path = save_to_excel(cn_data, filename)
            if file_path:
                saved_files.append(file_path)
                
            print("成功爬取中国金融信息网")
        else:
            print("爬取中国金融信息网失败")
            
        # 额外保存所有爬取结果到一个综合文件（可选）
        if saved_files:
            all_data = []
            
            # 尝试读取并合并所有Excel文件
            for file in saved_files:
                try:
                    df = pd.read_excel(file)
                    all_data.append(df)
                except Exception as e:
                    print(f"读取文件 {file} 出错: {e}")
            
            if all_data:
                # 合并所有数据
                combined_df = pd.concat(all_data, ignore_index=True)
                
                # 保存到综合Excel文件
                combined_path = os.path.join("exports", f"{today}_all_financial_news.xlsx")
                combined_df.to_excel(combined_path, index=False, engine='openpyxl')
                print(f"所有站点数据已合并保存到 {combined_path}")
                saved_files.append(combined_path)
            
    except Exception as e:
        print(f"爬取过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 返回所有保存的文件路径
    return saved_files

def crawl_both_sites():
    """为保持向后兼容，保留原函数名，但调用新的爬取函数"""
    return crawl_all_sites()

if __name__ == "__main__":
    result_files = crawl_all_sites()
    if result_files:
        print(f"爬取成功，已生成以下文件:")
        for file in result_files:
            print(f"- {file}")
    else:
        print("ERROR: 爬取失败，未能获取任何文章内容")
