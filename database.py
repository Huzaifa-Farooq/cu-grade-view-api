from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import json
import secrets
import random

from task import Task


DB_URI = "sqlite:///tasks_db____.db"

Base = declarative_base()


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    task_id = Column(String)
    key = Column(String, unique=True)
    status = Column(String, default=Task.PENDING)
    message = Column(String)

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'status': self.status,
            'message': self.message
        }

    def __repr__(self):
        return '<Task %r>' % self.task_id


class CourseScore(Base):
    __tablename__ = 'course_score'

    id = Column(Integer, primary_key=True)
    task_id = Column(String)
    course_id = Column(String)
    course_name = Column(String)
    credit_hours = Column(String)
    teacher = Column(String)
    section_title = Column(String)
    title = Column(String)
    marks = Column(String)
    total_marks = Column(String)
    datetime = Column(String)

    def to_dict(self):
        return {
            'task_id': self.task_id,
            'course_id': self.course_id,
            'course_name': self.course_name,
            'credit_hours': self.credit_hours,
            'teacher': self.teacher,
            'section_title': self.section_title,
            'title': self.title,
            'marks': self.marks,
            'total_marks': self.total_marks,
            'datetime': self.datetime
        }


class StudentProfile(Base):
    __tablename__ = 'student_profile'

    id = Column(Integer, primary_key=True)
    task_id = Column(String)
    name = Column(String)
    registration_number = Column(String)

    def to_dict(self):
        return {
            'studentName': self.name,
            'registrationNumber': self.registration_number
        }


class DataBase:
    def __init__(self, db_uri=DB_URI):
        engine = create_engine(db_uri, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def create_task(self, task_id):
        if self.get_task(task_id) is not None:
            return

        existing_keys = [task.key for task in self.session.query(Task).all()]
        n_chars = random.randint(8, 16)
        key = secrets.token_urlsafe(n_chars)
        while key in existing_keys:
            key = secrets.token_urlsafe(n_chars)

        task = Task(task_id=task_id, key=key)
        self.session.add(task)
        self.session.commit()
        return key

    def clean_task_data(self, task_id):
        self.session.query(CourseScore).filter_by(task_id=task_id).delete()
        self.session.query(StudentProfile).filter_by(task_id=task_id).delete()
        self.session.commit()

    def delete_task(self, task_id):
        self.clean_task_data(task_id)
        self.session.query(Task).filter_by(task_id=task_id).delete()
        self.session.commit()

    def get_task(self, task_id):
        return self.session.query(Task).filter_by(task_id=task_id).first()

    def get_task_course_score_data(self, task_id):
        return self.session.query(CourseScore).filter_by(task_id=task_id)

    def get_student_profile_data(self, task_id):
        data = self.session.query(StudentProfile).filter_by(task_id=task_id).first()
        return data.to_dict() if data else None

    def update_task_status(self, task_id, status, message=''):
        task = self.session.query(Task).filter_by(task_id=task_id).first()
        task.status = status
        task.message = message
        self.session.commit()

    def add_course_score_data(self, task_id, data):
        data = [data] if not isinstance(data, list) else data
        for item in data:
            score_data = CourseScore(task_id=task_id, **item)
            self.session.add(score_data)
        self.session.commit()

    def add_student_profile_data(self, task_id, data):
        profile_data = StudentProfile(task_id=task_id, **data)
        self.session.add(profile_data)
        self.session.commit()
