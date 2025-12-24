from flask import Blueprint, jsonify, request
import mysql.connector
from datetime import datetime, time, timedelta
from models.face_recognition_service import FaceRecognitionService

import base64
import json
import cv2
import numpy as np
import threading
import time as time_module
from datetime import time as dt_time

main = Blueprint('main', __name__)
face_service = FaceRecognitionService()

# 数据库配置 - 直接在程序中设置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '9194',  # 使用.env文件中的密码
    'database': 'attendance_system',
    'port': 3306
}

# 初始化时加载已有人脸数据
def load_known_faces():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT student_id, face_encoding FROM students WHERE face_encoding IS NOT NULL")
        faces = cursor.fetchall()
        
        for face in faces:
            if face['face_encoding']:
                # 从数据库加载人脸数据
                face_service.load_face_data(face['face_encoding'], face['student_id'])
        
        # 训练模型
        if len(face_service.face_samples) > 0:
            face_service.train_model()
        
        cursor.close()
        conn.close()
        
        print(f"Loaded {len(face_service.known_faces)} known faces")
    except Exception as e:
        print(f"Error loading known faces: {e}")

# 在应用启动时加载人脸数据
load_known_faces()

# 测试路由
@main.route('/api/')
def index():
    return jsonify({'message': '学生人脸识别考勤系统API'})

# 调试接口：检查人脸识别状态
@main.route('/api/face_status')
def face_status():
    return jsonify({
        'trained': face_service.trained,
        'known_faces_count': len(face_service.known_faces),
        'face_samples_count': len(face_service.face_samples),
        'ids_count': len(face_service.ids)
    })

