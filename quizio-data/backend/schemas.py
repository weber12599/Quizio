from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# Base properties shared across models
class StudentBase(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None
    admission_year: Optional[int] = None
    class_name: Optional[str] = None


# Properties required for creation
class StudentCreate(StudentBase):
    password: str


# Properties allowed for updates (all optional)
class StudentUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    admission_year: Optional[int] = None
    class_name: Optional[str] = None


# Properties returned to the client
class StudentOut(StudentBase):
    id: int

    # Enable ORM mode for Pydantic V2
    model_config = ConfigDict(from_attributes=True)


# Schema for student login verification
class StudentLogin(BaseModel):
    student_id: str
    password: str


# Base properties shared across models
class QuestionBase(BaseModel):
    type: Literal['single', 'boolean', 'multiple', 'short', 'essay']
    content: str
    options: Optional[List[str]] = None
    reference_answer: Any
    difficulty: Optional[int] = Field(
        default=None, ge=1, le=3, description='Difficulty level: 1 to 3'
    )
    lesson: Optional[str] = None
    literacy_tags: Optional[List[str]] = None


# Properties required for creation
class QuestionCreate(QuestionBase):
    pass


# Properties allowed for updates (all optional)
class QuestionUpdate(BaseModel):
    type: Optional[Literal['single', 'boolean', 'multiple', 'short', 'essay']] = None
    content: Optional[str] = None
    options: Optional[List[str]] = None
    reference_answer: Optional[Any] = None
    difficulty: Optional[int] = Field(
        default=None, ge=1, le=3, description='Difficulty level: 1 to 3'
    )
    lesson: Optional[str] = None
    literacy_tags: Optional[List[str]] = None


# Properties returned to the client
class QuestionOut(QuestionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
