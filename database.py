from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import select

from sqlalchemy.orm import (
    sessionmaker, 
    validates,
    relationship,
    backref
    )

import json
import secrets
import random
import os
import dateutil.parser as date_parser
from datetime import datetime

from task import Task


DB_URI = "sqlite:///tasks_db____.db"
# DB_URI = os.environ['DB_URI']

Base = declarative_base()


def convert_str_to_datetime(date_str):
    return date_parser.parse(date_str)


class Task(Base):
    __tablename__ = 'task'

    id = Column(Integer, primary_key=True)
    task_id = Column(String)
    key = Column(String, unique=True)
    status = Column(String, default=Task.PENDING)
    message = Column(String)

    # Lazy=True -> https://docs.sqlalchemy.org/en/20/orm/relationship_api.html#sqlalchemy.orm.relationship.params.lazy
    # cascade="all, delete-orphan" -> delete all related data when task is deleted
    course_score = relationship("CourseScore", backref="task", cascade="all,delete", lazy=True)
    student_profile = relationship("StudentProfile", backref="task", cascade="all,delete", lazy=True, uselist=False)
    attendance = relationship("Attendance", backref="task", cascade="all,delete", lazy=True)

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
    task_id = Column(String, ForeignKey('task.task_id'), nullable=False)
    course_id = Column(String)
    course_name = Column(String)
    credit_hours = Column(String)
    teacher = Column(String)
    section_title = Column(String)
    title = Column(String)
    marks = Column(String)
    total_marks = Column(String)
    datetime = Column(DateTime)

    def to_dict(self):
        return {
            'course_id': self.course_id,
            'course_name': self.course_name,
            'credit_hours': self.credit_hours,
            'teacher': self.teacher,
            'section_title': self.section_title,
            'title': self.title,
            'marks': self.marks,
            'total_marks': self.total_marks,
            'datetime': datetime.strftime(self.datetime, "%d-%m-%Y")
        }

    @validates('datetime')
    def validate_datetime(self, key, datetime):
        return convert_str_to_datetime(datetime)

    def __repr__(self):
        return '<CourseScore %r>' % self.course_id


class StudentProfile(Base):
    __tablename__ = 'student_profile'

    id = Column(Integer, primary_key=True)
    task_id = Column(String, ForeignKey('task.task_id'), nullable=False)
    name = Column(String)
    registration_number = Column(String)

    def to_dict(self):
        return {
            'studentName': self.name,
            'registrationNumber': self.registration_number
        }

    def __repr__(self):
        return '<StudentProfile %r>' % self.name


class Attendance(Base):
    __tablename__ = 'attendance'

    id = Column(Integer, primary_key=True)
    task_id = Column(String, ForeignKey('task.task_id'), nullable=False)
    course_id = Column(String)
    attendance_type = Column(String)
    topic = Column(String)
    attended = Column(Boolean)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    @validates('start_time')
    def validate_start_time(self, key, start_time):
        return convert_str_to_datetime(start_time)

    @validates('end_time')
    def validate_end_time(self, key, end_time):
        return convert_str_to_datetime(end_time)

    def to_dict(self):
        return {
            'course_id': self.course_id,
            'attendance_type': self.attendance_type,
            'topic': self.topic,
            'attended': self.attended,
            'start_time': datetime.strftime(self.start_time, "%d-%m-%Y %I:%M %p"),
            'end_time': datetime.strftime(self.end_time, "%d-%m-%Y %I:%M %p")
        }

    def __repr__(self):
        return '<Attendance %r>' % self.course_id


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

    def delete_task(self, task_id):
        if task := self.session.scalars(select(Task).filter_by(task_id=task_id)).first():
            self.session.delete(task)
            self.session.commit()

    def get_task(self, task_id):
        return self.session.query(Task).filter_by(task_id=task_id).first()

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

    def add_attendance_data(self, task_id, data):
        data = [data] if not isinstance(data, list) else data
        for item in data:
            attendance = Attendance(task_id=task_id, **item)
            self.session.add(attendance)
        self.session.commit()

    def add_student_profile_data(self, task_id, data):
        profile_data = StudentProfile(task_id=task_id, **data)
        self.session.add(profile_data)
        self.session.commit()
