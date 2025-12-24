from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import threading
import time
from datetime import datetime, time as dt_time

def create_app():
    app = Flask(__name__, static_folder='frontend')
    CORS(app)
    
    # 配置
    app.config['SECRET_KEY'] = 'jianghe'  # 使用.env文件中的密钥
    
    # 注册蓝图
    from backend.routes import main
    app.register_blueprint(main)
    
    # 设置静态文件路由
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)
    
    return app

def run_scheduled_absence_check():
    """运行定时缺勤检查任务"""
    while True:
        # 获取当前时间
        now = datetime.now()
        current_time = now.time()
        
        # 设定检查时间：每晚10点 (22:00)
        check_time = dt_time(22, 0, 0)
        
        # 如果当前时间接近晚上10点，则执行检查
        if current_time.hour == 22 and current_time.minute == 0:
            from backend.routes import scheduled_absence_check
            scheduled_absence_check()
            # 等待一分钟，避免重复执行
            time.sleep(60)
        else:
            # 每分钟检查一次
            time.sleep(60)

if __name__ == '__main__':
    app = create_app()
    
    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduled_absence_check, daemon=True)
    scheduler_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)