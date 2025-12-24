// 全局变量
let currentStream = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 绑定表单提交事件
    document.getElementById('student-form').addEventListener('submit', addStudent);
    
    // 绑定拍照按钮事件
    document.getElementById('capture-btn').addEventListener('click', captureImage);
    
    // 绑定人脸检测调试按钮事件
    document.getElementById('debug-face-btn').addEventListener('click', debugFaceDetection);
    
    // 绑定识别按钮事件
    document.getElementById('recognize-btn').addEventListener('click', recognizeAttendance);
    
    // 绑定课程表单提交事件
    document.getElementById('course-form').addEventListener('submit', addCourse);
    
    // 绑定选课按钮事件
    document.getElementById('assign-course-btn').addEventListener('click', assignCourseToStudent);
    
    // 绑定查看学生课程事件
    document.getElementById('view-student').addEventListener('change', loadStudentCourses);
    
    // 初始化摄像头
    initCamera('video');
    
    // 初始化考勤页面摄像头
    initCamera('attendance-video');
    
    // 默认显示考勤记录
    loadAttendanceRecords();
    
    // 加载课程列表
    loadCourses();
});

// 显示指定部分并隐藏其他部分
function showSection(sectionId) {
    // 隐藏所有部分
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    // 显示指定部分
    document.getElementById(sectionId).classList.add('active');
    
    // 更新导航链接状态
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    event.target.classList.add('active');
    
    // 如果是考勤记录部分，刷新数据
    if (sectionId === 'records') {
        loadAttendanceRecords();
    }
    
    // 如果是课程部分，加载课程数据
    if (sectionId === 'add-course') {
        loadCourses();
    }
    
    // 如果是学生信息部分，加载学生数据
    if (sectionId === 'student-info') {
        loadStudents();
    }
    
    // 如果是学生选课部分，加载下拉列表数据
    if (sectionId === 'course-selection') {
        loadStudentsForSelection();
        loadCoursesForSelection();
    }
}

// 初始化摄像头
async function initCamera(videoElementId) {
    const video = document.getElementById(videoElementId);
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        
        // 保存流引用以便后续停止
        if (videoElementId === 'video') {
            currentStream = stream;
        }
    } catch (err) {
        console.error("无法访问摄像头:", err);
        showMessage('无法访问摄像头，请检查权限设置', 'error', `${videoElementId}-message`);
    }
}

// 拍照
function captureImage() {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');
    
    // 绘制当前视频帧到画布
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // 显示消息
    showMessage('拍照成功', 'success', 'student-message');
}