# 调试接口：检查特定学生的人脸数据
@main.route('/api/debug/student/<student_id>')
def debug_student(student_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, student_id, name, class_name, face_encoding FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if student:
            has_face_data = bool(student['face_encoding'])
            return jsonify({
                'success': True, 
                'data': {
                    'id': student['id'],
                    'student_id': student['student_id'],
                    'name': student['name'],
                    'class_name': student['class_name'],
                    'has_face_data': has_face_data,
                    'face_encoding_length': len(student['face_encoding']) if student['face_encoding'] else 0
                }
            })
        else:
            return jsonify({'success': False, 'message': '学生不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 调试接口：检查课程数据
@main.route('/api/debug/courses')
def debug_courses():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM courses")
        courses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': courses})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 调试接口：检查特定学生的课程
@main.route('/api/debug/student/<student_id>/courses')
def debug_student_courses_by_id(student_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 获取当前星期
        weekdays_chinese = {
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
            4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        }
        current_weekday = weekdays_chinese[datetime.now().weekday()]
        
        cursor.execute("""
            SELECT c.id, c.course_name, c.course_time_start, c.course_time_end, c.weekday
            FROM courses c
            JOIN student_courses sc ON c.id = sc.course_id
            WHERE sc.student_id = %s AND c.weekday = %s
        """, (student_id, current_weekday))
        
        courses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': courses, 'today': current_weekday})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 调试接口：检查学生选课数据
@main.route('/api/debug/student_courses')
def debug_student_courses():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM student_courses")
        student_courses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': student_courses})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 测试人脸识别接口
@main.route('/api/test_recognize', methods=['POST'])
def test_recognize():
    try:
        data = request.get_json()
        face_image = data.get('face_image')  # Base64格式的人脸图片
        
        if not face_image:
            return jsonify({'success': False, 'message': '未提供人脸图片'})
        
        # 移除Base64头部信息（如果有的话）
        if face_image.startswith('data:image'):
            face_image_data = face_image.split(',')[1]
        else:
            face_image_data = face_image
        
        # 解码Base64字符串
        image_data = base64.b64decode(face_image_data)
        
        # 调试：检查是否能检测到人脸
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        faces = face_service.detect_faces(img)
        
        if len(faces) == 0:
            return jsonify({'success': False, 'message': '未检测到人脸，请确保人脸清晰可见'})
        
        # 识别人脸
        student_id = face_service.recognize_face(image_data)
        
        if not student_id:
            return jsonify({'success': False, 'message': '未识别到学生，请确保已添加该学生的人脸数据'})
        
        return jsonify({
            'success': True, 
            'message': '识别成功', 
            'student_id': student_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 获取所有学生
@main.route('/api/students', methods=['GET'])
def get_students():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # 增加排序缓冲区大小以避免"Out of sort memory"错误
        cursor = conn.cursor()
        cursor.execute("SET SESSION sort_buffer_size = 2097152")  # 设置为2MB
        cursor.execute("SET SESSION read_rnd_buffer_size = 2097152")  # 设置为2MB
        cursor.close()
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT s.id, s.student_id, s.name, s.class_name, s.face_encoding,
                   COUNT(sc.course_id) as course_count
            FROM students s
            LEFT JOIN student_courses sc ON s.student_id = sc.student_id
            GROUP BY s.id, s.student_id, s.name, s.class_name, s.face_encoding
            ORDER BY s.id
        """)
        students = cursor.fetchall()
        
        # 处理照片数据
        for student in students:
            # 只需知道是否有照片，不需要返回实际的照片数据
            student['has_photo'] = bool(student['face_encoding'])
            # 删除face_encoding字段以减少传输数据量
            del student['face_encoding']
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': students})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 添加学生（包括人脸数据）
@main.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        name = data.get('name')
        class_name = data.get('class_name')
        face_image = data.get('face_image')  # Base64格式的人脸图片
        
        print(f"Adding student: {student_id}, {name}, {class_name}")
        
        face_encoding = None
        if face_image:
            print("Processing face image...")
            # 移除Base64头部信息（如果有的话）
            if face_image.startswith('data:image'):
                face_image_data = face_image.split(',')[1]
            else:
                face_image_data = face_image
            
            # 解码Base64字符串
            image_data = base64.b64decode(face_image_data)
            print(f"Image data size: {len(image_data)} bytes")
            
            # 添加人脸数据
            face_added = face_service.add_face(image_data, student_id)
            print(f"Face added: {face_added}")
            
            if face_added:
                # 重新训练模型
                trained = face_service.train_model()
                print(f"Model trained: {trained}")
                
                # 直接使用已经添加的人脸数据而不是重新提取
                # 注意：这里需要获取最新添加的人脸数据
                if len(face_service.face_samples) > 0:
                    last_face_roi = face_service.face_samples[-1]  # 获取最新添加的人脸样本
                    # 检查方法是否存在
                    if hasattr(face_service, 'serialize_face'):
                        face_encoding = face_service.serialize_face(last_face_roi)
                        print(f"Face encoding generated, length: {len(face_encoding) if face_encoding else 0}")
                    else:
                        print("serialize_face method not found!")
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO students (student_id, name, class_name, face_encoding) VALUES (%s, %s, %s, %s)",
            (student_id, name, class_name, face_encoding)
        )
        conn.commit()
        
        student_id_db = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '学生添加成功', 'student_id': student_id_db})
    except Exception as e:
        print(f"Error adding student: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

# 删除学生
@main.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 删除学生（相关的课程关联和考勤记录会自动通过外键约束删除）
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        conn.commit()
        
        rows_affected = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        if rows_affected > 0:
            return jsonify({'success': True, 'message': '学生删除成功'})
        else:
            return jsonify({'success': False, 'message': '未找到该学生'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 获取所有课程
@main.route('/api/courses', methods=['GET'])
def get_courses():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, course_name, course_time_start, course_time_end, weekday FROM courses")
        courses = cursor.fetchall()
        
        # 格式化时间
        for course in courses:
            for key, value in course.items():
                if key in ['course_time_start', 'course_time_end'] and hasattr(value, 'strftime'):
                    course[key] = value.strftime('%H:%M')
                elif key in ['course_time_start', 'course_time_end'] and isinstance(value, (timedelta,)):
                    # 处理timedelta类型的时间
                    hours, remainder = divmod(value.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    course[key] = '{:02d}:{:02d}'.format(hours, minutes)
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': courses})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 添加课程
@main.route('/api/courses', methods=['POST'])
def add_course():
    try:
        data = request.get_json()
        course_name = data.get('course_name')
        course_time_start = data.get('course_time_start')
        course_time_end = data.get('course_time_end')
        weekday = data.get('weekday')
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO courses (course_name, course_time_start, course_time_end, weekday) VALUES (%s, %s, %s, %s)",
            (course_name, course_time_start, course_time_end, weekday)
        )
        conn.commit()
        
        course_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '课程添加成功', 'course_id': course_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 删除课程
@main.route('/api/courses/<course_id>', methods=['DELETE'])
def delete_course(course_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 删除课程（相关的学生课程关联和考勤记录会自动通过外键约束删除）
        cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        conn.commit()
        
        rows_affected = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        if rows_affected > 0:
            return jsonify({'success': True, 'message': '课程删除成功'})
        else:
            return jsonify({'success': False, 'message': '未找到该课程'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 为学生分配课程
@main.route('/api/student_courses', methods=['POST'])
def assign_course_to_student():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        course_id = data.get('course_id')
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查是否已经存在该选课记录
        cursor.execute(
            "SELECT id FROM student_courses WHERE student_id = %s AND course_id = %s",
            (student_id, course_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '该学生已选择此课程'})
        
        cursor.execute(
            "INSERT INTO student_courses (student_id, course_id) VALUES (%s, %s)",
            (student_id, course_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': '课程分配成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 删除学生关联的课程
@main.route('/api/student_courses/<student_id>/<course_id>', methods=['DELETE'])
def delete_student_course(student_id, course_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 删除学生课程关联
        cursor.execute(
            "DELETE FROM student_courses WHERE student_id = %s AND course_id = %s",
            (student_id, course_id)
        )
        conn.commit()
        
        rows_affected = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        if rows_affected > 0:
            return jsonify({'success': True, 'message': '学生课程关联删除成功'})
        else:
            return jsonify({'success': False, 'message': '未找到该学生课程关联'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 获取学生已选课程
@main.route('/api/student_courses/<student_id>', methods=['GET'])
def get_student_courses(student_id):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT c.id, c.course_name, c.course_time_start, c.course_time_end, c.weekday
            FROM courses c
            JOIN student_courses sc ON c.id = sc.course_id
            WHERE sc.student_id = %s
        """, (student_id,))
        
        courses = cursor.fetchall()
        
        # 格式化时间
        for course in courses:
            for key, value in course.items():
                if key in ['course_time_start', 'course_time_end'] and hasattr(value, 'strftime'):
                    course[key] = value.strftime('%H:%M')
                elif key in ['course_time_start', 'course_time_end'] and isinstance(value, (timedelta,)):
                    # 处理timedelta类型的时间
                    hours, remainder = divmod(value.seconds, 3600)
                    minutes, _ = divmod(remainder, 60)
                    course[key] = '{:02d}:{:02d}'.format(hours, minutes)
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': courses})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 测试课程查询接口
@main.route('/api/test_course_query/<student_id>')
def test_course_query(student_id):
    try:
        # 获取当前星期
        weekdays_chinese = {
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
            4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        }
        current_weekday = weekdays_chinese[datetime.now().weekday()]
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查询学生当天的课程
        cursor.execute("""
            SELECT c.id as course_id, c.course_name, c.course_time_start, c.course_time_end
            FROM courses c
            JOIN student_courses sc ON c.id = sc.course_id
            WHERE sc.student_id = %s AND c.weekday = %s
        """, (student_id, current_weekday))
        
        courses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'student_id': student_id,
            'current_weekday': current_weekday,
            'courses_found': len(courses),
            'courses': courses
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 人脸识别考勤
@main.route('/api/attendance/recognize', methods=['POST'])
def recognize_attendance():
    try:
        data = request.get_json()
        face_image = data.get('face_image')  # Base64格式的人脸图片
        
        if not face_image:
            return jsonify({'success': False, 'message': '未提供人脸图片'})
        
        # 移除Base64头部信息（如果有的话）
        if face_image.startswith('data:image'):
            face_image_data = face_image.split(',')[1]
        else:
            face_image_data = face_image
        
        # 解码Base64字符串
        image_data = base64.b64decode(face_image_data)
        
        # 识别人脸
        student_id = face_service.recognize_face(image_data)
        
        if not student_id:
            return jsonify({'success': False, 'message': '未识别到学生'})
        
        # 获取当前时间和星期几
        now = datetime.now()
        current_time = now.time()
        current_date = now.date()
        
        # 获取星期名称（与数据库中的格式一致）
        weekdays_chinese = {
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
            4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        }
        current_weekday = weekdays_chinese[now.weekday()]
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查找该学生当天的课程
        cursor.execute("""
            SELECT c.id as course_id, c.course_name, c.course_time_start, c.course_time_end
            FROM courses c
            JOIN student_courses sc ON c.id = sc.course_id
            WHERE sc.student_id = %s AND c.weekday = %s
        """, (student_id, current_weekday))
        
        courses = cursor.fetchall()
        
        if not courses:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '今天没有课程'})
        
        # 查找最适合的课程（当前时间范围内的课程）
        target_course = None
        for course in courses:
            # 处理时间格式
            course_time_start = course['course_time_start']
            course_time_end = course['course_time_end']
            
            # 如果是timedelta类型，转换为time类型
            if isinstance(course_time_start, timedelta):
                course_time_start = (datetime.min + course_time_start).time()
            if isinstance(course_time_end, timedelta):
                course_time_end = (datetime.min + course_time_end).time()
            
            # 确保比较的是相同类型
            if isinstance(course_time_start, str):
                course_time_start = datetime.strptime(course_time_start, '%H:%M:%S').time()
            if isinstance(course_time_end, str):
                course_time_end = datetime.strptime(course_time_end, '%H:%M:%S').time()
            
            # 更新课程时间（确保类型正确）
            course['course_time_start'] = course_time_start
            course['course_time_end'] = course_time_end
            
            if course_time_start <= current_time <= course_time_end:
                target_course = course
                break
        
        if not target_course:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '当前时间不在课程时间范围内'})
        
        # 检查是否已存在今天的考勤记录
        cursor.execute(
            "SELECT id FROM attendance_records WHERE student_id = %s AND course_id = %s AND record_date = %s",
            (student_id, target_course['course_id'], current_date)
        )
        
        existing_record = cursor.fetchone()
        
        if existing_record:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': '今天该课程已经签到过了', 'student_id': student_id})
        
        # 确定考勤状态
        status = '正常'
        # 计算是否迟到（课程开始10分钟后签到为迟到）
        if current_time > target_course['course_time_start']:
            time_diff = datetime.combine(current_date, current_time) - datetime.combine(current_date, target_course['course_time_start'])
            if time_diff > timedelta(minutes=10):
                status = '迟到'
        
        # 插入新的考勤记录
        cursor.execute(
            "INSERT INTO attendance_records (student_id, course_id, record_date, record_time, status) VALUES (%s, %s, %s, %s, %s)",
            (student_id, target_course['course_id'], current_date, current_time, status)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'考勤成功，状态：{status}', 
            'student_id': student_id,
            'time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'status': status
        })
    except Exception as e:
        print(f"Error in recognize_attendance: {e}")  # 调试信息
        return jsonify({'success': False, 'message': str(e)})

