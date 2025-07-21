#!/usr/bin/env python3
"""
初始化測試數據腳本
建立管理員、老師、學生帳號以及課程和出缺席記錄
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import db, User
from src.models.course import Course
from src.models.course_enrollment import CourseEnrollment
from src.models.attendance_form import AttendanceForm
from src.models.attendance_record import AttendanceRecord
from datetime import datetime, date, time
from flask import Flask

# 建立Flask應用程式
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def init_test_data():
    with app.app_context():
        # 清空現有數據
        db.drop_all()
        db.create_all()
        
        print("正在建立測試數據...")
        
        # 建立管理員帳號
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin',
            full_name='系統管理員'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # 建立老師帳號
        teacher1 = User(
            username='teacher1',
            email='teacher1@example.com',
            role='teacher',
            full_name='王老師'
        )
        teacher1.set_password('password123')
        db.session.add(teacher1)
        
        teacher2 = User(
            username='teacher2',
            email='teacher2@example.com',
            role='teacher',
            full_name='李老師'
        )
        teacher2.set_password('password123')
        db.session.add(teacher2)
        
        # 建立學生帳號
        students_data = [
            ('student1', 'student1@example.com', '張小明', 'S001'),
            ('student2', 'student2@example.com', '陳小華', 'S002'),
            ('student3', 'student3@example.com', '林小美', 'S003'),
            ('student4', 'student4@example.com', '黃小強', 'S004'),
            ('student5', 'student5@example.com', '劉小芳', 'S005'),
        ]
        
        students = []
        for username, email, full_name, student_id in students_data:
            student = User(
                username=username,
                email=email,
                role='student',
                full_name=full_name,
                student_id=student_id
            )
            student.set_password('password123')
            db.session.add(student)
            students.append(student)
        
        # 提交用戶數據
        db.session.commit()
        
        # 建立課程
        course1 = Course(
            course_code='CS101',
            course_name='計算機概論',
            teacher_id=teacher1.id,
            description='計算機科學基礎課程'
        )
        db.session.add(course1)
        
        course2 = Course(
            course_code='MATH201',
            course_name='高等數學',
            teacher_id=teacher2.id,
            description='數學進階課程'
        )
        db.session.add(course2)
        
        course3 = Course(
            course_code='ENG101',
            course_name='英文寫作',
            teacher_id=teacher1.id,
            description='英文寫作基礎課程'
        )
        db.session.add(course3)
        
        # 提交課程數據
        db.session.commit()
        
        # 學生加入課程
        enrollments_data = [
            (students[0].id, course1.id),  # 張小明 -> 計算機概論
            (students[0].id, course2.id),  # 張小明 -> 高等數學
            (students[1].id, course1.id),  # 陳小華 -> 計算機概論
            (students[1].id, course3.id),  # 陳小華 -> 英文寫作
            (students[2].id, course1.id),  # 林小美 -> 計算機概論
            (students[2].id, course2.id),  # 林小美 -> 高等數學
            (students[2].id, course3.id),  # 林小美 -> 英文寫作
            (students[3].id, course2.id),  # 黃小強 -> 高等數學
            (students[3].id, course3.id),  # 黃小強 -> 英文寫作
            (students[4].id, course1.id),  # 劉小芳 -> 計算機概論
        ]
        
        for student_id, course_id in enrollments_data:
            enrollment = CourseEnrollment(
                student_id=student_id,
                course_id=course_id
            )
            db.session.add(enrollment)
        
        # 提交課程加入數據
        db.session.commit()
        
        # 建立出缺席表單
        forms_data = [
            (course1.id, teacher1.id, '第一週課程', '2024-01-08', '09:00', '10:30'),
            (course1.id, teacher1.id, '第二週課程', '2024-01-15', '09:00', '10:30'),
            (course1.id, teacher1.id, '第三週課程', '2024-01-22', '09:00', '10:30'),
            (course2.id, teacher2.id, '數學第一課', '2024-01-09', '14:00', '15:30'),
            (course2.id, teacher2.id, '數學第二課', '2024-01-16', '14:00', '15:30'),
            (course3.id, teacher1.id, '英文寫作練習', '2024-01-10', '10:30', '12:00'),
        ]
        
        forms = []
        for course_id, teacher_id, title, form_date, start_time, end_time in forms_data:
            form = AttendanceForm(
                title=title,
                course_id=course_id,
                teacher_id=teacher_id,
                form_date=datetime.strptime(form_date, '%Y-%m-%d').date(),
                start_time=datetime.strptime(start_time, '%H:%M').time(),
                end_time=datetime.strptime(end_time, '%H:%M').time(),
                description='課程出缺席記錄',
                is_active=True
            )
            db.session.add(form)
            forms.append(form)
        
        # 提交表單數據
        db.session.commit()
        
        # 建立出缺席記錄
        import random
        statuses = ['present', 'absent', 'late', 'excused']
        
        for form in forms:
            # 獲取該課程的學生
            enrollments = CourseEnrollment.query.filter_by(course_id=form.course_id, is_active=True).all()
            
            for enrollment in enrollments:
                # 隨機生成出缺席狀態，但大部分是出席
                status = random.choices(statuses, weights=[70, 10, 15, 5])[0]
                
                record = AttendanceRecord(
                    form_id=form.id,
                    student_id=enrollment.student_id,
                    status=status,
                    notes='測試記錄' if status in ['excused', 'late'] else ''
                )
                db.session.add(record)
        
        # 提交出缺席記錄
        db.session.commit()
        
        print("測試數據建立完成！")
        print("\n帳號資訊：")
        print("管理員: admin / admin123")
        print("老師1: teacher1 / password123 (王老師)")
        print("老師2: teacher2 / password123 (李老師)")
        print("學生: student1-student5 / password123")
        print(f"\n課程加入代碼：")
        print(f"計算機概論 (CS101): {course1.join_code}")
        print(f"高等數學 (MATH201): {course2.join_code}")
        print(f"英文寫作 (ENG101): {course3.join_code}")

if __name__ == '__main__':
    init_test_data()

