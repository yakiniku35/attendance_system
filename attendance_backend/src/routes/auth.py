from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from src.models.password_reset import PasswordReset, EmailVerification
from src.utils.email_service import email_service
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import re
from flask import Response
from typing import Any

auth_bp = Blueprint('auth', __name__)

def validate_email(email: str) -> bool:
    """驗證郵件格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """驗證密碼強度"""
    if len(password) < 6:
        return False, "密碼長度至少6個字符"
    return True, ""

@auth_bp.route('/auth/register', methods=['POST'])
def register() -> tuple:
    """用戶註冊 API，回傳 JSON 與狀態碼"""
    data = request.get_json()
    
    # 驗證必要欄位
    required_fields = ['username', 'email', 'full_name', 'password', 'role']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'缺少必要欄位: {field}'}), 400
    
    username = data['username'].strip()
    email = data['email'].strip().lower()
    full_name = data['full_name'].strip()
    password = data['password']
    role = data['role']
    student_id = data.get('student_id', '').strip()
    
    # 驗證角色
    if role not in ['student', 'teacher']:
        return jsonify({'error': '註冊時只能選擇學生或老師角色'}), 400
    
    # 驗證郵件格式
    if not validate_email(email):
        return jsonify({'error': '郵件格式不正確'}), 400
    
    # 驗證密碼強度
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 檢查用戶名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用戶名已存在'}), 400
    
    # 檢查郵件是否已存在
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '郵件地址已被註冊'}), 400
    
    # 如果是學生，檢查學號是否已存在
    if role == 'student' and student_id:
        if User.query.filter_by(student_id=student_id).first():
            return jsonify({'error': '學號已存在'}), 400
    
    try:
        # 創建新用戶
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            student_id=student_id if role == 'student' else None
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # 獲取用戶ID
        
        # 創建郵件驗證記錄
        verification = EmailVerification(user.id, 'registration')
        db.session.add(verification)
        
        db.session.commit()
        
        # 發送歡迎郵件
        try:
            success, message = email_service.send_registration_welcome(
                email, full_name, verification.token
            )
            if not success:
                print(f"歡迎郵件發送失敗: {message}")
        except Exception as e:
            print(f"發送歡迎郵件時出錯: {str(e)}")
        
        return jsonify({
            'message': '註冊成功！歡迎郵件已發送到您的郵箱',
            'user': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"註冊失敗: {str(e)}")
        return jsonify({'error': '註冊失敗，請稍後再試'}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login() -> Response:
    """用戶登入 API，回傳 JSON 與狀態碼"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        response = jsonify({'error': '請輸入用戶名和密碼'})
        response.status_code = 400
        return response

    username = data['username'].strip()
    password = data['password']

    user = User.query.filter(
        db.or_(User.username == username, User.email == username)
    ).first()
    if not user:
        response = jsonify({'error': '用戶不存在'})
        response.status_code = 401
        return response
    if not user.is_active:
        response = jsonify({'error': '帳號已被停用，請聯繫管理員'})
        response.status_code = 401
        return response
    if not user.check_password(password):
        response = jsonify({'error': '密碼錯誤'})
        response.status_code = 401
        return response
        return jsonify({'error': '密碼錯誤'}), 401
    
    # 設置session
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    
    # 更新最後登入時間
    user.last_login = db.func.now()
    db.session.commit()
    
    return jsonify({
        'message': '登入成功',
        'user': user.to_dict()
    })

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """用戶登出"""
    session.clear()
    return jsonify({'message': '登出成功'})

