from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import nh3
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


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
    record_at: Optional[datetime] = None
    student_id: Optional[int] = None
    guest_name: Optional[str] = None


class StudentSubmissionCreate(StudentSubmissionBase):
    answers: List[StudentAnswerCreate] = []


class StudentSubmission(StudentSubmissionBase):
    id: int
    created_at: datetime
    discussion_score: Optional[int] = None
    session_id: Optional[str] = None
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


# ==========================================
# Interaction Schemas (write — batch from quizio-game)
# ==========================================


class InteractionAuthor(BaseModel):
    student_id: Optional[int] = None
    guest_name: Optional[str] = None
    is_host: bool = False

    @model_validator(mode='after')
    def validate_exactly_one(self) -> 'InteractionAuthor':
        count = sum([
            self.student_id is not None,
            bool(self.guest_name),
            self.is_host,
        ])
        if count != 1:
            raise ValueError('Exactly one of student_id, guest_name, or is_host must be set')
        return self


class CommentLikeCreate(BaseModel):
    author: InteractionAuthor


class CommentCreate(BaseModel):
    content: str
    author: InteractionAuthor
    comment_likes: List[CommentLikeCreate] = []

    @field_validator('content')
    @classmethod
    def sanitize_comment(cls, v: str) -> str:
        return nh3.clean(v, tags=set(), attributes={})


class AnswerInteractionCreate(BaseModel):
    answer_id: int
    answer_likes: List[InteractionAuthor] = []
    comments: List[CommentCreate] = []


class OptionInteractionCreate(BaseModel):
    question_id: int
    option_index: int
    option_likes: List[InteractionAuthor] = []
    comments: List[CommentCreate] = []


class InteractionBatchPayload(BaseModel):
    # All option-level interactions in the batch share the same session
    # (since end_game flushes one session at a time). Use any submission_id
    # from the session as the anchor.
    session_anchor_submission_id: Optional[int] = None
    answer_interactions: List[AnswerInteractionCreate] = []
    option_interactions: List[OptionInteractionCreate] = []


# ==========================================
# Interaction Schemas (read — for quizio-data frontend)
# ==========================================


class InteractionLikeRead(BaseModel):
    id: int
    author: Dict[str, Any]


class InteractionCommentRead(BaseModel):
    id: int
    content: str
    author: Dict[str, Any]
    created_at: datetime
    comment_likes: List[InteractionLikeRead] = []


class AnswerInteractionRead(BaseModel):
    answer_id: int
    submission_id: int
    answer_content: Optional[str]
    author: Dict[str, Any]
    answer_likes: List[InteractionLikeRead] = []
    comments: List[InteractionCommentRead] = []


class OptionInteractionRead(BaseModel):
    option_index: int
    option_text: str
    option_likes: List[InteractionLikeRead] = []
    comments: List[InteractionCommentRead] = []


class QuestionInteractionRead(BaseModel):
    question_id: int
    question_title: str
    question_type: str
    question_options: Optional[List[str]] = None
    answers: List[AnswerInteractionRead] = []
    options: List[OptionInteractionRead] = []


# ==========================================
# Batch Submission Response (extended)
# ==========================================


class AnswerIdMapping(BaseModel):
    student_id: Optional[int] = None
    guest_name: Optional[str] = None
    question_id: int
    answer_id: int
    submission_id: int


class BatchSubmissionResponse(BaseModel):
    status: str
    processed_count: int
    answer_ids: List[AnswerIdMapping] = []


# ==========================================
# Discussion Score
# ==========================================


class DiscussionScoreUpdate(BaseModel):
    score: Optional[int] = None
