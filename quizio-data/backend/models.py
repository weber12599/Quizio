from database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    students = relationship('Student', back_populates='teacher')
    questions = relationship('Question', back_populates='owner')


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    admission_year = Column(Integer, nullable=True)
    class_name = Column(String(50), nullable=True)

    teacher_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    teacher = relationship('User', back_populates='students')


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    reference_answer = Column(JSON, nullable=False)
    difficulty = Column(Integer, nullable=True, index=True)
    lesson = Column(String(100), nullable=True, index=True)
    literacy_tags = Column(JSON, nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    is_public = Column(Boolean, default=False, server_default='false', nullable=False)

    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    owner = relationship('User', back_populates='questions')
