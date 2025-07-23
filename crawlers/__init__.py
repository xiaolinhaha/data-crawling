from flask import Blueprint

from .financial_news_crawler import financial_news_bp
from .cnfin_crawler import cnfin_bp
from .east_money_crawler import east_money_bp
from .east_money_focus_crawler import east_money_focus_bp
from .east_money_lczx_crawler import east_money_lczx_bp
from .sina_finance_crawler import sina_finance_bp
from .sina_stock_crawler import sina_stock_bp
from .shenlanbao_crawler import shenlanbao_bp
from .cs_company_crawler import cs_company_bp
from .sohu_policy_crawler import sohu_policy_bp
from .eastmoney_antifraud_crawler import eastmoney_antifraud_bp
from .cnfin_risk_crawler import cnfin_risk_bp
from .sohu_finance_crawler import sohu_finance_bp
from .eastmoney_international_crawler import eastmoney_international_bp
from .huanqiu_world_crawler import huanqiu_world_bp
from .people_health_crawler import people_health_bp
from .people_society_crawler import people_society_bp
from .people_science_crawler import people_science_bp
from .ndrc_policy_crawler import ndrc_policy_bp
from .chinapolicy_crawler import chinapolicy_bp
from .stock_index_crawler import stock_index_bp

# 创建爬虫模块的主蓝图
crawlers_bp = Blueprint('crawlers', __name__)

# 注册各个爬虫的蓝图
crawlers_bp.register_blueprint(financial_news_bp, url_prefix='/financial_news')
crawlers_bp.register_blueprint(cnfin_bp, url_prefix='/cnfin')
crawlers_bp.register_blueprint(east_money_bp, url_prefix='/east_money')
crawlers_bp.register_blueprint(east_money_focus_bp, url_prefix='/east_money_focus')
crawlers_bp.register_blueprint(east_money_lczx_bp, url_prefix='/east_money_lczx')
crawlers_bp.register_blueprint(sina_finance_bp, url_prefix='/sina_finance')
crawlers_bp.register_blueprint(sina_stock_bp, url_prefix='/sina_stock')
crawlers_bp.register_blueprint(shenlanbao_bp, url_prefix='/shenlanbao')
crawlers_bp.register_blueprint(cs_company_bp, url_prefix='/cs_company')
crawlers_bp.register_blueprint(sohu_policy_bp, url_prefix='/sohu_policy')
crawlers_bp.register_blueprint(eastmoney_antifraud_bp, url_prefix='/eastmoney_antifraud')
crawlers_bp.register_blueprint(cnfin_risk_bp, url_prefix='/cnfin_risk')
crawlers_bp.register_blueprint(sohu_finance_bp, url_prefix='/sohu_finance')
crawlers_bp.register_blueprint(eastmoney_international_bp, url_prefix='/eastmoney_international')
crawlers_bp.register_blueprint(huanqiu_world_bp, url_prefix='/huanqiu_world')
crawlers_bp.register_blueprint(people_health_bp, url_prefix='/people_health')
crawlers_bp.register_blueprint(people_society_bp, url_prefix='/people_society')
crawlers_bp.register_blueprint(people_science_bp, url_prefix='/people_science')
crawlers_bp.register_blueprint(ndrc_policy_bp, url_prefix='/ndrc_policy')
crawlers_bp.register_blueprint(chinapolicy_bp, url_prefix='/chinapolicy')
crawlers_bp.register_blueprint(stock_index_bp, url_prefix='/stock_index')

# 爬虫索引路由
@crawlers_bp.route('/', methods=['GET'])
def list_crawlers():
    """列出所有可用的爬虫"""
    crawlers = [
        {
            'name': '中国金融新闻网',
            'endpoint': '/api/crawlers/financial_news/financial_news',
            'description': '爬取中国金融新闻网的最新新闻'
        },
        {
            'name': '中国金融信息网',
            'endpoint': '/api/crawlers/cnfin/cnfin_news',
            'description': '爬取中国金融信息网的最新新闻'
        },
        {
            'name': '东方财富网评论精华',
            'endpoint': '/api/crawlers/east_money/east_money_news',
            'description': '爬取东方财富网评论精华栏目的最新文章'
        },
        {
            'name': '东方财富网焦点',
            'endpoint': '/api/crawlers/east_money_focus/east_money_focus',
            'description': '爬取东方财富网焦点页面的重要文章'
        },
        {
            'name': '东方财富网理财资讯',
            'endpoint': '/api/crawlers/east_money_lczx/east_money_lczx_news',
            'description': '爬取东方财富网理财资讯栏目的最新文章'
        },
        {
            'name': '新浪财经基金',
            'endpoint': '/api/crawlers/sina_finance/sina_finance_news',
            'description': '爬取新浪财经基金首页顶部新闻'
        },
        {
            'name': '新浪财经股票',
            'endpoint': '/api/crawlers/sina_stock/sina_stock_news',
            'description': '爬取新浪财经股票页面顶部新闻'
        },
        {
            'name': '深蓝保保险攻略',
            'endpoint': '/api/crawlers/shenlanbao/shenlanbao_article',
            'description': '爬取深蓝保保险攻略页面的最新文章'
        },
        {
            'name': '中证网公司要闻',
            'endpoint': '/api/crawlers/cs_company/cs_company_article',
            'description': '爬取中证网公司要闻页面的最新两条文章'
        },
        {
            'name': '搜狐政策搜索',
            'endpoint': '/api/crawlers/sohu_policy/sohu_policy_news',
            'description': '获取搜狐政策搜索的24小时内最新两条新闻'
        },
        {
            'name': '东方财富网防骗文章',
            'endpoint': '/api/crawlers/eastmoney_antifraud/eastmoney_antifraud_article',
            'description': '获取东方财富网关于防骗的最新文章'
        },
        {
            'name': '中国金融网风险揭示',
            'endpoint': '/api/crawlers/cnfin_risk/cnfin_risk_news',
            'description': '获取中国金融网风险揭示栏目的最新文章'
        },
        {
            'name': '搜狐财经',
            'endpoint': '/api/crawlers/sohu_finance/sohu_finance_news',
            'description': '获取搜狐财经栏目的最新文章'
        },
        {
            'name': '东方财富网国际经济',
            'endpoint': '/api/crawlers/eastmoney_international/eastmoney_international',
            'description': '获取东方财富网国际经济栏目的最新文章'
        },
        {
            'name': '环球网国际新闻',
            'endpoint': '/api/crawlers/huanqiu_world/huanqiu_world_news',
            'description': '获取环球网国际新闻栏目24小时内的最新文章'
        },
        {
            'name': '人民网健康',
            'endpoint': '/api/crawlers/people_health/people_health_topic',
            'description': '获取人民网健康首页大标题'
        },
        {
            'name': '人民网社会',
            'endpoint': '/api/crawlers/people_society/people_society_headline',
            'description': '获取人民网社会版块首页大标题'
        },
        {
            'name': '人民网科普',
            'endpoint': '/api/crawlers/people_science/people_science_headline',
            'description': '获取人民网科普版块首页大标题'
        },
        {
            'name': '国家发改委政策解读',
            'endpoint': '/api/crawlers/ndrc_policy/ndrc_policy_news',
            'description': '获取国家发改委政策解读栏目当天的最新文章'
        },
        {
            'name': '中国政策网解读',
            'endpoint': '/api/crawlers/chinapolicy/chinapolicy_news',
            'description': '获取中国政策网解读栏目24小时内的最新两条文章'
        }
    ]
    
    return {
        'status': 'success',
        'message': '成功获取爬虫列表',
        'data': crawlers
    } 