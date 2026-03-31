from database import Base
from sqlalchemy import JSON, Column, Integer, String, Text


# Define the Student ORM model
class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    admission_year = Column(Integer, nullable=True)
    class_name = Column(String(50), nullable=True)


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
