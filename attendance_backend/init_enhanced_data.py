#!/usr/bin/env python3
"""
增強版出缺席管理系統初始化腳本
包含管理員功能、郵件通知、密碼重置和地理位置驗證
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import db, User
from src.models.course import Course
from src.models.course_enrollment import CourseEnrollment
from src.models.attendance_form import AttendanceForm
from src.models.attendance_record import AttendanceRecord
from src.models.password_reset import PasswordReset, EmailVerification
from datetime import datetime, date, time, timedelta
import random

def init_enhanced_database():
    """初始化增強版資料庫"""
    print("正在初始化增強版資料庫...")
    
    # 刪除現有資料庫檔案
    db_path = os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("已刪除舊資料庫檔案")
    
    # 確保資料庫目錄存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 創建所有表
    db.create_all()
    print("資料庫表創建完成")
    
    # 創建管理員
    admin = User(
        username='admin',
        email='admin@example.com',
        full_name='系統管理員',
        role='admin'
    )
    admin.set_password('admin123')
    admin.email_verified = True
    db.session.add(admin)
    
    # 創建老師
    teachers = [
        {
            'username': 'teacher1',
            'email': 'teacher1@example.com',
            'full_name': '王老師',
            'password': 'password123'
        },
        {
            'username': 'teacher2',
            'email': 'teacher2@example.com',
            'full_name': '李老師',
            'password': 'password123'
        },
        {
            'username': 'teacher3',
            'email': 'teacher3@example.com',
            'full_name': '張老師',
            'password': 'password123'
        }
    ]
    
    teacher_objects = []
    for teacher_data in teachers:
        teacher = User(
            username=teacher_data['username'],
            email=teacher_data['email'],
            full_name=teacher_data['full_name'],
            role='teacher'
        )
        teacher.set_password(teacher_data['password'])
        teacher.email_verified = True
        db.session.add(teacher)
        teacher_objects.append(teacher)
    
    # 創建學生
    students = [
        {
            'username': 'student1',
            'email': 'student1@example.com',
            'full_name': '張小明',
            'student_id': 'S001',
            'password': 'password123'
        },
        {
            'username': 'student2',
            'email': 'student2@example.com',
            'full_name': '陳小華',
            'student_id': 'S002',
            'password': 'password123'
        },
        {
            'username': 'student3',
            'email': 'student3@example.com',
            'full_name': '林小美',
            'student_id': 'S003',
            'password': 'password123'
        },
        {
            'username': 'student4',
            'email': 'student4@example.com',
            'full_name': '黃小強',
            'student_id': 'S004',
            'password': 'password123'
        },
        {
            'username': 'student5',
            'email': 'student5@example.com',
            'full_name': '劉小芳',
            'student_id': 'S005',
            'password': 'password123'
        },
        {
            'username': 'student6',
            'email': 'student6@example.com',
            'full_name': '吳小龍',
            'student_id': 'S006',
            'password': 'password123'
        },
        {
            'username': 'student7',
            'email': 'student7@example.com',
            'full_name': '趙小鳳',
            'student_id': 'S007',
            'password': 'password123'
        },
        {
            'username': 'student8',
            'email': 'student8@example.com',
            'full_name': '孫小傑',
            'student_id': 'S008',
            'password': 'password123'
        }
    ]
    
    student_objects = []
    for student_data in students:
        student = User(
            username=student_data['username'],
            email=student_data['email'],
            full_name=student_data['full_name'],
            student_id=student_data['student_id'],
            role='student'
        )
        student.set_password(student_data['password'])
        student.email_verified = True
        db.session.add(student)
        student_objects.append(student)
    
    # 提交用戶數據
    db.session.commit()
    print("用戶創建完成")
    
    # 創建課程
    courses = [
        {
            'course_code': 'CS101',
            'course_name': '計算機概論',
            'description': '介紹計算機基本概念和程式設計基礎',
            'teacher': teacher_objects[0]
        },
        {
            'course_code': 'MATH201',
            'course_name': '高等數學',
            'description': '微積分和線性代數的進階課程',
            'teacher': teacher_objects[1]
        },
        {
            'course_code': 'ENG101',
            'course_name': '英文寫作',
            'description': '學術英文寫作技巧和實務練習',
            'teacher': teacher_objects[0]
        },
        {
            'course_code': 'PHYS201',
            'course_name': '普通物理學',
            'description': '力學、熱學、電磁學基礎',
            'teacher': teacher_objects[2]
        },
        {
            'course_code': 'CHEM101',
            'course_name': '普通化學',
            'description': '化學基本原理和實驗',
            'teacher': teacher_objects[1]
        }
    ]
    
    course_objects = []
    for course_data in courses:
        course = Course(
            course_code=course_data['course_code'],
            course_name=course_data['course_name'],
            description=course_data['description'],
            teacher_id=course_data['teacher'].id
        )
        db.session.add(course)
        course_objects.append(course)
    
    # 提交課程數據
    db.session.commit()
    print("課程創建完成")
    
    # 學生加入課程
    enrollments = [
        # CS101 - 6個學生
        (student_objects[0], course_objects[0]),
        (student_objects[1], course_objects[0]),
        (student_objects[2], course_objects[0]),
        (student_objects[3], course_objects[0]),
        (student_objects[4], course_objects[0]),
        (student_objects[5], course_objects[0]),
        
        # MATH201 - 5個學生
        (student_objects[1], course_objects[1]),
        (student_objects[2], course_objects[1]),
        (student_objects[3], course_objects[1]),
        (student_objects[6], course_objects[1]),
        (student_objects[7], course_objects[1]),
        
        # ENG101 - 4個學生
        (student_objects[0], course_objects[2]),
        (student_objects[4], course_objects[2]),
        (student_objects[5], course_objects[2]),
        (student_objects[6], course_objects[2]),
        
        # PHYS201 - 3個學生
        (student_objects[2], course_objects[3]),
        (student_objects[3], course_objects[3]),
        (student_objects[7], course_objects[3]),
        
        # CHEM101 - 4個學生
        (student_objects[1], course_objects[4]),
        (student_objects[4], course_objects[4]),
        (student_objects[6], course_objects[4]),
        (student_objects[7], course_objects[4])
    ]
    
    for student, course in enrollments:
        enrollment = CourseEnrollment(
            student_id=student.id,
            course_id=course.id
        )
        db.session.add(enrollment)
    
    db.session.commit()
    print("學生課程加入完成")
    
    # 創建出缺席表單（包含地理位置驗證）
    forms_data = [
        # CS101 表單
        {
            'course': course_objects[0],
            'title': '第一週課程出席',
            'description': '計算機概論第一週課程',
            'form_date': date.today() - timedelta(days=14),
            'location_required': True,
            'allowed_latitude': 25.0330,  # 台北市
            'allowed_longitude': 121.5654,
            'location_radius': 200,
            'location_name': '資訊大樓101教室'
        },
        {
            'course': course_objects[0],
            'title': '第二週課程出席',
            'description': '程式設計基礎',
            'form_date': date.today() - timedelta(days=7),
            'location_required': True,
            'allowed_latitude': 25.0330,
            'allowed_longitude': 121.5654,
            'location_radius': 150,
            'location_name': '資訊大樓101教室'
        },
        {
            'course': course_objects[0],
            'title': '第三週課程出席',
            'description': '資料結構介紹',
            'form_date': date.today(),
            'location_required': False
        },
        
        # MATH201 表單
        {
            'course': course_objects[1],
            'title': '微積分第一章',
            'description': '極限與連續',
            'form_date': date.today() - timedelta(days=10),
            'location_required': True,
            'allowed_latitude': 25.0340,
            'allowed_longitude': 121.5650,
            'location_radius': 100,
            'location_name': '數學系201教室'
        },
        {
            'course': course_objects[1],
            'title': '微積分第二章',
            'description': '導數與微分',
            'form_date': date.today() - timedelta(days=3),
            'location_required': True,
            'allowed_latitude': 25.0340,
            'allowed_longitude': 121.5650,
            'location_radius': 100,
            'location_name': '數學系201教室'
        },
        
        # ENG101 表單
        {
            'course': course_objects[2],
            'title': '學術寫作基礎',
            'description': '論文結構與格式',
            'form_date': date.today() - timedelta(days=5),
            'location_required': False
        },
        
        # PHYS201 表單
        {
            'course': course_objects[3],
            'title': '力學基礎',
            'description': '牛頓運動定律',
            'form_date': date.today() - timedelta(days=8),
            'location_required': True,
            'allowed_latitude': 25.0320,
            'allowed_longitude': 121.5660,
            'location_radius': 150,
            'location_name': '物理實驗室'
        }
    ]
    
    form_objects = []
    for form_data in forms_data:
        form = AttendanceForm(
            course_id=form_data['course'].id,
            title=form_data['title'],
            description=form_data['description'],
            form_date=form_data['form_date'],
            location_required=form_data.get('location_required', False),
            allowed_latitude=form_data.get('allowed_latitude'),
            allowed_longitude=form_data.get('allowed_longitude'),
            location_radius=form_data.get('location_radius', 100),
            location_name=form_data.get('location_name')
        )
        db.session.add(form)
        form_objects.append(form)
    
    db.session.commit()
    print("出缺席表單創建完成")
    
    # 創建出缺席記錄（包含地理位置數據）
    statuses = ['present', 'absent', 'late', 'excused']
    
    for form in form_objects:
        # 獲取該課程的學生
        course_enrollments = CourseEnrollment.query.filter_by(
            course_id=form.course_id, is_active=True
        ).all()
        
        for enrollment in course_enrollments:
            # 80%的機率有記錄
            if random.random() < 0.8:
                status = random.choices(
                    statuses,
                    weights=[70, 15, 10, 5],  # 出席率較高
                    k=1
                )[0]
                
                # 生成位置數據
                latitude = None
                longitude = None
                location_accuracy = None
                
                if form.location_required and status in ['present', 'late']:
                    # 在允許範圍內生成隨機位置
                    if form.allowed_latitude and form.allowed_longitude:
                        # 在允許範圍內的隨機偏移
                        lat_offset = random.uniform(-0.001, 0.001)
                        lng_offset = random.uniform(-0.001, 0.001)
                        latitude = form.allowed_latitude + lat_offset
                        longitude = form.allowed_longitude + lng_offset
                        location_accuracy = random.uniform(5, 50)  # 5-50公尺精確度
                
                record = AttendanceRecord(
                    form_id=form.id,
                    student_id=enrollment.student_id,
                    status=status,
                    notes=f'自動生成的{status}記錄',
                    latitude=latitude,
                    longitude=longitude,
                    location_accuracy=location_accuracy
                )
                
                # 驗證位置
                if form.location_required:
                    record.verify_location()
                
                db.session.add(record)
    
    db.session.commit()
    print("出缺席記錄創建完成")
    
    # 創建一些郵件驗證記錄（示例）
    for i, student in enumerate(student_objects[:3]):
        verification = EmailVerification(student.id, 'registration')
        db.session.add(verification)
    
    db.session.commit()
    print("郵件驗證記錄創建完成")
    
    print("\n=== 增強版測試數據創建完成！===")
    print("\n帳號資訊：")
    print("管理員: admin / admin123")
    print("老師1: teacher1 / password123 (王老師)")
    print("老師2: teacher2 / password123 (李老師)")
    print("老師3: teacher3 / password123 (張老師)")
    print("學生: student1-student8 / password123")
    
    print("\n課程加入代碼：")
    for course in course_objects:
        print(f"{course.course_name} ({course.course_code}): {course.join_code}")
    
    print("\n新功能：")
    print("✅ 管理員用戶管理")
    print("✅ 郵件通知系統")
    print("✅ 密碼重置功能")
    print("✅ 地理位置驗證")
    print("✅ 增強的統計分析")

if __name__ == '__main__':
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        init_enhanced_database()

