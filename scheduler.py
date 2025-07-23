from apscheduler.schedulers.background import BackgroundScheduler
import requests
import json
import logging
import pytz
import datetime
import os
import uuid  # 用于生成唯一ID

# 配置日志
logger = logging.getLogger('scheduler')
# 防止日志传播到根记录器
logger.propagate = False

# 全局调度器实例标志
_scheduler_initialized = False
scheduler = None

# 定义API Tokens
API_TOKEN = "app-cihyej58HzuFM1fGU2DrVr4S"
WECHAT_API_TOKEN = "app-VRGYZg8fFUe6mayiaAvbIeej"  # 使用有效的API令牌

class TaskConfig:
    @staticmethod
    def hotspots(article_type, api_token):
        url = "https://dipp.rs-ibg.com/rssz/v1/workflows/run"
        # url = "https://malla.leagpoint.com/rssz/v1/workflows/run"
        payload = json.dumps({
            "inputs": {
                "article_type": article_type
            },
            "response_mode": "blocking",
            "user": "abc-123"
        })
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        logger.info(f"调度任务执行: {article_type}, 响应: {response.text}")

    @staticmethod
    def task2(api_token):
        # 可以添加更多任务
        pass

    @staticmethod
    def hourly_task(article_type, api_token):
        """每10分钟执行一次的指数任务"""
        task_id = uuid.uuid4()  # 生成唯一执行ID
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"========== 开始执行{article_type}任务 ==========")
        logger.info(f"执行时间: {current_time}")
        
        try:
            # url = "https://malla.leagpoint.com/rssz/v1/workflows/run"
            url = "https://dipp.rs-ibg.com/rssz/v1/workflows/run"
            payload = json.dumps({
                "inputs": {
                    "article_type": article_type
                },
                "response_mode": "blocking",
                "user": "abc-123"
            })
            headers = {
                'Authorization': f'Bearer {api_token}',
                'Content-Type': 'application/json'
            }
            
            # 发送请求
            response = requests.request("POST", url, headers=headers, data=payload)
            
            # 记录响应
            logger.info(f"响应状态码: {response.status_code}")
            
        except Exception as e:
            logger.error(f"{article_type}任务执行出错: {str(e)}", exc_info=True)
        
        logger.info(f"========== {article_type}任务执行完成 ==========")

def configure_scheduler():
    """配置并注册所有调度任务"""
    global scheduler
    
    # 先移除所有已存在的任务，避免重复
    scheduler.remove_all_jobs()
    logger.info("已清除所有现有任务")
    
    # 设置起始时间(9:00)和间隔(2分钟)
    start_hour = 9
    start_minute = 0
    interval_minutes = 2
    
    # 图片中的所有主题
    topics = [
        "财经快评-1",
        "财经快评-2",
        "热点新闻-1",
        "热点新闻-2",
        "理财资讯-1",
        "理财资讯-2",
        "基金投资",
        "股市观察",
        "保险导航",
        "行业瞭望",
        "政策解读1",
        "政策解读2",
        "风险警示1",
        "风险警示2",
        "国际经济",
        "国际新闻",
        "健康生活",
        "社会法治",
        "科普中国",
    ]
    
    # 为每个主题添加定时任务，每个任务相隔2分钟
    for i, topic in enumerate(topics):
        # 计算当前任务的执行时间
        current_minute = (start_minute + i * interval_minutes) % 60
        current_hour = start_hour + (start_minute + i * interval_minutes) // 60
        
        # 添加任务
        scheduler.add_job(
            TaskConfig.hotspots, 
            'cron', 
            id=f'topic_{i+1}', 
            hour=current_hour, 
            minute=current_minute, 
            second=0, 
            args=[topic, WECHAT_API_TOKEN],
            max_instances=1  # 限制最大实例数为1
        )
        logger.info(f"添加定时任务: {topic}, 执行时间: {current_hour:02d}:{current_minute:02d}:00")
    
    # 注册原有定时任务 - 使用API_TOKEN
    original_tasks = [
        {"id": "hotspots4", "minute": 1, "name": "房地产"},
        {"id": "hotspots5", "minute": 2, "name": "金价"}
    ]
    
    # 添加原始任务
    for task in original_tasks:
        scheduler.add_job(
            TaskConfig.hotspots, 
            'cron', 
            id=task["id"], 
            hour=9, 
            minute=task["minute"], 
            second=0, 
            args=[task["name"], API_TOKEN],
            max_instances=1  # 限制最大实例数为1
        )
        logger.info(f"添加原始任务: {task['name']}, 执行时间: 09:{task['minute']:02d}:00")
    
   # 交易所指数任务：设置为每半小时执行一次
    scheduler.add_job(
        TaskConfig.hourly_task, 
        'cron', 
        id='exchange_index_task',  # 使用明确的任务ID 
        hour='*', # 每小时执行一次
        minute='2,12,22,32,42,52',
        args=["交易所指数", WECHAT_API_TOKEN],
        max_instances=1,    # 限制最大实例数为1
        coalesce=True,      # 合并错过的执行
        misfire_grace_time=30  # 错过执行时间的宽限期（秒）
    )
    logger.info("添加交易所指数任务: 每半小时执行一次（2分和32分）")

def init_scheduler():
    """初始化并启动调度器"""
    global _scheduler_initialized, scheduler
    
    # 如果调度器已经初始化，则直接返回
    if _scheduler_initialized:
        logger.info("调度器已经初始化，跳过重复初始化")
        return scheduler
    
    # 检查已有调度器
    import gc
    from apscheduler.schedulers.background import BackgroundScheduler
    existing_schedulers = [obj for obj in gc.get_objects() if isinstance(obj, BackgroundScheduler) and hasattr(obj, 'running')]
    
    if existing_schedulers:
        scheduler = existing_schedulers[0]
        logger.info("使用已存在的调度器实例")
        if not scheduler.running:
            logger.info("已存在的调度器未运行，启动它")
            scheduler.start()
        _scheduler_initialized = True
        return scheduler
    
    # 创建调度器实例
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Shanghai'))
    
    # 清空日志文件 (如果需要)
    try:
        with open('logs/scheduler.log', 'w') as f:
            f.write(f"========== 调度器日志重置于 {datetime.datetime.now()} ==========\n")
        logger.info("已清空调度器日志文件")
    except Exception as e:
        logger.error(f"清空日志文件失败: {str(e)}")
    
    # 配置调度器
    configure_scheduler()
    scheduler.start()
    
    # 标记为已初始化
    _scheduler_initialized = True
    logger.info("调度器已初始化并启动")
    return scheduler

def shutdown_scheduler():
    """关闭调度器"""
    global _scheduler_initialized, scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        _scheduler_initialized = False
        logger.info("调度器已关闭") 
    else:
        logger.info("调度器未在运行，无需关闭") 