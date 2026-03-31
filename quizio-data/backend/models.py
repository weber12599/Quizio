from database import Base
from sqlalchemy import Column, Integer, String


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
