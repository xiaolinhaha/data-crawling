@echo off
echo 正在创建虚拟环境...
python -m venv venv

echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

echo 正在安装依赖...
pip install -r requirements.txt

echo 环境设置完成！
echo 运行 'python run.py' 启动服务 