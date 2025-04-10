from fastapi import FastAPI
from .crawler import get_baidu_slogan

app = FastAPI(
    title="Hello World API",
    description="一个简单的FastAPI Hello World示例"
)

@app.get("/")
async def hello_world():
    return {"message": "Hello World"}

@app.get("/baidu-slogan")
async def fetch_baidu_slogan():
    """
    爬取百度首页的一条文案
    """
    slogan = get_baidu_slogan()
    return {"baidu_slogan": slogan} 