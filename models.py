from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'professor', 'admin'
    
    # Common fields
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Student-specific field
    student_id = db.Column(db.String(20), unique=True, nullable=True)  # Only for students
    
    # Relationship type discriminator
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': role
    }
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        base_dict = {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if self.role == 'student' and self.student_id:
            base_dict['student_id'] = self.student_id
        
        return base_dict

class Student(User):
    __mapper_args__ = {
        'polymorphic_identity': 'student'
    }

class Professor(User):
    __mapper_args__ = {
        'polymorphic_identity': 'professor'
    }

class Admin(User):
    __mapper_args__ = {
        'polymorphic_identity': 'admin'
    }

class Lesson(db.Model):
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # The teacher who created this lesson
    professor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship to sections
    sections = db.relationship('Section', backref='lesson', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'professor_id': self.professor_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sections': [section.to_dict() for section in sorted(self.sections, key=lambda x: x.order_index)]
        }

class Section(db.Model):
    __tablename__ = 'sections'
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    
    title = db.Column(db.String(200), nullable=False)
    body_content = db.Column(db.Text, nullable=False) # Main section text (HTML)
    order_index = db.Column(db.Integer, default=0) # To order sections within a lesson

    def to_dict(self):
        return {
            'id': self.id,
            'lesson_id': self.lesson_id,
            'title': self.title,
            'body_content': self.body_content,
            'order_index': self.order_index
        }

class Exam(db.Model):
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False) # Required association
    professor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='exam', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('ExamSubmission', backref='exam', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_answers=False):
        return {
            'id': self.id,
            'title': self.title,
            'lesson_id': self.lesson_id,
            'professor_id': self.professor_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'questions': [q.to_dict(include_correct=include_answers) for q in sorted(self.questions, key=lambda x: x.order_index)]
        }

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    
    question_text = db.Column(db.Text, nullable=False) # HTML content
    option_a = db.Column(db.Text, nullable=False) # HTML or plain text
    option_b = db.Column(db.Text, nullable=False) # HTML or plain text
    option_c = db.Column(db.Text, nullable=False) # HTML or plain text
    option_d = db.Column(db.Text, nullable=False) # HTML or plain text
    correct_option = db.Column(db.String(1), nullable=False) # 'A', 'B', 'C', or 'D'
    order_index = db.Column(db.Integer, default=0)
    
    def to_dict(self, include_correct=False):
        d = {
            'id': self.id,
            'exam_id': self.exam_id,
            'question_text': self.question_text,
            'option_a': self.option_a,
            'option_b': self.option_b,
            'option_c': self.option_c,
            'option_d': self.option_d,
            'order_index': self.order_index
        }
        if include_correct:
            d['correct_option'] = self.correct_option
        return d

class ExamSubmission(db.Model):
    __tablename__ = 'exam_submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Float, nullable=False) # score out of 100 or fractional
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'student_id': self.student_id,
            'score': self.score,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }


