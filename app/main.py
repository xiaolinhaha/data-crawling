from fastapi import FastAPI
from .crawler import get_baidu_slogan
from .crawlers.direct_crawler import crawl_website_to_word

app = FastAPI(
    title="金融新闻爬虫API",
    description="爬取金融时报网站的最新新闻和评论，并生成Word文档"
)

@app.get("/")
async def hello_world():
    return {"message": "欢迎使用金融新闻爬虫API"}

@app.get("/baidu-slogan")
async def fetch_baidu_slogan():
    """
    爬取百度首页的一条文案
    """
    slogan = get_baidu_slogan()
    return {"baidu_slogan": slogan}

@app.get("/financial-news")
async def fetch_financial_news():
    """
    爬取金融时报最新的一条新闻，从list-left区域提取内容并生成Word文档
    """
    result = crawl_website_to_word()
    return result 