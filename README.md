# FastAPI Hello World

一个简单的FastAPI Hello World示例项目，使用虚拟环境确保可移植性。

## 功能

1. `/` - 返回Hello World消息
2. `/baidu-slogan` - 爬取百度首页的一条文案

## 使用方法

### 1. 创建虚拟环境

```bash
python -m venv venv
```

### 2. 激活虚拟环境

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行服务

```bash
python run.py
```

访问 [http://localhost:8000](http://localhost:8000) 查看API。
访问 [http://localhost:8000/docs](http://localhost:8000/docs) 查看API文档。
访问 [http://localhost:8000/baidu-slogan](http://localhost:8000/baidu-slogan) 获取百度首页文案。 