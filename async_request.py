import logging
logger = logging.getLogger(__name__)
async def send_post_request(session, url, headers, data):
    async with session.post(url=url, headers=headers, json=data, ssl=True) as response:
        if response.status != 200:
            logger.error(f"Failed to post to {url} with status code {response.status},{response.text}")
            return {
                "data":
                    {"outputs":
                         {"result": "本次总结请求出错"}}}
        return await response.json()