# 学生人脸识别考勤系统数据库设计

## 1. 数据库表结构

### 1.1 学生表 (students)
存储学生基本信息和人脸特征数据

```sql
CREATE TABLE students (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(20) UNIQUE NOT NULL COMMENT '学号',
    name VARCHAR(50) NOT NULL COMMENT '姓名',
    class_name VARCHAR(50) NOT NULL COMMENT '班级',
    face_encoding TEXT COMMENT '人脸特征数据（JSON格式）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 1.2 课程表 (courses)
存储课程信息

```sql
CREATE TABLE courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    course_name VARCHAR(100) NOT NULL COMMENT '课程名称',
    course_time_start TIME NOT NULL COMMENT '课程开始时间',
    course_time_end TIME NOT NULL COMMENT '课程结束时间',
    weekday ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL COMMENT '上课星期',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3 学生课程关联表 (student_courses)
存储学生和课程的多对多关系

```sql
CREATE TABLE student_courses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(20) NOT NULL COMMENT '学号',
    course_id INT NOT NULL COMMENT '课程ID',
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_course (student_id, course_id)
);
```

### 1.4 考勤记录表 (attendance_records)
存储学生考勤记录

```sql
CREATE TABLE attendance_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_id VARCHAR(20) NOT NULL COMMENT '学号',
    course_id INT NOT NULL COMMENT '课程ID',
    record_date DATE NOT NULL COMMENT '考勤日期',
    record_time TIME NOT NULL COMMENT '考勤时间',
    status ENUM('正常', '迟到', '缺勤') DEFAULT '正常' COMMENT '考勤状态',
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE KEY unique_student_course_date (student_id, course_id, record_date)
);
```

### 1.5 管理员/教师用户表 (users)
存储管理员或教师账户信息

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    role ENUM('admin', 'teacher') DEFAULT 'teacher' COMMENT '角色',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 2. 表关系说明

1. students 表和 attendance_records 表通过 student_id 字段关联
2. courses 表和 attendance_records 表通过 course_id 字关联
3. students 表和 courses 表通过 student_courses 表建立多对多关系
4. users 表独立存在，用于系统登录验证

## 3. 约束说明

1. student_courses 表使用 CASCADE 删除策略：
   - 当学生被删除时，相关的课程关联记录也会自动删除
   - 当课程被删除时，相关的课程关联记录也会自动删除
2. attendance_records 表使用 CASCADE 删除策略：
   - 当学生被删除时，相关的考勤记录也会自动删除
   - 当课程被删除时，相关的考勤记录也会自动删除

## 4. 索引优化

为了提高查询效率，在以下字段上建立索引：
- students.student_id (唯一索引)
- courses.id (主键索引)
- attendance_records.record_date (普通索引)
- attendance_records.student_id (普通索引)
- attendance_records.course_id (普通索引)
- student_courses.student_id (普通索引)
- student_courses.course_id (普通索引)