from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.course import Course
from src.models.course_enrollment import CourseEnrollment
from src.models.attendance_form import AttendanceForm
from src.models.attendance_record import AttendanceRecord
from datetime import datetime, date, time
from functools import wraps

attendance_bp = Blueprint('attendance', __name__)

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

# 表單管理
@attendance_bp.route('/forms', methods=['GET'])
@login_required
def get_forms():
    user = User.query.get(session['user_id'])
    
    if user.role == 'admin':
        forms = AttendanceForm.query.all()
    elif user.role == 'teacher':
        forms = AttendanceForm.query.filter_by(teacher_id=user.id).all()
    else:  # student
        # 學生只能看到已加入課程的開放表單
        enrollments = CourseEnrollment.query.filter_by(student_id=user.id, is_active=True).all()
        course_ids = [e.course_id for e in enrollments]
        forms = AttendanceForm.query.filter(
            AttendanceForm.course_id.in_(course_ids),
            AttendanceForm.is_active == True
        ).all()
    
    result = []
    for form in forms:
        form_dict = form.to_dict()
        # 添加課程資訊
        course = Course.query.get(form.course_id)
        if course:
            form_dict['course_name'] = course.course_name
            form_dict['course_code'] = course.course_code
        
        # 如果是學生，檢查是否已填寫
        if user.role == 'student':
            record = AttendanceRecord.query.filter_by(
                form_id=form.id, 
                student_id=user.id
            ).first()
            form_dict['submitted'] = record is not None
            if record:
                form_dict['my_status'] = record.status
        
        result.append(form_dict)
    
    return jsonify(result)

