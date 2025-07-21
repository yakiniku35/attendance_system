from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.course import Course
from src.models.course_enrollment import CourseEnrollment
from src.models.attendance_form import AttendanceForm
from src.models.attendance_record import AttendanceRecord
from functools import wraps
from datetime import datetime
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '需要登入'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '需要登入'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': '需要管理員權限'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """獲取所有用戶列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role_filter = request.args.get('role')
    search = request.args.get('search', '').strip()
    
    query = User.query
    
    # 角色篩選
    if role_filter and role_filter in ['student', 'teacher', 'admin']:
        query = query.filter(User.role == role_filter)
    
    # 搜尋功能
    if search:
        query = query.filter(
            db.or_(
                User.username.contains(search),
                User.full_name.contains(search),
                User.email.contains(search),
                User.student_id.contains(search) if hasattr(User, 'student_id') else False
            )
        )
    
    # 分頁
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    users_data = []
    for user in users.items:
        user_dict = user.to_dict()
        
        # 添加統計資訊
        if user.role == 'student':
            # 學生統計
            enrollments = CourseEnrollment.query.filter_by(student_id=user.id, is_active=True).count()
            records = AttendanceRecord.query.filter_by(student_id=user.id).count()
            user_dict['stats'] = {
                'enrolled_courses': enrollments,
                'attendance_records': records
            }
        elif user.role == 'teacher':
            # 老師統計
            courses = Course.query.filter_by(teacher_id=user.id, is_active=True).count()
            forms = AttendanceForm.query.join(Course).filter(
                Course.teacher_id == user.id,
                AttendanceForm.is_active == True
            ).count()
            user_dict['stats'] = {
                'courses_taught': courses,
                'forms_created': forms
            }
        else:
            user_dict['stats'] = {}
        
        users_data.append(user_dict)
    
    return jsonify({
        'users': users_data,
        'pagination': {
            'page': users.page,
            'pages': users.pages,
            'per_page': users.per_page,
            'total': users.total,
            'has_next': users.has_next,
            'has_prev': users.has_prev
        }
    })

@admin_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_detail(user_id):
    """獲取用戶詳細資訊"""
    user = User.query.get_or_404(user_id)
    user_dict = user.to_dict()
    
    # 添加詳細統計
    if user.role == 'student':
        # 學生詳細統計
        enrollments = db.session.query(CourseEnrollment, Course).join(
            Course, CourseEnrollment.course_id == Course.id
        ).filter(
            CourseEnrollment.student_id == user.id,
            CourseEnrollment.is_active == True
        ).all()
        
        courses_data = []
        for enrollment, course in enrollments:
            # 計算該課程的出席統計
            forms = AttendanceForm.query.filter_by(course_id=course.id, is_active=True).all()
            form_ids = [form.id for form in forms]
            
            records = AttendanceRecord.query.filter(
                AttendanceRecord.form_id.in_(form_ids),
                AttendanceRecord.student_id == user.id
            ).all()
            
            status_count = {'present': 0, 'absent': 0, 'late': 0, 'excused': 0}
            for record in records:
                if record.status in status_count:
                    status_count[record.status] += 1
            
            total_records = len(records)
            attendance_rate = (status_count['present'] / total_records * 100) if total_records > 0 else 0
            
            courses_data.append({
                'course': course.to_dict(),
                'enrolled_at': enrollment.enrolled_at.isoformat(),
                'attendance_stats': {
                    'total_forms': len(forms),
                    'submitted_records': total_records,
                    'attendance_rate': round(attendance_rate, 1),
                    'status_count': status_count
                }
            })
        
        user_dict['enrolled_courses'] = courses_data
        
    elif user.role == 'teacher':
        # 老師詳細統計
        courses = Course.query.filter_by(teacher_id=user.id, is_active=True).all()
        courses_data = []
        
        for course in courses:
            # 學生數量
            student_count = CourseEnrollment.query.filter_by(course_id=course.id, is_active=True).count()
            
            # 表單數量
            form_count = AttendanceForm.query.filter_by(course_id=course.id, is_active=True).count()
            
            # 出席記錄數量
            record_count = db.session.query(AttendanceRecord).join(
                AttendanceForm, AttendanceRecord.form_id == AttendanceForm.id
            ).filter(AttendanceForm.course_id == course.id).count()
            
            courses_data.append({
                'course': course.to_dict(),
                'stats': {
                    'student_count': student_count,
                    'form_count': form_count,
                    'record_count': record_count
                }
            })
        
        user_dict['taught_courses'] = courses_data
    
    return jsonify(user_dict)

