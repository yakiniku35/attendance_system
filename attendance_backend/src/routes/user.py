from flask import Blueprint, jsonify, request, session
from src.models.user import User, db
from functools import wraps

user_bp = Blueprint('user', __name__)

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

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    
    # 檢查必要欄位
    required_fields = ['username', 'email', 'password', 'full_name', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必要欄位: {field}'}), 400
    
    # 檢查用戶名和信箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用戶名已存在'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '信箱已存在'}), 400
    
    # 如果是學生，檢查學號
    if data['role'] == 'student':
        if 'student_id' not in data:
            return jsonify({'error': '學生需要提供學號'}), 400
        if User.query.filter_by(student_id=data['student_id']).first():
            return jsonify({'error': '學號已存在'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data['role'],
        full_name=data['full_name'],
        student_id=data.get('student_id')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    
    if 'username' not in data or 'password' not in data:
        return jsonify({'error': '需要用戶名和密碼'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        session['user_id'] = user.id
        session['user_role'] = user.role
        return jsonify({
            'message': '登入成功',
            'user': user.to_dict()
        })
    else:
        return jsonify({'error': '用戶名或密碼錯誤'}), 401

@user_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'message': '登出成功'})

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict())

@user_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    data = request.json
    
    # 檢查必要欄位
    required_fields = ['username', 'email', 'password', 'full_name', 'role']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必要欄位: {field}'}), 400
    
    # 檢查用戶名和信箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用戶名已存在'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': '信箱已存在'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        role=data['role'],
        full_name=data['full_name'],
        student_id=data.get('student_id')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    # 只有管理員或用戶本人可以查看
    current_user = User.query.get(session['user_id'])
    if current_user.role != 'admin' and current_user.id != user_id:
        return jsonify({'error': '權限不足'}), 403
    
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.full_name = data.get('full_name', user.full_name)
    user.role = data.get('role', user.role)
    user.student_id = data.get('student_id', user.student_id)
    
    if 'password' in data:
        user.set_password(data['password'])
    
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
