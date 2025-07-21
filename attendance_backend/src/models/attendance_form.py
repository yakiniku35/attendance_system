from src.models.user import db
from datetime import datetime
import secrets
import string

class AttendanceForm(db.Model):
    __tablename__ = 'attendance_forms'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    form_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 地理位置驗證相關欄位
    location_required = db.Column(db.Boolean, default=False)  # 是否需要位置驗證
    allowed_latitude = db.Column(db.Float)  # 允許的緯度
    allowed_longitude = db.Column(db.Float)  # 允許的經度
    location_radius = db.Column(db.Integer, default=100)  # 允許的範圍（公尺）
    location_name = db.Column(db.String(200))  # 位置名稱
    
    # 關聯
    course = db.relationship('Course', backref=db.backref('attendance_forms', lazy=True))
    
    def __init__(self, course_id, title, form_date, description=None, start_time=None, end_time=None,
                 location_required=False, allowed_latitude=None, allowed_longitude=None, 
                 location_radius=100, location_name=None):
        self.course_id = course_id
        self.title = title
        self.description = description
        self.form_date = form_date
        self.start_time = start_time
        self.end_time = end_time
        self.location_required = location_required
        self.allowed_latitude = allowed_latitude
        self.allowed_longitude = allowed_longitude
        self.location_radius = location_radius
        self.location_name = location_name
    
    def is_location_valid(self, user_latitude, user_longitude):
        """檢查用戶位置是否在允許範圍內"""
        if not self.location_required:
            return True, "不需要位置驗證"
        
        if not self.allowed_latitude or not self.allowed_longitude:
            return True, "表單未設置位置限制"
        
        if not user_latitude or not user_longitude:
            return False, "請提供您的位置資訊"
        
        # 計算距離（使用Haversine公式）
        import math
        
        # 轉換為弧度
        lat1 = math.radians(self.allowed_latitude)
        lon1 = math.radians(self.allowed_longitude)
        lat2 = math.radians(user_latitude)
        lon2 = math.radians(user_longitude)
        
        # Haversine公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半徑（公尺）
        r = 6371000
        distance = c * r
        
        if distance <= self.location_radius:
            return True, f"位置驗證成功（距離: {int(distance)}公尺）"
        else:
            return False, f"您不在允許的範圍內（距離: {int(distance)}公尺，允許範圍: {self.location_radius}公尺）"
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'form_date': self.form_date.isoformat() if self.form_date else None,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'location_required': self.location_required,
            'allowed_latitude': self.allowed_latitude,
            'allowed_longitude': self.allowed_longitude,
            'location_radius': self.location_radius,
            'location_name': self.location_name
        }