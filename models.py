from app import db
from flask_login import UserMixin
from datetime import datetime, time
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # admin, faculty, student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Faculty specific fields
    designation = db.Column(db.String(50))  # Assistant Prof, Associate Prof, Professor
    department = db.Column(db.String(100))
    employee_id = db.Column(db.String(20), unique=True)
    
    # Relationships
    assignments = db.relationship('Assignment', backref='faculty_member', lazy=True)
    
    def get_workload_limit(self):
        """Get workload limit based on designation"""
        limits = {
            'Assistant Prof': 18,
            'Associate Prof': 16,
            'Professor': 14
        }
        return limits.get(self.designation, 18)
    
    def get_current_workload(self):
        """Calculate current workload from assignments"""
        total = 0
        for assignment in self.assignments:
            total += assignment.lecture_hours + assignment.tutorial_hours + assignment.practical_hours
        return total
    
    def can_assign_workload(self, additional_hours):
        """Check if additional workload can be assigned"""
        return (self.get_current_workload() + additional_hours) <= self.get_workload_limit()
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    lecture_hours = db.Column(db.Integer, default=0)
    tutorial_hours = db.Column(db.Integer, default=0)
    practical_hours = db.Column(db.Integer, default=0)
    subject_type = db.Column(db.String(20), default='Regular')  # Regular, Elective
    semester = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    division = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('Assignment', backref='subject', lazy=True)
    timetable_entries = db.relationship('TimetableEntry', backref='subject', lazy=True)
    
    @property
    def total_hours(self):
        return self.lecture_hours + self.tutorial_hours + self.practical_hours

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    lecture_hours = db.Column(db.Integer, default=0)
    tutorial_hours = db.Column(db.Integer, default=0)
    practical_hours = db.Column(db.Integer, default=0)
    division = db.Column(db.String(10))
    academic_year = db.Column(db.String(10), default='2024-25')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def total_hours(self):
        return self.lecture_hours + self.tutorial_hours + self.practical_hours

class TimetableEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  # Monday, Tuesday, etc.
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    room = db.Column(db.String(20))
    division = db.Column(db.String(10))
    semester = db.Column(db.Integer, nullable=False)
    session_type = db.Column(db.String(20), default='Lecture')  # Lecture, Tutorial, Practical
    academic_year = db.Column(db.String(10), default='2024-25')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    faculty = db.relationship('User', backref='timetable_entries')

class ImportedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    import_date = db.Column(db.DateTime, default=datetime.utcnow)
    data_type = db.Column(db.String(50))  # faculty, subjects, assignments, etc.
    total_rows = db.Column(db.Integer)
    successful_rows = db.Column(db.Integer)
    failed_rows = db.Column(db.Integer)
    mapping_config = db.Column(db.Text)  # JSON string of column mappings
    
class ImportedDataRow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    import_id = db.Column(db.Integer, db.ForeignKey('imported_data.id'), nullable=False)
    row_data = db.Column(db.Text)  # JSON string of row data
    status = db.Column(db.String(20), default='success')  # success, failed
    error_message = db.Column(db.Text)
    
    # Relationship
    import_session = db.relationship('ImportedData', backref='rows')

class AcademicYear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(10), unique=True, nullable=False)  # 2024-25
    is_current = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
