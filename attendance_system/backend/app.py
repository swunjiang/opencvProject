from flask import Flask
from flask_cors import CORS
from backend.routes import main
import threading
import time
from datetime import datetime, time as dt_time

app = Flask(__name__)
CORS(app)

# 注册蓝图
app.register_blueprint(main)

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
    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=run_scheduled_absence_check, daemon=True)
    scheduler_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)