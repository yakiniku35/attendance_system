from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.course import Course
from src.models.attendance_form import AttendanceForm
from src.models.attendance_record import AttendanceRecord
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from functools import wraps

analytics_bp = Blueprint('analytics', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '需要登入'}), 401
        return f(*args, **kwargs)
    return decorated_function

@analytics_bp.route('/analytics/student/<int:student_id>', methods=['GET'])
@login_required
def get_student_analytics(student_id):
    user = User.query.get(session['user_id'])
    
    # 檢查權限：學生只能查看自己的數據，老師和管理員可以查看所有學生
    if user.role == 'student' and user.id != student_id:
        return jsonify({'error': '權限不足'}), 403
    
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'error': '指定用戶不是學生'}), 400
    
    # 獲取日期範圍參數
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = AttendanceRecord.query.filter_by(student_id=student_id)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.join(AttendanceForm).filter(AttendanceForm.form_date >= start_date)
        except ValueError:
            return jsonify({'error': '開始日期格式錯誤'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.join(AttendanceForm).filter(AttendanceForm.form_date <= end_date)
        except ValueError:
            return jsonify({'error': '結束日期格式錯誤'}), 400
    
    records = query.all()
    
    # 統計各種狀態的數量
    status_count = {}
    course_stats = {}
    monthly_stats = {}
    
    for record in records:
        # 狀態統計
        status = record.status
        status_count[status] = status_count.get(status, 0) + 1
        
        # 課程統計
        form = AttendanceForm.query.get(record.form_id)
        if form:
            course = Course.query.get(form.course_id)
            if course:
                course_key = f"{course.course_code} - {course.course_name}"
                if course_key not in course_stats:
                    course_stats[course_key] = {}
                course_stats[course_key][status] = course_stats[course_key].get(status, 0) + 1
            
            # 月度統計
            month_key = form.form_date.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {}
            monthly_stats[month_key][status] = monthly_stats[month_key].get(status, 0) + 1
    
    # 計算出席率
    total_records = len(records)
    present_count = status_count.get('present', 0)
    attendance_rate = (present_count / total_records * 100) if total_records > 0 else 0
    
    return jsonify({
        'student_info': student.to_dict(),
        'total_records': total_records,
        'attendance_rate': round(attendance_rate, 2),
        'status_count': status_count,
        'course_stats': course_stats,
        'monthly_stats': monthly_stats
    })

@analytics_bp.route('/analytics/course/<int:course_id>', methods=['GET'])
@login_required
def get_course_analytics(course_id):
    user = User.query.get(session['user_id'])
    course = Course.query.get_or_404(course_id)
    
    # 檢查權限：老師只能查看自己的課程，管理員可以查看所有課程
    if user.role == 'teacher' and course.teacher_id != user.id:
        return jsonify({'error': '權限不足'}), 403
    elif user.role == 'student':
        return jsonify({'error': '學生無法查看課程統計'}), 403
    
    # 獲取日期範圍參數
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = AttendanceForm.query.filter_by(course_id=course_id)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(AttendanceForm.form_date >= start_date)
        except ValueError:
            return jsonify({'error': '開始日期格式錯誤'}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(AttendanceForm.form_date <= end_date)
        except ValueError:
            return jsonify({'error': '結束日期格式錯誤'}), 400
    
    forms = query.all()
    
    # 統計數據
    total_forms = len(forms)
    total_responses = 0
    status_count = {}
    daily_stats = {}
    student_stats = {}
    
    for form in forms:
        records = AttendanceRecord.query.filter_by(form_id=form.id).all()
        total_responses += len(records)
        
        # 日期統計
        date_key = form.form_date.isoformat()
        daily_stats[date_key] = {
            'form_title': form.title,
            'total_responses': len(records),
            'status_count': {}
        }
        
        for record in records:
            status = record.status
            status_count[status] = status_count.get(status, 0) + 1
            daily_stats[date_key]['status_count'][status] = daily_stats[date_key]['status_count'].get(status, 0) + 1
            
            # 學生統計
            student = User.query.get(record.student_id)
            if student:
                student_key = f"{student.student_id} - {student.full_name}"
                if student_key not in student_stats:
                    student_stats[student_key] = {}
                student_stats[student_key][status] = student_stats[student_key].get(status, 0) + 1
    
    # 計算平均出席率
    present_count = status_count.get('present', 0)
    average_attendance_rate = (present_count / total_responses * 100) if total_responses > 0 else 0
    
    return jsonify({
        'course_info': course.to_dict(),
        'total_forms': total_forms,
        'total_responses': total_responses,
        'average_attendance_rate': round(average_attendance_rate, 2),
        'status_count': status_count,
        'daily_stats': daily_stats,
        'student_stats': student_stats
    })

@analytics_bp.route('/analytics/overview', methods=['GET'])
@login_required
def get_system_overview():
    user = User.query.get(session['user_id'])
    
    # 只有管理員可以查看系統概覽
    if user.role != 'admin':
        return jsonify({'error': '需要管理員權限'}), 403
    
    # 基本統計
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    total_courses = Course.query.count()
    total_forms = AttendanceForm.query.count()
    total_records = AttendanceRecord.query.count()
    
    # 最近30天的活動統計
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    recent_forms = AttendanceForm.query.filter(AttendanceForm.form_date >= thirty_days_ago).count()
    recent_records = AttendanceRecord.query.filter(AttendanceRecord.submitted_at >= datetime.combine(thirty_days_ago, datetime.min.time())).count()
    
    # 出席狀態統計
    status_stats = db.session.query(
        AttendanceRecord.status,
        func.count(AttendanceRecord.id)
    ).group_by(AttendanceRecord.status).all()
    
    status_count = {status: count for status, count in status_stats}
    
    # 每月統計
    monthly_stats = db.session.query(
        func.strftime('%Y-%m', AttendanceForm.form_date).label('month'),
        func.count(AttendanceRecord.id).label('total_records'),
        func.sum(func.case([(AttendanceRecord.status == 'present', 1)], else_=0)).label('present_count')
    ).join(AttendanceRecord, AttendanceForm.id == AttendanceRecord.form_id)\
     .group_by(func.strftime('%Y-%m', AttendanceForm.form_date))\
     .order_by('month').all()
    
    monthly_data = []
    for month, total, present in monthly_stats:
        attendance_rate = (present / total * 100) if total > 0 else 0
        monthly_data.append({
            'month': month,
            'total_records': total,
            'present_count': present,
            'attendance_rate': round(attendance_rate, 2)
        })
    
    return jsonify({
        'basic_stats': {
            'total_users': total_users,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_courses': total_courses,
            'total_forms': total_forms,
            'total_records': total_records
        },
        'recent_activity': {
            'recent_forms': recent_forms,
            'recent_records': recent_records
        },
        'status_count': status_count,
        'monthly_stats': monthly_data
    })

