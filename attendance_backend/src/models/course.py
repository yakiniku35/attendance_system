from src.models.user import db
from datetime import datetime
import random
import string

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=True)
    join_code = db.Column(db.String(10), unique=True, nullable=False)  # 學生加入課程的代碼
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯
    forms = db.relationship('AttendanceForm', backref='course', lazy=True)
    enrollments = db.relationship('CourseEnrollment', backref='course', lazy=True)
    
    def __init__(self, **kwargs):
        super(Course, self).__init__(**kwargs)
        if not self.join_code:
            self.join_code = self.generate_join_code()
    
    @staticmethod
    def generate_join_code():
        """生成6位數的課程加入代碼"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Course.query.filter_by(join_code=code).first():
                return code
    
    def __repr__(self):
        return f'<Course {self.course_code}: {self.course_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_code': self.course_code,
            'course_name': self.course_name,
            'teacher_id': self.teacher_id,
            'description': self.description,
            'join_code': self.join_code,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