// 调试人脸检测
async function debugFaceDetection() {
    // 获取图片数据
    const canvas = document.getElementById('canvas');
    const imageData = canvas.toDataURL('image/jpeg');
    
    if (imageData === 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQH/2wBDAQEBAQEBAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQH/wAARCAAEAAQDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAr/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=') {
        showMessage('请先拍照', 'error', 'student-message');
        return;
    }
    
    // 发送数据到后端进行调试
    try {
        const response = await fetch('/api/debug/face_detection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                face_image: imageData
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success', 'student-message');
            console.log('Face detection debug info:', result);
        } else {
            showMessage('人脸检测失败: ' + result.message, 'error', 'student-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'student-message');
    }
}

// 添加学生
async function addStudent(event) {
    event.preventDefault();
    
    const studentId = document.getElementById('student-id').value;
    const name = document.getElementById('student-name').value;
    const className = document.getElementById('class-name').value;
    
    // 获取图片数据
    const canvas = document.getElementById('canvas');
    const imageData = canvas.toDataURL('image/jpeg');
    
    if (imageData === 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQH/2wBDAQEBAQEBAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQECAQH/wAARCAAEAAQDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAr/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=') {
        showMessage('请先拍照', 'error', 'student-message');
        return;
    }
    
    // 发送数据到后端
    try {
        const response = await fetch('/api/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_id: studentId,
                name: name,
                class_name: className,
                face_image: imageData
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('学生添加成功', 'success', 'student-message');
            // 清空表单
            document.getElementById('student-form').reset();
        } else {
            showMessage('添加失败: ' + result.message, 'error', 'student-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'student-message');
    }
}

// 加载所有学生信息
async function loadStudents() {
    try {
        const response = await fetch('/api/students');
        const result = await response.json();
        
        if (result.success) {
            const tbody = document.querySelector('#students-table tbody');
            if (tbody) {
                tbody.innerHTML = '';
                
                result.data.forEach(student => {
                    // 创建照片占位符（实际项目中可以显示真实照片）
                    const photoCell = student.has_photo ? '✓' : '✗';
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${student.id}</td>
                        <td>${student.student_id}</td>
                        <td>${student.name}</td>
                        <td>${student.class_name}</td>
                        <td>${photoCell}</td>
                        <td>${student.course_count || 0}</td>
                        <td>
                            <button class="delete-btn" onclick="deleteStudent('${student.student_id}')">删除</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        } else {
            showMessage('加载学生信息失败: ' + result.message, 'error', 'students-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'students-message');
    }
}

// 删除学生
async function deleteStudent(studentId) {
    if (!confirm(`确定要删除学号为 ${studentId} 的学生吗？此操作不可撤销！`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/students/${studentId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('学生删除成功', 'success', 'students-message');
            // 重新加载学生列表
            loadStudents();
        } else {
            showMessage('删除失败: ' + result.message, 'error', 'students-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'students-message');
    }
}

// 调试函数：检查特定学生的人脸数据
async function debugStudent(studentId) {
    try {
        const response = await fetch(`/api/debug/student/${studentId}`);
        const result = await response.json();
        
        if (result.success) {
            console.log('Student debug info:', result.data);
            alert(`学生信息:
ID: ${result.data.id}
学号: ${result.data.student_id}
姓名: ${result.data.name}
班级: ${result.data.class_name}
有人脸数据: ${result.data.has_face_data}
数据长度: ${result.data.face_encoding_length}`);
        } else {
            alert('获取学生信息失败: ' + result.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('网络错误，请稍后再试');
    }
}

// 为选课功能加载学生列表
async function loadStudentsForSelection() {
    try {
        const response = await fetch('/api/students');
        const result = await response.json();
        
        if (result.success) {
            const studentSelect = document.getElementById('select-student');
            const viewStudentSelect = document.getElementById('view-student');
            
            // 清空现有选项
            studentSelect.innerHTML = '<option value="">请选择学生</option>';
            viewStudentSelect.innerHTML = '<option value="">请选择学生</option>';
            
            // 添加学生选项
            result.data.forEach(student => {
                const option1 = document.createElement('option');
                option1.value = student.student_id;
                option1.textContent = `${student.name} (${student.student_id})`;
                studentSelect.appendChild(option1);
                
                const option2 = document.createElement('option');
                option2.value = student.student_id;
                option2.textContent = `${student.name} (${student.student_id})`;
                viewStudentSelect.appendChild(option2);
            });
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// 为选课功能加载课程列表
async function loadCoursesForSelection() {
    try {
        const response = await fetch('/api/courses');
        const result = await response.json();
        
        if (result.success) {
            const courseSelect = document.getElementById('select-course');
            
            // 清空现有选项
            courseSelect.innerHTML = '<option value="">请选择课程</option>';
            
            // 添加课程选项
            result.data.forEach(course => {
                const option = document.createElement('option');
                option.value = course.id;
                option.textContent = `${course.course_name} (${course.weekday} ${course.course_time_start}-${course.course_time_end})`;
                courseSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

// 为学生分配课程
async function assignCourseToStudent() {
    const studentId = document.getElementById('select-student').value;
    const courseId = document.getElementById('select-course').value;
    
    if (!studentId || !courseId) {
        showMessage('请选择学生和课程', 'error', 'assignment-message');
        return;
    }
    
    try {
        const response = await fetch('/api/student_courses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_id: studentId,
                course_id: parseInt(courseId)
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('课程分配成功', 'success', 'assignment-message');
        } else {
            showMessage('分配失败: ' + result.message, 'error', 'assignment-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'assignment-message');
    }
}

// 加载学生已选课程
async function loadStudentCourses() {
    const studentId = document.getElementById('view-student').value;
    
    if (!studentId) {
        return;
    }
    
    try {
        const response = await fetch(`/api/student_courses/${studentId}`);
        const result = await response.json();
        
        if (result.success) {
            const tbody = document.querySelector('#student-courses-table tbody');
            if (tbody) {
                tbody.innerHTML = '';
                
                result.data.forEach(course => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${course.course_name}</td>
                        <td>${course.course_time_start}</td>
                        <td>${course.course_time_end}</td>
                        <td>${course.weekday}</td>
                        <td>
                            <button class="delete-btn" onclick="deleteStudentCourse('${studentId}', ${course.id})">删除</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
                
                if (result.data.length === 0) {
                    const row = document.createElement('tr');
                    row.innerHTML = '<td colspan="5">该学生尚未选择任何课程</td>';
                    tbody.appendChild(row);
                }
            }
        } else {
            showMessage('加载学生课程失败: ' + result.message, 'error', 'student-courses-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'student-courses-message');
    }
}

// 删除学生课程关联
async function deleteStudentCourse(studentId, courseId) {
    if (!confirm(`确定要删除该学生的课程关联吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/student_courses/${studentId}/${courseId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('学生课程关联删除成功', 'success', 'student-courses-message');
            // 重新加载学生课程列表
            loadStudentCourses();
        } else {
            showMessage('删除失败: ' + result.message, 'error', 'student-courses-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'student-courses-message');
    }
}

// 添加课程
async function addCourse(event) {
    event.preventDefault();
    
    const courseName = document.getElementById('course-name').value;
    const courseTimeStart = document.getElementById('course-time-start').value;
    const courseTimeEnd = document.getElementById('course-time-end').value;
    const weekday = document.getElementById('weekday').value;
    
    // 发送数据到后端
    try {
        const response = await fetch('/api/courses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                course_name: courseName,
                course_time_start: courseTimeStart,
                course_time_end: courseTimeEnd,
                weekday: weekday
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('课程添加成功', 'success', 'course-message');
            // 清空表单
            document.getElementById('course-form').reset();
            // 重新加载课程列表
            loadCourses();
            // 重新加载选课页面的课程列表
            loadCoursesForSelection();
        } else {
            showMessage('添加失败: ' + result.message, 'error', 'course-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'course-message');
    }
}

// 人脸识别考勤
async function recognizeAttendance() {
    const video = document.getElementById('attendance-video');
    const canvas = document.getElementById('attendance-canvas');
    const context = canvas.getContext('2d');
    
    // 绘制当前视频帧到画布
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // 获取图片数据
    const imageData = canvas.toDataURL('image/jpeg');
    
    // 显示正在识别消息
    showMessage('正在识别...', 'success', 'attendance-message');
    
    // 发送数据到后端进行识别
    try {
        const response = await fetch('/api/attendance/recognize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                face_image: imageData
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(`${result.message}！学号：${result.student_id}，时间：${result.time}`, 'success', 'attendance-message');
            // 刷新考勤记录
            loadAttendanceRecords();
        } else {
            showMessage('识别失败: ' + result.message, 'error', 'attendance-message');
            
            // 如果是未识别到学生，提供更多信息
            if (result.message === '未识别到学生') {
                showMessage('请确保：1. 已添加该学生的人脸数据；2. 人脸清晰可见；3. 光线充足', 'error', 'attendance-message');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'attendance-message');
    }
}

// 测试人脸识别功能
async function testRecognize() {
    const video = document.getElementById('attendance-video');
    const canvas = document.getElementById('attendance-canvas');
    const context = canvas.getContext('2d');
    
    // 绘制当前视频帧到画布
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // 获取图片数据
    const imageData = canvas.toDataURL('image/jpeg');
    
    // 显示正在识别消息
    showMessage('正在测试识别...', 'success', 'attendance-message');
    
    // 发送数据到后端进行测试识别
    try {
        const response = await fetch('/api/test_recognize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                face_image: imageData
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(`测试识别成功！学号：${result.student_id}`, 'success', 'attendance-message');
        } else {
            showMessage('测试识别失败: ' + result.message, 'error', 'attendance-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'attendance-message');
    }
}

// 加载课程列表
async function loadCourses() {
    try {
        const response = await fetch('/api/courses');
        const result = await response.json();
        
        if (result.success) {
            const tbody = document.querySelector('#courses-table tbody');
            if (tbody) {
                tbody.innerHTML = '';
                
                result.data.forEach(course => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${course.course_name}</td>
                        <td>${course.course_time_start}</td>
                        <td>${course.course_time_end}</td>
                        <td>${course.weekday}</td>
                        <td>
                            <button class="delete-btn" onclick="deleteCourse(${course.id})">删除</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        } else {
            showMessage('加载课程失败: ' + result.message, 'error', 'courses-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'courses-message');
    }
}

// 删除课程
async function deleteCourse(courseId) {
    if (!confirm(`确定要删除ID为 ${courseId} 的课程吗？此操作不可撤销！`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/courses/${courseId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('课程删除成功', 'success', 'courses-message');
            // 重新加载课程列表
            loadCourses();
        } else {
            showMessage('删除失败: ' + result.message, 'error', 'courses-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'courses-message');
    }
}

// 加载考勤记录
async function loadAttendanceRecords() {
    try {
        const response = await fetch('/api/attendance');
        const result = await response.json();
        
        if (result.success) {
            const tbody = document.querySelector('#records table tbody');
            tbody.innerHTML = '';
            
            result.data.forEach(record => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${record.student_id}</td>
                    <td>${record.name}</td>
                    <td>${record.class_name}</td>
                    <td>${record.course_name}</td>
                    <td>${record.record_date}</td>
                    <td>${record.record_time}</td>
                    <td>${record.status || '正常'}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            showMessage('加载记录失败: ' + result.message, 'error', 'records-message');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('网络错误，请稍后再试', 'error', 'records-message');
    }
}

// 显示消息
function showMessage(message, type, elementId) {
    const messageElement = document.getElementById(elementId);
    messageElement.textContent = message;
    messageElement.className = 'message ' + type;
}


function checkAbsences() {
    fetch('/api/attendance/check_absences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        alert('缺勤检查完成');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('检查失败');
    });
}