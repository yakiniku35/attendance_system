from src.models.user import db
from datetime import datetime

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey('attendance_forms.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # present, absent, late, excused
    notes = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 地理位置記錄
    latitude = db.Column(db.Float)  # 提交時的緯度
    longitude = db.Column(db.Float)  # 提交時的經度
    location_accuracy = db.Column(db.Float)  # 位置精確度（公尺）
    location_verified = db.Column(db.Boolean, default=False)  # 位置是否通過驗證
    location_distance = db.Column(db.Float)  # 與允許位置的距離（公尺）
    
    # 關聯
    form = db.relationship('AttendanceForm', backref=db.backref('attendance_records', lazy=True))
    student = db.relationship('User', backref=db.backref('attendance_records', lazy=True))
    
    def __init__(self, form_id, student_id, status, notes=None, 
                 latitude=None, longitude=None, location_accuracy=None):
        self.form_id = form_id
        self.student_id = student_id
        self.status = status
        self.notes = notes
        self.latitude = latitude
        self.longitude = longitude
        self.location_accuracy = location_accuracy
    
    def verify_location(self):
        """驗證位置並更新驗證狀態"""
        if not self.form.location_required:
            self.location_verified = True
            return True, "不需要位置驗證"
        
        if not self.latitude or not self.longitude:
            self.location_verified = False
            return False, "缺少位置資訊"
        
        is_valid, message = self.form.is_location_valid(self.latitude, self.longitude)
        self.location_verified = is_valid
        
        # 計算距離並記錄
        if self.form.allowed_latitude and self.form.allowed_longitude:
            import math
            
            lat1 = math.radians(self.form.allowed_latitude)
            lon1 = math.radians(self.form.allowed_longitude)
            lat2 = math.radians(self.latitude)
            lon2 = math.radians(self.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            r = 6371000  # 地球半徑（公尺）
            self.location_distance = c * r
        
        return is_valid, message
    
    def to_dict(self):
        return {
            'id': self.id,
            'form_id': self.form_id,
            'student_id': self.student_id,
            'status': self.status,
            'notes': self.notes,
            'submitted_at': self.submitted_at.isoformat(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_accuracy': self.location_accuracy,
            'location_verified': self.location_verified,
            'location_distance': self.location_distance
        }