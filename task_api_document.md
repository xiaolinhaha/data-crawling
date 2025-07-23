# 工作流任务调用文档

## 1. 定时任务手动调用指南

系统包含三类任务，每类任务使用不同的API令牌：

### A. 新闻主题类任务 (WECHAT_API_TOKEN)

**接口**: `/api/scheduler/run_task`  
**方法**: POST  
**Content-Type**: application/json

**参数**:
```json
{
  "task_name": "hotspots",
  "args": ["主题名称"]
}
```

**可用主题**:
- 财经快评-1
- 财经快评-2
- 热点新闻-1
- 热点新闻-2
- 理财资讯-1
- 理财资讯-2
- 基金投资
- 股市观察
- 保险导航
- 行业瞭望
- 政策解读1
- 政策解读2
- 风险警示1
- 风险警示2
- 国际经济
- 国际新闻
- 健康生活
- 社会法治
- 科普中国

**示例**:
```bash
curl -X POST "http://127.0.0.1:5005/api/scheduler/run_task" -H "Content-Type: application/json" -d '{"task_name": "hotspots", "args": ["财经快评-2"]}'
```

### B. 原始任务类 (API_TOKEN)

**接口**: `/api/scheduler/run_task`  
**方法**: POST  
**Content-Type**: application/json

**参数**:
```json
{
  "task_name": "hotspots",
  "args": ["任务名称"]
}
```

**可用任务**:
- 每日金句
- 金价
- 金融
- 房地产
- 经济指标

**示例**:
```bash
curl -X POST "http://127.0.0.1:5005/api/scheduler/run_task" -H "Content-Type: application/json" -d '{"task_name": "hotspots", "args": ["金价"]}'
```

### C. 交易所指数任务 (WECHAT_API_TOKEN)

**接口**: `/api/scheduler/run_task`  
**方法**: POST  
**Content-Type**: application/json

**参数**:
```json
{
  "task_name": "hourly_task",
  "args": ["交易所指数"]
}
```

**示例**:
```bash
curl -X POST "http://127.0.0.1:5005/api/scheduler/run_task" -H "Content-Type: application/json" -d '{"task_name": "hourly_task", "args": ["交易所指数"]}'
```

## 2. 强制指定API令牌

所有任务都可以通过在args参数中提供第二个元素来强制指定API令牌：

```json
{
  "task_name": "hotspots",
  "args": ["任务名称", "自定义API令牌"]
}
```

示例:
```bash
curl -X POST "http://127.0.0.1:5005/api/scheduler/run_task" -H "Content-Type: application/json" -d '{"task_name": "hotspots", "args": ["财经快评-2", "app-sWWA6yNTphzXxTLQFQbjmJ6B"]}'
```

## 3. 调度器管理接口

### 查看调度器状态
**接口**: `/api/scheduler/status`  
**方法**: GET

```bash
curl -X GET "http://127.0.0.1:5005/api/scheduler/status"
```

### 启动调度器
**接口**: `/api/scheduler/start`  
**方法**: POST

```bash
curl -X POST "http://127.0.0.1:5005/api/scheduler/start"
```

### 停止调度器
**接口**: `/api/scheduler/stop`  
**方法**: POST

```bash
curl -X POST "http://127.0.0.1:5005/api/scheduler/stop"
```

## 4. Python 调用示例

```python
import requests
import json

def call_task(task_name, args):
    """调用任务API
    
    Args:
        task_name (str): 任务名称，如 "hotspots" 或 "hourly_task"
        args (list): 参数列表，包含任务类型和可选的API令牌
    
    Returns:
        dict: API响应
    """
    url = "http://127.0.0.1:5005/api/scheduler/run_task"
    payload = {
        "task_name": task_name,
        "args": args
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

# 调用财经快评-2
result = call_task("hotspots", ["财经快评-2"])
print(result)

# 调用交易所指数
result = call_task("hourly_task", ["交易所指数"])
print(result)

# 调用原始任务-金价
result = call_task("hotspots", ["金价"])
print(result)

# 使用自定义API令牌
result = call_task("hotspots", ["财经快评-2", "your-custom-api-token"])
print(result)
```

## 5. 任务自动执行时间表

| 任务类型 | 执行频率 | 时间 |
|---------|---------|------|
| 新闻主题类任务 | 每日一次 | 从9:00开始，每隔2分钟执行一个主题 |
| 原始任务类 | 每日一次 | 按预定时间(9:00-9:05)执行 |
| 交易所指数 | 每小时一次 | 整点执行 |

注意：所有任务均已配置为按时自动执行，以上API仅用于手动触发或测试。 