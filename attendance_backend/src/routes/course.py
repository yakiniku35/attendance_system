from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.course import Course
from src.models.course_enrollment import CourseEnrollment
from functools import wraps

course_bp = Blueprint('course', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '需要登入'}), 401
        return f(*args, **kwargs)
    return decorated_function

def teacher_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '需要登入'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.role not in ['teacher', 'admin']:
            return jsonify({'error': '需要老師或管理員權限'}), 403
        return f(*args, **kwargs)
    return decorated_function

@course_bp.route('/courses', methods=['GET'])
@login_required
def get_courses():
    user = User.query.get(session['user_id'])
    
    if user.role == 'admin':
        # 管理員可以看到所有課程
        courses = Course.query.filter_by(is_active=True).all()
    elif user.role == 'teacher':
        # 老師只能看到自己的課程
        courses = Course.query.filter_by(teacher_id=user.id, is_active=True).all()
    else:  # student
        # 學生只能看到已加入的課程
        enrollments = CourseEnrollment.query.filter_by(student_id=user.id, is_active=True).all()
        course_ids = [e.course_id for e in enrollments]
        courses = Course.query.filter(Course.id.in_(course_ids), Course.is_active == True).all()
    
    result = []
    for course in courses:
        course_dict = course.to_dict()
        # 添加老師資訊
        teacher = User.query.get(course.teacher_id)
        if teacher:
            course_dict['teacher_name'] = teacher.full_name
        
        # 如果是老師或管理員，添加學生數量
        if user.role in ['teacher', 'admin']:
            enrollment_count = CourseEnrollment.query.filter_by(course_id=course.id, is_active=True).count()
            course_dict['student_count'] = enrollment_count
        
        result.append(course_dict)
    
    return jsonify(result)

@course_bp.route('/courses', methods=['POST'])
@teacher_or_admin_required
def create_course():
    data = request.json
    user = User.query.get(session['user_id'])
    
    # 檢查必要欄位
    required_fields = ['course_code', 'course_name']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必要欄位: {field}'}), 400
    
    # 檢查課程代碼是否已存在
    if Course.query.filter_by(course_code=data['course_code']).first():
        return jsonify({'error': '課程代碼已存在'}), 400
    
    # 如果是管理員，可以指定老師；否則使用當前用戶
    teacher_id = data.get('teacher_id', user.id) if user.role == 'admin' else user.id
    
    course = Course(
        course_code=data['course_code'],
        course_name=data['course_name'],
        teacher_id=teacher_id,
        description=data.get('description', '')
    )
    
    db.session.add(course)
    db.session.commit()
    
    return jsonify(course.to_dict()), 201

@course_bp.route('/courses/join', methods=['POST'])
@login_required
def join_course():
    user = User.query.get(session['user_id'])
    data = request.json
    
    # 只有學生可以加入課程
    if user.role != 'student':
        return jsonify({'error': '只有學生可以加入課程'}), 403
    
    # 檢查必要欄位
    if 'join_code' not in data:
        return jsonify({'error': '缺少課程加入代碼'}), 400
    
    # 查找課程
    course = Course.query.filter_by(join_code=data['join_code'], is_active=True).first()
    if not course:
        return jsonify({'error': '課程代碼無效或課程不存在'}), 400
    
    # 檢查是否已經加入
    existing_enrollment = CourseEnrollment.query.filter_by(
        student_id=user.id, 
        course_id=course.id
    ).first()
    
    if existing_enrollment:
        if existing_enrollment.is_active:
            return jsonify({'error': '您已經加入此課程'}), 400
        else:
            # 重新啟用
            existing_enrollment.is_active = True
            db.session.commit()
            return jsonify({
                'message': '成功重新加入課程',
                'course': course.to_dict()
            })
    
    # 建立新的加入記錄
    enrollment = CourseEnrollment(
        student_id=user.id,
        course_id=course.id
    )
    
    db.session.add(enrollment)
    db.session.commit()
    
    return jsonify({
        'message': '成功加入課程',
        'course': course.to_dict()
    }), 201

@course_bp.route('/courses/<int:course_id>/leave', methods=['POST'])
@login_required
def leave_course(course_id):
    user = User.query.get(session['user_id'])
    
    # 只有學生可以退出課程
    if user.role != 'student':
        return jsonify({'error': '只有學生可以退出課程'}), 403
    
    # 查找加入記錄
    enrollment = CourseEnrollment.query.filter_by(
        student_id=user.id,
        course_id=course_id,
        is_active=True
    ).first()
    
    if not enrollment:
        return jsonify({'error': '您尚未加入此課程'}), 400
    
    # 停用加入記錄
    enrollment.is_active = False
    db.session.commit()
    
    return jsonify({'message': '成功退出課程'})

@course_bp.route('/courses/<int:course_id>/students', methods=['GET'])
@teacher_or_admin_required
def get_course_students(course_id):
    course = Course.query.get_or_404(course_id)
    user = User.query.get(session['user_id'])
    
    # 檢查權限
    if user.role == 'teacher' and course.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    
    # 獲取課程學生
    enrollments = CourseEnrollment.query.filter_by(course_id=course_id, is_active=True).all()
    students = []
    
    for enrollment in enrollments:
        student = User.query.get(enrollment.student_id)
        if student:
            student_dict = student.to_dict()
            student_dict['enrolled_at'] = enrollment.enrolled_at.isoformat()
            students.append(student_dict)
    
    return jsonify({
        'course': course.to_dict(),
        'students': students,
        'total_students': len(students)
    })

@course_bp.route('/courses/<int:course_id>', methods=['GET'])
@login_required
def get_course(course_id):
    course = Course.query.get_or_404(course_id)
    user = User.query.get(session['user_id'])
    
    # 檢查權限
    if user.role == 'teacher' and course.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    elif user.role == 'student':
        # 學生只能查看已加入的課程
        enrollment = CourseEnrollment.query.filter_by(
            student_id=user.id,
            course_id=course_id,
            is_active=True
        ).first()
        if not enrollment:
            return jsonify({'error': '您尚未加入此課程'}), 403
    
    course_dict = course.to_dict()
    
    # 添加老師資訊
    teacher = User.query.get(course.teacher_id)
    if teacher:
        course_dict['teacher_name'] = teacher.full_name
    
    # 如果是老師或管理員，添加學生數量
    if user.role in ['teacher', 'admin']:
        enrollment_count = CourseEnrollment.query.filter_by(course_id=course.id, is_active=True).count()
        course_dict['student_count'] = enrollment_count
    
    return jsonify(course_dict)

@course_bp.route('/courses/<int:course_id>', methods=['PUT'])
@teacher_or_admin_required
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    user = User.query.get(session['user_id'])
    data = request.json
    
    # 檢查權限
    if user.role == 'teacher' and course.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    
    course.course_code = data.get('course_code', course.course_code)
    course.course_name = data.get('course_name', course.course_name)
    course.description = data.get('description', course.description)
    course.is_active = data.get('is_active', course.is_active)
    
    # 只有管理員可以更改老師
    if user.role == 'admin' and 'teacher_id' in data:
        course.teacher_id = data['teacher_id']
    
    db.session.commit()
    return jsonify(course.to_dict())

@course_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@teacher_or_admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    user = User.query.get(session['user_id'])
    
    # 檢查權限
    if user.role == 'teacher' and course.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    
    # 軟刪除：設為不活躍
    course.is_active = False
    db.session.commit()
    return jsonify({'message': '課程已刪除'})