# 自动检查并添加缺勤记录
@main.route('/api/attendance/check_absences', methods=['POST'])
def check_and_add_absences():
    try:
        # 获取当前日期和星期几
        now = datetime.now()
        current_date = now.date()
        
        # 获取星期名称（与数据库中的格式一致）
        weekdays_chinese = {
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
            4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        }
        current_weekday = weekdays_chinese[now.weekday()]
        current_time = now.time()
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查找今天有课但还没有考勤记录的学生
        cursor.execute("""
            SELECT DISTINCT sc.student_id, c.id as course_id, c.course_time_start, c.course_time_end
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            WHERE c.weekday = %s
            AND sc.student_id NOT IN (
                SELECT ar.student_id 
                FROM attendance_records ar 
                WHERE ar.record_date = %s AND ar.course_id = c.id
            )
        """, (current_weekday, current_date))
        
        courses_without_attendance = cursor.fetchall()
        
        absent_records_added = 0
        
        # 为每一条记录检查是否应该标记为缺勤
        for course in courses_without_attendance:
            course_time_end = course['course_time_end']
            
            # 如果课程已经结束，则添加缺勤记录
            if isinstance(course_time_end, str):
                course_time_end = datetime.strptime(course_time_end, '%H:%M:%S').time()
            elif isinstance(course_time_end, timedelta):
                course_time_end = (datetime.min + course_time_end).time()
            
            # 如果当前时间已经超过了课程结束时间，则标记为缺勤
            if current_time > course_time_end:
                cursor.execute(
                    "INSERT INTO attendance_records (student_id, course_id, record_date, record_time, status) VALUES (%s, %s, %s, %s, %s)",
                    (course['student_id'], course['course_id'], current_date, current_time, '缺勤')
                )
                absent_records_added += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'成功添加了 {absent_records_added} 条缺勤记录'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 定时任务：每天晚上10点检查并添加缺勤记录
