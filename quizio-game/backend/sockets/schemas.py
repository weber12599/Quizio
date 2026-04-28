from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, field_validator, model_validator
from utils import sanitize_rich_text


# ---------------------------------------------------------
# Join Room Payloads
# ---------------------------------------------------------
class HostJoinRoomPayload(BaseModel):
    room_pin: str
    token: str
    exam_id: int
    target_class: Optional[str] = None
    allow_guests: bool = True
    expected_students: List[str] = []
    host_name: str = '老師'


class ClientJoinRoomPayload(BaseModel):
    room_pin: str
    is_guest: bool = False
    guest_name: Optional[str] = None
    student_id: Optional[str] = None
    password: Optional[str] = None
    player_id: Optional[str] = None

    @model_validator(mode='after')
    def validate_guest_or_student(self) -> 'ClientJoinRoomPayload':
        if self.is_guest:
            if not any(
                isinstance(s, str) and bool(s.strip())
                for s in [self.player_id, self.guest_name]
            ):
                raise ValueError(
                    'player_id or guest_name is required when is_guest is True'
                )

        else:
            if (
                not isinstance(self.student_id, str)
                or not self.student_id.strip()
                or not isinstance(self.password, str)
                or not self.password.strip()
            ):
                raise ValueError(
                    'student_id and password are required when is_guest is False'
                )
        return self


class ScreenJoinRoomPayload(BaseModel):
    room_pin: str


class HostBroadcastQuestionsPayload(BaseModel):
    room_pin: str
    questions: List[Dict[str, Any]]


class HostDisplayQuestionPayload(BaseModel):
    room_pin: str
    question: Optional[Dict[str, Any]] = None
    display_state: str = 'question'


class HostPinAnswerPayload(BaseModel):
    room_pin: str
    question_id: int
    pinned_answer: Optional[Dict[str, Any]] = None


class SubmitAnswerPayload(BaseModel):
    room_pin: str
    question_id: int
    answer: Union[str, int, List[int], None]

    @field_validator('answer')
    @classmethod
    def sanitize_answer(
        cls, v: Union[str, int, List[int], None]
    ) -> Union[str, int, List[int], None]:
        # Apply nh3 sanitization automatically when the payload is parsed
        if isinstance(v, int):
            return v
        elif isinstance(v, str):
            return sanitize_rich_text(v)
        elif isinstance(v, list):
            return [
                sanitize_rich_text(item) if isinstance(item, str) else item
                for item in v
            ]
        return None


class HostShowLeaderboardPayload(BaseModel):
    room_pin: str


class EndGamePayload(BaseModel):
    room_pin: str


# ---------------------------------------------------------
# Interaction Payloads
# ---------------------------------------------------------


class LikeAnswerPayload(BaseModel):
    room_pin: str
    question_id: int
    answer_owner_id: str


class CommentAnswerPayload(BaseModel):
    room_pin: str
    question_id: int
    answer_owner_id: str
    content: str

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return sanitize_rich_text(v)


class DeleteCommentPayload(BaseModel):
    room_pin: str
    question_id: int
    answer_owner_id: str
    comment_id: str


class LikeCommentPayload(BaseModel):
    room_pin: str
    question_id: int
    answer_owner_id: str
    comment_id: str
