from flask import Flask, jsonify

import config
import env
from crawlers import crawlers_bp
from crawlers.eastmoney_antifraud_crawler import eastmoney_antifraud_bp
from controller import bp as controller_bp
import logging
import os
from logging.handlers import RotatingFileHandler
from scheduler import init_scheduler, shutdown_scheduler
import atexit

# 配置日志
def setup_logging():
    # 确保logs目录存在
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 主日志配置 - 使用更精简的格式
    main_handler = RotatingFileHandler('logs/server.log', maxBytes=10485760, backupCount=5)
    main_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s'
    ))
    
    # 错误日志配置 - 保留详细格式用于调试
    error_handler = RotatingFileHandler('logs/error.log', maxBytes=10485760, backupCount=5)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '[%(asctime)s][%(name)s.%(funcName)s():%(lineno)d] [%(levelname)s] %(message)s'
    ))
    
    # 调度器专用日志配置 - 简化格式
    scheduler_handler = RotatingFileHandler('logs/scheduler.log', maxBytes=10485760, backupCount=5)
    scheduler_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(message)s'
    ))
    
    # 清理原有处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 配置根日志记录器 - 调整为WARNING级别减少输出
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(main_handler)
    root_logger.addHandler(error_handler)
    
    # 单独配置apscheduler的日志 - 调整为WARNING级别减少输出
    apscheduler_logger = logging.getLogger('apscheduler')
    apscheduler_logger.setLevel(logging.WARNING)  
    apscheduler_logger.propagate = False
    for handler in apscheduler_logger.handlers[:]:
        apscheduler_logger.removeHandler(handler)
    apscheduler_logger.addHandler(main_handler)
    
    # 配置调度器日志
    scheduler_logger = logging.getLogger('scheduler')
    scheduler_logger.setLevel(logging.INFO)
    scheduler_logger.propagate = False
    for handler in scheduler_logger.handlers[:]:
        scheduler_logger.removeHandler(handler)
    scheduler_logger.addHandler(scheduler_handler)
    
    # 设置werkzeug日志级别为WARNING减少输出
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)
app.config.from_object(config.BaseConfig)
# 设置JSON编码，确保中文不会被转为Unicode
app.config['JSON_AS_ASCII'] = False

app.register_blueprint(controller_bp, url_prefix='/api')
app.register_blueprint(crawlers_bp, url_prefix='/api/crawlers')
app.register_blueprint(eastmoney_antifraud_bp, url_prefix='/api/crawlers/eastmoney_antifraud')

# 添加首页路由
@app.route('/')
def index():
    return jsonify({
        "status": "success",
        "message": "反诈新闻爬虫API服务",
        "endpoints": {
            "反诈新闻": "/api/crawlers/eastmoney_antifraud/eastmoney_antifraud_article",
            "调度器状态": "/scheduler/status",
            "启动调度器": "/scheduler/start",
            "停止调度器": "/scheduler/stop",
            "执行调度任务": "/scheduler/run_task"
        }
    })

# 启动应用
if __name__ == '__main__':
    # 设置日志
    setup_logging()
    
    # 导入并初始化调度器 - 单例模式避免重复初始化
    from scheduler import init_scheduler, shutdown_scheduler
    
    # 初始化调度器
    scheduler = init_scheduler()
    
    # 注册应用退出时的清理函数
    atexit.register(shutdown_scheduler)
    
    app.run(debug=env.DEBUG_MODEL,
            host=env.APP_HOST,
            port=env.APP_PORT)
