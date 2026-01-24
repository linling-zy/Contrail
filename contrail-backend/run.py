"""
应用启动入口
运行此文件启动 Flask 开发服务器
"""
import os
from dotenv import load_dotenv
from app import create_app

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量获取配置名称，默认为 development
config_name = os.environ.get('FLASK_ENV', 'development')

# 创建应用实例
app = create_app(config_name)

if __name__ == '__main__':
    # 开发环境配置
    app.run(
        host='0.0.0.0',  # 允许外部访问（微信小程序需要）
        port=5000,  # 端口号
        debug=True  # 开启调试模式
    )

