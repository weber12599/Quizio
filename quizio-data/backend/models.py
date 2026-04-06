from database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
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
    exams = relationship('Exam', back_populates='owner', cascade='all, delete-orphan')


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    admission_year = Column(Integer, nullable=True)
    class_name = Column(String(50), nullable=True)
    teacher_id = Column(
        Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )

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
    owner_id = Column(
        Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )

    owner = relationship('User', back_populates='questions')


class Exam(Base):
    __tablename__ = 'exams'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    target_date = Column(Date, nullable=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    owner_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )

    owner = relationship('User', back_populates='exams')
    exam_questions = relationship(
        'ExamQuestion',
        back_populates='exam',
        cascade='all, delete-orphan',
        order_by='ExamQuestion.sort_order',
    )


class ExamQuestion(Base):
    __tablename__ = 'exam_questions'

    sort_order = Column(Integer, default=0, nullable=False)
    exam_id = Column(
        Integer, ForeignKey('exams.id', ondelete='CASCADE'), primary_key=True
    )
    question_id = Column(
        Integer, ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True
    )

    exam = relationship('Exam', back_populates='exam_questions')
    question = relationship('Question')


class Media(Base):
    __tablename__ = 'media'

    id = Column(Integer, primary_key=True, index=True)
    fid = Column(String, unique=True, index=True, nullable=False)
    uploader_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StudentSubmission(Base):
    __tablename__ = 'student_submissions'

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(
        Integer, ForeignKey('exams.id', ondelete='CASCADE'), nullable=False
    )
    student_id = Column(
        Integer, ForeignKey('students.id', ondelete='SET NULL'), nullable=True
    )
    guest_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exam = relationship('Exam')
    student = relationship('Student')
    answers = relationship(
        'StudentAnswer', back_populates='submission', cascade='all, delete-orphan'
    )


class StudentAnswer(Base):
    __tablename__ = 'student_answers'

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey('student_submissions.id', ondelete='CASCADE'),
        nullable=False,
    )
    exam_id = Column(
        Integer, ForeignKey('exams.id', ondelete='CASCADE'), nullable=False
    )
    question_id = Column(
        Integer, ForeignKey('questions.id', ondelete='CASCADE'), nullable=False
    )
    answer_content = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submission = relationship('StudentSubmission', back_populates='answers')
    exam = relationship('Exam')
    question = relationship('Question')