@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """忘記密碼 - 發送重置郵件"""
    data = request.get_json()
    
    if not data.get('email'):
        return jsonify({'error': '請輸入郵件地址'}), 400
    
    email = data['email'].strip().lower()
    
    if not validate_email(email):
        return jsonify({'error': '郵件格式不正確'}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # 為了安全，不透露用戶是否存在
        return jsonify({'message': '如果該郵件地址已註冊，您將收到密碼重置郵件'}), 200
    
    if not user.is_active:
        return jsonify({'error': '帳號已被停用，請聯繫管理員'}), 400
    
    try:
        # 使之前的重置請求失效
        PasswordReset.query.filter_by(user_id=user.id, is_used=False).update({'is_used': True})
        
        # 創建新的密碼重置請求
        reset_request = PasswordReset(user.id)
        db.session.add(reset_request)
        db.session.commit()
        
        # 發送重置郵件
        success, message = email_service.send_password_reset(
            user.email, user.full_name, reset_request.otp_code, reset_request.token
        )
        
        if success:
            return jsonify({
                'message': '密碼重置郵件已發送，請檢查您的郵箱',
                'reset_token': reset_request.token  # 前端需要這個token
            }), 200
        else:
            return jsonify({'error': '郵件發送失敗，請稍後再試'}), 500
    
    except Exception as e:
        db.session.rollback()
        print(f"密碼重置請求失敗: {str(e)}")
        return jsonify({'error': '系統錯誤，請稍後再試'}), 500

@auth_bp.route('/auth/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    """驗證密碼重置OTP"""
    data = request.get_json()
    
    required_fields = ['reset_token', 'otp_code']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'缺少必要欄位: {field}'}), 400
    
    reset_token = data['reset_token']
    otp_code = data['otp_code'].strip()
    
    # 查找重置請求
    reset_request = PasswordReset.query.filter_by(
        token=reset_token,
        otp_code=otp_code
    ).first()
    
    if not reset_request:
        return jsonify({'error': '無效的重置令牌或驗證碼'}), 400
    
    if not reset_request.is_valid():
        return jsonify({'error': '驗證碼已過期或已使用，請重新申請'}), 400
    
    return jsonify({
        'message': 'OTP驗證成功，請設置新密碼',
        'verified': True
    })

@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password() -> tuple:
    """重置密碼 API，回傳 JSON 與狀態碼"""
    data = request.get_json()
    
    required_fields = ['reset_token', 'otp_code', 'new_password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'缺少必要欄位: {field}'}), 400
    
    reset_token = data['reset_token']
    otp_code = data['otp_code'].strip()
    new_password = data['new_password']
    
    # 驗證新密碼
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # 查找重置請求
    reset_request = PasswordReset.query.filter_by(
        token=reset_token,
        otp_code=otp_code
    ).first()
    
    if not reset_request:
        return jsonify({'error': '無效的重置令牌或驗證碼'}), 400
    
    if not reset_request.is_valid():
        return jsonify({'error': '驗證碼已過期或已使用，請重新申請'}), 400
    
    try:
        # 更新用戶密碼
        user = reset_request.user
        user.set_password(new_password)
        
        # 標記重置請求為已使用
        reset_request.mark_as_used()
        
        db.session.commit()
        
        return jsonify({'message': '密碼重置成功，請使用新密碼登入'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"密碼重置失敗: {str(e)}")
        return jsonify({'error': '密碼重置失敗，請稍後再試'}), 500

@auth_bp.route('/auth/change-password', methods=['POST'])
def change_password() -> tuple:
    """修改密碼 API，回傳 JSON 與狀態碼"""
    if 'user_id' not in session:
        return jsonify({'error': '需要登入'}), 401
    
    data = request.get_json()
    
    required_fields = ['current_password', 'new_password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'error': f'缺少必要欄位: {field}'}), 400
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    # 驗證新密碼
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    user = User.query.get(session['user_id'])
    
    if not user.check_password(current_password):
        return jsonify({'error': '當前密碼錯誤'}), 400
    
    try:
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': '密碼修改成功'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"密碼修改失敗: {str(e)}")
        return jsonify({'error': '密碼修改失敗，請稍後再試'}), 500

@auth_bp.route('/auth/verify-email', methods=['POST'])
def verify_email():
    """驗證郵件地址"""
    data = request.get_json()
    
    if not data.get('token'):
        return jsonify({'error': '缺少驗證令牌'}), 400
    
    token = data['token']
    
    # 查找驗證記錄
    verification = EmailVerification.query.filter_by(token=token).first()
    
    if not verification:
        return jsonify({'error': '無效的驗證令牌'}), 400
    
    if not verification.is_valid():
        return jsonify({'error': '驗證令牌已過期或已使用'}), 400
    
    try:
        # 標記用戶郵件為已驗證
        user = verification.user
        user.email_verified = True
        
        # 標記驗證為已使用
        verification.mark_as_used()
        
        db.session.commit()
        
        return jsonify({'message': '郵件驗證成功'})
    
    except Exception as e:
        db.session.rollback()
        print(f"郵件驗證失敗: {str(e)}")
        return jsonify({'error': 'Email verification failed, please try again later'}), 500