def scheduled_absence_check():
    """定时任务：检查并添加缺勤记录"""
    try:
        # 获取当前日期和时间
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()
        
        # 获取星期名称（与数据库中的格式一致）
        weekdays_chinese = {
            0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
            4: 'Friday', 5: 'Saturday', 6: 'Sunday'
        }
        current_weekday = weekdays_chinese[now.weekday()]
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查找今天有课但还没有考勤记录的学生
        cursor.execute("""
            SELECT DISTINCT sc.student_id, c.id as course_id, c.course_time_start, c.course_time_end
            FROM student_courses sc
            JOIN courses c ON sc.course_id = c.id
            WHERE c.weekday = %s
            AND sc.student_id NOT IN (
                SELECT ar.student_id 
                FROM attendance_records ar 
                WHERE ar.record_date = %s AND ar.course_id = c.id
            )
        """, (current_weekday, current_date))
        
        courses_without_attendance = cursor.fetchall()
        
        absent_records_added = 0
        
        # 为每一条记录检查是否应该标记为缺勤
        for course in courses_without_attendance:
            course_time_end = course['course_time_end']
            
            # 如果课程已经结束，则添加缺勤记录
            if isinstance(course_time_end, str):
                course_time_end = datetime.strptime(course_time_end, '%H:%M:%S').time()
            elif isinstance(course_time_end, timedelta):
                course_time_end = (datetime.min + course_time_end).time()
            
            # 如果当前时间已经超过了课程结束时间，则标记为缺勤
            if current_time > course_time_end:
                cursor.execute(
                    "INSERT INTO attendance_records (student_id, course_id, record_date, record_time, status) VALUES (%s, %s, %s, %s, %s)",
                    (course['student_id'], course['course_id'], current_date, current_time, '缺勤')
                )
                absent_records_added += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"[定时任务] 成功添加了 {absent_records_added} 条缺勤记录")
    except Exception as e:
        print(f"[定时任务] 添加缺勤记录时发生错误: {str(e)}")

