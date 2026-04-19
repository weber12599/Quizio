from datetime import date, datetime
from typing import Dict, List, Optional, Union

import nh3
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def sanitize_rich_text(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    Allows safe formatting tags and images.
    """
    if not html_content:
        return html_content

    allowed_tags = {
        'p',
        'b',
        'i',
        'u',
        'strong',
        'em',
        'br',
        'ul',
        'ol',
        'li',
        'img',
        'h1',
        'h2',
        'h3',
        'blockquote',
        'code',
        'pre',
        's',
    }
    allowed_attributes = {
        'img': {'src', 'alt', 'title', 'width', 'height'},
        'code': {'class'},
    }
    return nh3.clean(html_content, tags=allowed_tags, attributes=allowed_attributes)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GuestLogin(BaseModel):
    guest_name: str = Field(..., min_length=1, max_length=50)


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


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    admission_year: Optional[int] = None
    class_name: Optional[str] = None


class StudentResponse(StudentBase):
    id: int
    teacher_id: int
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    type: str
    difficulty: Optional[int] = 1
    lesson: Optional[str] = None
    content: str
    options: Optional[List[str]] = None
    reference_answer: Union[bool, int, str, List[int]]
    literacy_tags: Optional[List[str]] = None
    is_public: bool = False
    is_locked: bool = False
    is_archived: bool = False
    needs_manual_grading: bool = False

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return sanitize_rich_text(v)


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    type: Optional[str] = None
    difficulty: Optional[int] = None
    lesson: Optional[str] = None
    content: Optional[str] = None
    options: Optional[List[str]] = None
    reference_answer: Optional[Union[bool, int, str, List[int]]] = None
    literacy_tags: Optional[List[str]] = None
    is_archived: Optional[bool] = None
    is_public: Optional[bool] = None
    needs_manual_grading: Optional[bool] = None

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return sanitize_rich_text(v)
        return v


class QuestionResponse(QuestionBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ExamQuestionSetup(BaseModel):
    question_id: int
    score: int = 10


class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    target_date: Optional[date] = None


class ExamCreate(ExamBase):
    questions: List[ExamQuestionSetup] = []


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[date] = None
    questions: Optional[List[ExamQuestionSetup]] = None


class ExamQuestionResponse(BaseModel):
    exam_id: int
    question_id: int
    sort_order: int
    score: int
    question: QuestionResponse

    model_config = ConfigDict(from_attributes=True)


class ExamResponse(ExamBase):
    id: int
    owner_id: int
    is_locked: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    exam_questions: List[ExamQuestionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class UserWithDetails(UserResponse):
    students: List[StudentResponse] = []
    questions: List[QuestionResponse] = []
    exams: List[ExamResponse] = []


class StudentAnswerBase(BaseModel):
    question_id: int
    answer_content: Optional[str] = None
    is_correct: Optional[bool] = None
    score: Optional[int] = None

    @field_validator('answer_content')
    @classmethod
    def sanitize_student_answer(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return sanitize_rich_text(v)
        return v


class StudentAnswerCreate(StudentAnswerBase):
    pass


class StudentAnswer(StudentAnswerBase):
    id: int
    submission_id: int
    exam_id: int
    created_at: datetime
    question: Optional[QuestionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class StudentSubmissionBase(BaseModel):
    exam_id: int
    record_at: datetime
    student_id: Optional[int] = None
    guest_name: Optional[str] = None


class StudentSubmissionCreate(StudentSubmissionBase):
    answers: List[StudentAnswerCreate] = []


class StudentSubmission(StudentSubmissionBase):
    id: int
    created_at: datetime
    answers: List[StudentAnswer] = []

    model_config = ConfigDict(from_attributes=True)


class SubmissionScoreDetail(BaseModel):
    submission_id: int
    score: int
    record_at: datetime


class ExamGradeHeader(BaseModel):
    id: int
    title: str
    target_date: Optional[date]
    max_attempts: int = 1

    model_config = ConfigDict(from_attributes=True)


class StudentGradeEntry(BaseModel):
    student_db_id: Optional[int]
    student_id: str
    name: str
    class_name: Optional[str]
    exam_submissions: Dict[str, List[SubmissionScoreDetail]]


class GradeReportResponse(BaseModel):
    exams: List[ExamGradeHeader]
    students: List[StudentGradeEntry]


class AnswerGradingHistoryResponse(BaseModel):
    id: int
    answer_id: int
    old_score: Optional[int] = None
    new_score: Optional[int] = None
    teacher_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
