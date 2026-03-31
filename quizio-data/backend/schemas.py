from typing import Optional

from pydantic import BaseModel, ConfigDict


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
