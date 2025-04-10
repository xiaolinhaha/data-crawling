#!/bin/bash

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（不同系统有不同的激活方式）
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "无法找到虚拟环境激活脚本"
    exit 1
fi

# 安装依赖
pip install -r requirements.txt

echo "环境设置完成！"
echo "运行 'python run.py' 启动服务" 