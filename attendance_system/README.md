# 学生人脸识别考勤系统

这是一个基于Python Flask、MySQL和人脸识别技术的学生考勤系统。

## 功能特点

1. 学生信息管理（添加学生、人脸注册）
2. 课程管理（添加课程、课程时间设置）
3. 学生选课功能（学生可以选择多门课程）
4. 人脸识别考勤（根据课程时间判断考勤状态）
5. 考勤记录查询
6. 基于Web的用户界面

## 技术栈

- 后端：Python Flask
- 数据库：MySQL
- 人脸识别：OpenCV库
- 前端：HTML, CSS, JavaScript (AJAX)
- 数据库连接：mysql-connector-python

## 安装步骤

1. 克隆项目代码
2. 安装依赖包：
   ```
   pip install -r requirements.txt
   ```

3. 安装OpenCV扩展模块（用于人脸识别功能）：
   ```
   pip install opencv-contrib-python
   ```

4. 创建MySQL数据库：
   ```sql
   CREATE DATABASE attendance_system;
   ```

5. 根据database_design.md中的表结构创建数据表

6. 修改.env文件中的数据库配置

7. 运行应用：
   ```
   python app.py
   ```

8. 访问 http://localhost:5000 使用系统

## API接口

- GET /api/students - 获取所有学生
- POST /api/students - 添加学生
- DELETE /api/students/<student_id> - 删除学生
- GET /api/courses - 获取所有课程
- POST /api/courses - 添加课程
- DELETE /api/courses/<course_id> - 删除课程
- POST /api/student_courses - 为学生分配课程
- DELETE /api/student_courses/<student_id>/<course_id> - 删除学生课程关联
- GET /api/student_courses/<student_id> - 获取学生已选课程
- POST /api/attendance/recognize - 人脸识别考勤
- GET /api/attendance - 获取考勤记录
- GET /api/face_status - 获取人脸识别状态信息（调试用）
- POST /api/test_recognize - 测试人脸识别功能（调试用）
- POST /api/debug/face_detection - 测试人脸检测（调试用）
- POST /api/debug/add_face - 测试人脸添加过程（调试用）
- POST /api/debug/full_add_face - 完整测试人脸添加流程（调试用）
- GET /api/debug/courses - 获取所有课程信息（调试用）
- GET /api/debug/student_courses - 获取所有学生选课信息（调试用）
- GET /api/debug/student/<student_id>/courses - 获取特定学生当天课程信息（调试用）
- GET /api/debug/student/<student_id> - 获取特定学生的人脸数据信息（调试用）
- GET /api/test_course_query/<student_id> - 测试课程查询（调试用）

## 界面功能说明

1. **添加学生** - 录入学生基本信息和人脸照片
2. **学生信息** - 查看所有学生信息及选课情况
3. **学生选课** - 为学生分配课程，查看学生已选课程
4. **课程管理** - 添加和管理课程信息
5. **人脸识别考勤** - 通过摄像头进行人脸识别考勤
6. **考勤记录** - 查看所有考勤记录

## 考勤规则

- 课程开始10分钟内签到为"正常"
- 超过10分钟签到为"迟到"
- 未签到为"缺勤"

## 故障排除

### 人脸识别无法工作

如果遇到"识别失败: 未识别到学生"的问题，请按以下步骤排查：

1. **检查OpenCV安装**：
   - 确保已安装 `opencv-contrib-python`：
     ```
     pip install opencv-contrib-python
     ```

2. **确认人脸数据已录入**：
   - 在"添加学生"页面正确录入学生人脸照片
   - 确保拍照时人脸清晰可见，光线充足

3. **检查人脸识别状态**：
   - 访问 `/api/face_status` 接口查看人脸识别模块状态
   - 确认 `trained` 为 `true` 且 `known_faces_count` 大于0

4. **测试人脸识别功能**：
   - 使用测试接口 `/api/test_recognize` 来验证人脸识别是否正常工作

5. **重启应用**：
   - 有时需要重启应用以重新加载人脸数据

### 其他常见问题

1. **数据库连接失败**：
   - 检查MySQL服务是否运行
   - 验证数据库配置（主机、用户名、密码、数据库名）

2. **摄像头无法访问**：
   - 检查浏览器权限设置，确保允许访问摄像头
   - 确认摄像头设备正常工作

## 注意事项

1. 需要支持摄像头的设备才能使用人脸识别功能
2. 推荐安装 `opencv-contrib-python` 以获得完整的人脸识别功能
3. 如果只想使用基础功能，可以只安装 `opencv-python`
4. 当前版本使用简化的人脸识别实现，适用于演示和学习目的
5. 在生产环境中，建议使用更专业的人脸识别服务