@attendance_bp.route('/forms', methods=['POST'])
@teacher_or_admin_required
def create_form():
    data = request.json
    user = User.query.get(session['user_id'])
    
    # 檢查必要欄位
    required_fields = ['title', 'course_id', 'form_date', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必要欄位: {field}'}), 400
    
    # 檢查課程是否存在
    course = Course.query.get(data['course_id'])
    if not course:
        return jsonify({'error': '課程不存在'}), 400
    
    # 檢查權限（老師只能為自己的課程建立表單）
    if user.role == 'teacher' and course.teacher_id != user.id:
        return jsonify({'error': '只能為自己的課程建立表單'}), 403
    
    try:
        form_date = datetime.strptime(data['form_date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': '日期或時間格式錯誤'}), 400
    
    form = AttendanceForm(
        title=data['title'],
        course_id=data['course_id'],
        teacher_id=user.id,
        form_date=form_date,
        start_time=start_time,
        end_time=end_time,
        description=data.get('description', ''),
        is_active=data.get('is_active', True)
    )
    
    db.session.add(form)
    db.session.commit()
    
    return jsonify(form.to_dict()), 201

@attendance_bp.route('/forms/<int:form_id>', methods=['GET'])
@login_required
def get_form(form_id):
    form = AttendanceForm.query.get_or_404(form_id)
    user = User.query.get(session['user_id'])
    
    # 檢查權限
    if user.role == 'teacher' and form.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    
    form_dict = form.to_dict()
    
    # 添加課程資訊
    course = Course.query.get(form.course_id)
    if course:
        form_dict['course_name'] = course.course_name
        form_dict['course_code'] = course.course_code
    
    # 如果是老師或管理員，添加統計資訊
    if user.role in ['teacher', 'admin']:
        records = AttendanceRecord.query.filter_by(form_id=form_id).all()
        form_dict['total_responses'] = len(records)
        form_dict['status_count'] = {}
        for record in records:
            status = record.status
            form_dict['status_count'][status] = form_dict['status_count'].get(status, 0) + 1
    
    return jsonify(form_dict)

@attendance_bp.route('/forms/<int:form_id>', methods=['PUT'])
@teacher_or_admin_required
def update_form(form_id):
    form = AttendanceForm.query.get_or_404(form_id)
    user = User.query.get(session['user_id'])
    data = request.json
    
    # 檢查權限
    if user.role == 'teacher' and form.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    
    form.title = data.get('title', form.title)
    form.description = data.get('description', form.description)
    form.is_active = data.get('is_active', form.is_active)
    
    if 'form_date' in data:
        try:
            form.form_date = datetime.strptime(data['form_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': '日期格式錯誤'}), 400
    
    if 'start_time' in data:
        try:
            form.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': '開始時間格式錯誤'}), 400
    
    if 'end_time' in data:
        try:
            form.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': '結束時間格式錯誤'}), 400
    
    db.session.commit()
    return jsonify(form.to_dict())

@attendance_bp.route('/forms/<int:form_id>', methods=['DELETE'])
@teacher_or_admin_required
def delete_form(form_id):
    form = AttendanceForm.query.get_or_404(form_id)
    user = User.query.get(session['user_id'])
    
    # 檢查權限
    if user.role == 'teacher' and form.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    
    db.session.delete(form)
    db.session.commit()
    return '', 204

# 出缺席記錄管理
@attendance_bp.route('/forms/<int:form_id>/submit', methods=['POST'])
@login_required
def submit_attendance(form_id):
    form = AttendanceForm.query.get_or_404(form_id)
    user = User.query.get(session['user_id'])
    data = request.json
    
    # 只有學生可以提交出缺席
    if user.role != 'student':
        return jsonify({'error': '只有學生可以提交出缺席記錄'}), 403
    
    # 檢查表單是否開放
    if not form.is_active:
        return jsonify({'error': '表單已關閉'}), 400
    
    # 檢查必要欄位
    if 'status' not in data:
        return jsonify({'error': '缺少出缺席狀態'}), 400
    
    # 檢查狀態是否有效
    valid_statuses = ['present', 'absent', 'late', 'excused']
    if data['status'] not in valid_statuses:
        return jsonify({'error': '無效的出缺席狀態'}), 400
    
    # 檢查是否已經提交過
    existing_record = AttendanceRecord.query.filter_by(
        form_id=form_id, 
        student_id=user.id
    ).first()
    
    if existing_record:
        # 更新現有記錄
        existing_record.status = data['status']
        existing_record.notes = data.get('notes', '')
        existing_record.submitted_at = datetime.utcnow()
        db.session.commit()
        return jsonify(existing_record.to_dict())
    else:
        # 建立新記錄
        record = AttendanceRecord(
            form_id=form_id,
            student_id=user.id,
            status=data['status'],
            notes=data.get('notes', '')
        )
        db.session.add(record)
        db.session.commit()
        return jsonify(record.to_dict()), 201

@attendance_bp.route('/forms/<int:form_id>/records', methods=['GET'])
@teacher_or_admin_required
def get_form_records(form_id):
    form = AttendanceForm.query.get_or_404(form_id)
    user = User.query.get(session['user_id'])
    
    # 檢查權限
    if user.role == 'teacher' and form.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    
    records = AttendanceRecord.query.filter_by(form_id=form_id).all()
    result = []
    
    for record in records:
        record_dict = record.to_dict()
        # 添加學生資訊
        student = User.query.get(record.student_id)
        if student:
            record_dict['student_name'] = student.full_name
            record_dict['student_id_number'] = student.student_id
        result.append(record_dict)
    
    return jsonify(result)

@attendance_bp.route('/my-records', methods=['GET'])
@login_required
def get_my_records():
    user = User.query.get(session['user_id'])
    
    # 只有學生可以查看自己的記錄
    if user.role != 'student':
        return jsonify({'error': '只有學生可以查看個人出缺席記錄'}), 403
    
    records = AttendanceRecord.query.filter_by(student_id=user.id).all()
    result = []
    
    for record in records:
        record_dict = record.to_dict()
        # 添加表單和課程資訊
        form = AttendanceForm.query.get(record.form_id)
        if form:
            record_dict['form_title'] = form.title
            record_dict['form_date'] = form.form_date.isoformat()
            course = Course.query.get(form.course_id)
            if course:
                record_dict['course_name'] = course.course_name
                record_dict['course_code'] = course.course_code
        result.append(record_dict)
    
    return jsonify(result)