@admin_bp.route('/admin/users/<int:user_id>/role', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    """更新用戶角色"""
    user = User.query.get_or_404(user_id)
    current_admin = User.query.get(session['user_id'])
    
    # 防止管理員修改自己的角色
    if user.id == current_admin.id:
        return jsonify({'error': '不能修改自己的角色'}), 400
    
    data = request.get_json()
    new_role = data.get('role')
    
    if new_role not in ['student', 'teacher', 'admin']:
        return jsonify({'error': '無效的角色'}), 400
    
    old_role = user.role
    user.role = new_role
    
    try:
        db.session.commit()
        
        # 記錄角色變更日誌
        print(f"管理員 {current_admin.username} 將用戶 {user.username} 的角色從 {old_role} 更改為 {new_role}")
        
        return jsonify({
            'message': f'用戶角色已從 {old_role} 更改為 {new_role}',
            'user': user.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新角色失敗'}), 500

@admin_bp.route('/admin/users/<int:user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(user_id):
    """更新用戶狀態（啟用/停用）"""
    user = User.query.get_or_404(user_id)
    current_admin = User.query.get(session['user_id'])
    
    # 防止管理員停用自己
    if user.id == current_admin.id:
        return jsonify({'error': '不能停用自己的帳號'}), 400
    
    data = request.get_json()
    is_active = data.get('is_active', True)
    
    user.is_active = is_active
    
    try:
        db.session.commit()
        
        status_text = '啟用' if is_active else '停用'
        print(f"管理員 {current_admin.username} {status_text}了用戶 {user.username}")
        
        return jsonify({
            'message': f'用戶已{status_text}',
            'user': user.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '更新狀態失敗'}), 500

@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """刪除用戶（軟刪除）"""
    user = User.query.get_or_404(user_id)
    current_admin = User.query.get(session['user_id'])
    
    # 防止管理員刪除自己
    if user.id == current_admin.id:
        return jsonify({'error': '不能刪除自己的帳號'}), 400
    
    # 軟刪除：設為不活躍
    user.is_active = False
    
    try:
        db.session.commit()
        
        print(f"管理員 {current_admin.username} 刪除了用戶 {user.username}")
        
        return jsonify({'message': '用戶已刪除'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '刪除用戶失敗'}), 500

@admin_bp.route('/admin/stats/overview', methods=['GET'])
@admin_required
def get_admin_overview():
    """獲取管理員總覽統計"""
    # 基本統計
    total_users = User.query.filter_by(is_active=True).count()
    total_students = User.query.filter_by(role='student', is_active=True).count()
    total_teachers = User.query.filter_by(role='teacher', is_active=True).count()
    total_admins = User.query.filter_by(role='admin', is_active=True).count()
    
    total_courses = Course.query.filter_by(is_active=True).count()
    total_forms = AttendanceForm.query.filter_by(is_active=True).count()
    total_records = AttendanceRecord.query.count()
    total_enrollments = CourseEnrollment.query.filter_by(is_active=True).count()
    
    # 最近註冊用戶（30天內）
    from datetime import timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_users = User.query.filter(User.created_at >= thirty_days_ago).count()
    
    # 活躍統計（最近7天有活動的用戶）
    seven_days_ago = datetime.now() - timedelta(days=7)
    active_students = db.session.query(User.id).join(
        AttendanceRecord, User.id == AttendanceRecord.student_id
    ).filter(
        User.role == 'student',
        AttendanceRecord.submitted_at >= seven_days_ago
    ).distinct().count()
    
    active_teachers = db.session.query(User.id).join(
        Course, User.id == Course.teacher_id
    ).join(
        AttendanceForm, Course.id == AttendanceForm.course_id
    ).filter(
        User.role == 'teacher',
        AttendanceForm.created_at >= seven_days_ago
    ).distinct().count()
    
    # 角色分布
    role_distribution = db.session.query(
        User.role,
        func.count(User.id)
    ).filter(User.is_active == True).group_by(User.role).all()
    
    role_stats = {role: count for role, count in role_distribution}
    
    # 每月新增用戶統計
    monthly_users = db.session.query(
        func.strftime('%Y-%m', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= datetime.now() - timedelta(days=365))\
     .group_by(func.strftime('%Y-%m', User.created_at))\
     .order_by('month').all()
    
    monthly_data = [{'month': month, 'count': count} for month, count in monthly_users]
    
    return jsonify({
        'basic_stats': {
            'total_users': total_users,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_admins': total_admins,
            'total_courses': total_courses,
            'total_forms': total_forms,
            'total_records': total_records,
            'total_enrollments': total_enrollments,
            'recent_users': recent_users
        },
        'activity_stats': {
            'active_students': active_students,
            'active_teachers': active_teachers
        },
        'role_distribution': role_stats,
        'monthly_users': monthly_data
    })

@admin_bp.route('/admin/users/bulk-action', methods=['POST'])
@admin_required
def bulk_user_action():
    """批量用戶操作"""
    data = request.get_json()
    user_ids = data.get('user_ids', [])
    action = data.get('action')
    
    if not user_ids or not action:
        return jsonify({'error': '缺少必要參數'}), 400
    
    current_admin = User.query.get(session['user_id'])
    
    # 防止操作自己
    if current_admin.id in user_ids:
        return jsonify({'error': '不能對自己執行批量操作'}), 400
    
    users = User.query.filter(User.id.in_(user_ids)).all()
    
    if not users:
        return jsonify({'error': '找不到指定的用戶'}), 404
    
    try:
        success_count = 0
        
        if action == 'activate':
            for user in users:
                user.is_active = True
                success_count += 1
        
        elif action == 'deactivate':
            for user in users:
                user.is_active = False
                success_count += 1
        
        elif action == 'delete':
            for user in users:
                user.is_active = False  # 軟刪除
                success_count += 1
        
        elif action == 'change_role':
            new_role = data.get('new_role')
            if new_role not in ['student', 'teacher', 'admin']:
                return jsonify({'error': '無效的角色'}), 400
            
            for user in users:
                user.role = new_role
                success_count += 1
        
        else:
            return jsonify({'error': '無效的操作'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'成功處理 {success_count} 個用戶',
            'success_count': success_count
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '批量操作失敗'}), 500