# 手动触发定时任务（用于测试）
@main.route('/api/attendance/run_check', methods=['POST'])
def run_absence_check():
    """手动触发缺勤检查任务"""
    try:
        scheduled_absence_check()
        return jsonify({'success': True, 'message': '缺勤检查已完成'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 获取考勤记录
@main.route('/api/attendance', methods=['GET'])
def get_attendance():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        # 增加排序缓冲区大小以避免"Out of sort memory"错误
        cursor = conn.cursor()
        cursor.execute("SET SESSION sort_buffer_size = 2097152")  # 设置为2MB
        cursor.execute("SET SESSION read_rnd_buffer_size = 2097152")  # 设置为2MB
        cursor.close()
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT ar.id, s.student_id, s.name, s.class_name, c.course_name, ar.record_date, ar.record_time, ar.status
            FROM attendance_records ar
            JOIN students s ON ar.student_id = s.student_id
            JOIN courses c ON ar.course_id = c.id
            ORDER BY ar.record_date DESC, ar.record_time DESC
            LIMIT 1000
        """)
        
        records = cursor.fetchall()
        
        # 处理日期和时间格式
        for record in records:
            for key, value in record.items():
                if hasattr(value, 'total_seconds'):  # 检查是否为timedelta类型
                    record[key] = str(value)
                elif key == 'record_date' and hasattr(value, 'strftime'):
                    # 格式化日期为 YYYY-MM-DD
                    record[key] = value.strftime('%Y-%m-%d')
                elif key == 'record_time' and hasattr(value, 'strftime'):
                    # 格式化时间为 HH:MM:SS
                    record[key] = value.strftime('%H:%M:%S')
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 调试接口：测试人脸检测
@main.route('/api/debug/face_detection', methods=['POST'])
def debug_face_detection():
    try:
        data = request.get_json()
        face_image = data.get('face_image')  # Base64格式的人脸图片
        
        if not face_image:
            return jsonify({'success': False, 'message': '未提供人脸图片'})
        
        # 移除Base64头部信息（如果有的话）
        if face_image.startswith('data:image'):
            face_image_data = face_image.split(',')[1]
        else:
            face_image_data = face_image
        
        # 解码Base64字符串
        image_data = base64.b64decode(face_image_data)
        
        # 调试：检查是否能检测到人脸
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 检查图像是否成功解码
        if img is None:
            return jsonify({'success': False, 'message': '无法解码图像数据'})
        
        print(f"Image shape: {img.shape}")
        
        # 检测人脸
        faces = face_service.detect_faces(img)
        print(f"Detected faces: {len(faces)}")
        
        face_details = []
        for i, (x, y, w, h) in enumerate(faces):
            face_details.append({
                'face_id': i,
                'x': int(x),
                'y': int(y),
                'width': int(w),
                'height': int(h)
            })
        
        return jsonify({
            'success': True,
            'message': f'检测到 {len(faces)} 张人脸',
            'face_count': len(faces),
            'faces': face_details,
            'image_shape': img.shape
        })
    except Exception as e:
        print(f"Error in debug_face_detection: {e}")
        return jsonify({'success': False, 'message': str(e)})

# 调试接口：测试人脸添加过程
@main.route('/api/debug/add_face', methods=['POST'])
def debug_add_face():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        face_image = data.get('face_image')  # Base64格式的人脸图片
        
        if not face_image:
            return jsonify({'success': False, 'message': '未提供人脸图片'})
        
        if not student_id:
            return jsonify({'success': False, 'message': '未提供学生ID'})
        
        # 移除Base64头部信息（如果有的话）
        if face_image.startswith('data:image'):
            face_image_data = face_image.split(',')[1]
        else:
            face_image_data = face_image
        
        # 解码Base64字符串
        image_data = base64.b64decode(face_image_data)
        print(f"Image data size: {len(image_data)} bytes")
        
        # 调试：检查是否能检测到人脸
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 检查图像是否成功解码
        if img is None:
            return jsonify({'success': False, 'message': '无法解码图像数据'})
        
        print(f"Image shape: {img.shape}")
        
        # 检测人脸
        faces = face_service.detect_faces(img)
        print(f"Detected faces: {len(faces)}")
        
        if len(faces) == 0:
            return jsonify({'success': False, 'message': '未检测到人脸，请确保人脸清晰可见'})
        
        # 提取人脸
        face_roi = face_service.extract_face(img, faces[0])
        print(f"Extracted face shape: {face_roi.shape}")
        
        # 添加人脸数据
        face_added = face_service.add_face(image_data, student_id)
        print(f"Face added: {face_added}")
        
        # 训练模型
        if face_added:
            trained = face_service.train_model()
            print(f"Model trained: {trained}")
        
        # 序列化人脸数据
        serialized_face = face_service.serialize_face(face_roi)
        print(f"Serialized face data length: {len(serialized_face) if serialized_face else 0}")
        
        return jsonify({
            'success': True,
            'message': '人脸添加过程完成',
            'face_detected': len(faces) > 0,
            'face_added': face_added,
            'model_trained': face_service.trained if hasattr(face_service, 'trained') else False,
            'serialized_data_length': len(serialized_face) if serialized_face else 0
        })
    except Exception as e:
        print(f"Error in debug_add_face: {e}")
        return jsonify({'success': False, 'message': str(e)})

# 调试接口：完整测试人脸添加流程
@main.route('/api/debug/full_add_face', methods=['POST'])
def debug_full_add_face():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        name = data.get('name', 'Test Student')
        class_name = data.get('class_name', 'Test Class')
        face_image = data.get('face_image')  # Base64格式的人脸图片
        
        if not face_image:
            return jsonify({'success': False, 'message': '未提供人脸图片'})
        
        if not student_id:
            return jsonify({'success': False, 'message': '未提供学生ID'})
        
        print(f"Full add face test for student: {student_id}")
        
        # 移除Base64头部信息（如果有的话）
        if face_image.startswith('data:image'):
            face_image_data = face_image.split(',')[1]
        else:
            face_image_data = face_image
        
        # 解码Base64字符串
        image_data = base64.b64decode(face_image_data)
        print(f"Image data size: {len(image_data)} bytes")
        
        # 调试：检查是否能检测到人脸
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 检查图像是否成功解码
        if img is None:
            return jsonify({'success': False, 'message': '无法解码图像数据'})
        
        print(f"Image shape: {img.shape}")
        
        # 检测人脸
        faces = face_service.detect_faces(img)
        print(f"Detected faces: {len(faces)}")
        
        if len(faces) == 0:
            return jsonify({'success': False, 'message': '未检测到人脸，请确保人脸清晰可见'})
        
        # 提取人脸
        face_roi = face_service.extract_face(img, faces[0])
        print(f"Extracted face shape: {face_roi.shape}")
        
        # 添加人脸数据
        face_added = face_service.add_face(image_data, student_id)
        print(f"Face added: {face_added}")
        
        # 训练模型
        model_trained = False
        if face_added:
            model_trained = face_service.train_model()
            print(f"Model trained: {model_trained}")
        
        # 序列化人脸数据
        serialized_face = face_service.serialize_face(face_roi)
        print(f"Serialized face data length: {len(serialized_face) if serialized_face else 0}")
        
        # 模拟数据库插入
        print("Simulating database insert...")
        has_face_encoding = serialized_face is not None and len(serialized_face) > 0
        print(f"Has face encoding: {has_face_encoding}")
        
        return jsonify({
            'success': True,
            'message': '完整人脸添加流程测试完成',
            'student_id': student_id,
            'name': name,
            'class_name': class_name,
            'face_detected': len(faces) > 0,
            'face_added': face_added,
            'model_trained': model_trained,
            'has_face_encoding': has_face_encoding,
            'face_encoding_length': len(serialized_face) if serialized_face else 0
        })
    except Exception as e:
        print(f"Error in debug_full_add_face: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})
