from src.models.user import db
from datetime import datetime, timedelta
import secrets
import string

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    user = db.relationship('User', backref=db.backref('password_resets', lazy=True))
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.token = self.generate_token()
        self.otp_code = self.generate_otp()
        self.expires_at = datetime.utcnow() + timedelta(minutes=15)  # 15分鐘有效期
    
    @staticmethod
    def generate_token():
        """生成安全的重置令牌"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_otp():
        """生成6位數OTP代碼"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def is_expired(self):
        """檢查是否已過期"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """檢查是否有效（未使用且未過期）"""
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        """標記為已使用"""
        self.is_used = True
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': self.expires_at.isoformat(),
            'is_used': self.is_used,
            'created_at': self.created_at.isoformat()
        }

class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    verification_type = db.Column(db.String(20), nullable=False)  # 'registration', 'email_change'
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    user = db.relationship('User', backref=db.backref('email_verifications', lazy=True))
    
    def __init__(self, user_id, verification_type='registration'):
        self.user_id = user_id
        self.verification_type = verification_type
        self.token = self.generate_token()
        self.expires_at = datetime.utcnow() + timedelta(hours=24)  # 24小時有效期
    
    @staticmethod
    def generate_token():
        """生成安全的驗證令牌"""
        return secrets.token_urlsafe(32)
    
    def is_expired(self):
        """檢查是否已過期"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """檢查是否有效（未使用且未過期）"""
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        """標記為已使用"""
        self.is_used = True
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'verification_type': self.verification_type,
            'expires_at': self.expires_at.isoformat(),
            'is_used': self.is_used,
            'created_at': self.created_at.isoformat()
        }

