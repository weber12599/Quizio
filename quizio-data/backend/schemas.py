from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentLogin(BaseModel):
    student_id: str
    password: str


class StudentBase(BaseModel):
    student_id: str
    name: str
    password: str
    email: Optional[EmailStr] = None
    admission_year: Optional[int] = None
    class_name: Optional[str] = None
    teacher_id: Optional[int] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    admission_year: Optional[int] = None
    class_name: Optional[str] = None


class Student(StudentBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    type: str
    difficulty: Optional[int] = 1
    lesson: Optional[str] = None
    content: str
    options: Optional[Any] = None
    reference_answer: Any
    literacy_tags: Optional[List[str]] = None
    is_archived: bool = False
    owner_id: Optional[int] = None
    is_public: bool = False


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    type: Optional[str] = None
    difficulty: Optional[int] = None
    lesson: Optional[str] = None
    content: Optional[str] = None
    options: Optional[Any] = None
    reference_answer: Optional[Any] = None
    literacy_tags: Optional[List[str]] = None
    is_archived: Optional[bool] = None
    is_public: Optional[bool] = None


class Question(QuestionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserWithDetails(UserResponse):
    students: List[Student] = []
    questions: List[Question] = []
