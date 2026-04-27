from database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_mixin, declared_attr, relationship, validates
from sqlalchemy.sql import func

# ==========================================
# Mixins
# ==========================================


@declarative_mixin
class SoftDeleteMixin:
    """
    Provides a common deleted_at column for soft-deletion across all models.
    When a record is "deleted" via the application, this timestamp is set instead of physically removing the row.
    """

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)


@declarative_mixin
class InteractiveMixin:
    """
    Provides polymorphic author fields and validation for interactive components (Likes/Comments).
    """

    student_id = Column(
        Integer, ForeignKey('students.id', ondelete='RESTRICT'), nullable=True
    )
    user_id = Column(
        Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=True
    )
    guest_name = Column(String, nullable=True)

    @declared_attr
    def student(cls):
        return relationship('Student')

    @declared_attr
    def user(cls):
        return relationship('User')

    @declared_attr
    def __table_args__(cls):
        return cls._get_author_checks()

    @classmethod
    def _get_author_checks(cls):
        return (
            CheckConstraint(
                '(CASE WHEN student_id IS NOT NULL THEN 1 ELSE 0 END + '
                'CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END + '
                'CASE WHEN guest_name IS NOT NULL THEN 1 ELSE 0 END) = 1',
                name=f'{cls.__tablename__}_single_author_check',
            ),
        )

    @validates('student_id', 'user_id', 'guest_name')
    def validate_single_author(self, key, value):
        """
        Ensure only one author type is set before flushing to the database.
        """
        current_values = {
            'student_id': self.student_id,
            'user_id': self.user_id,
            'guest_name': self.guest_name,
        }
        current_values[key] = value

        non_null_count = sum(1 for v in current_values.values() if v is not None)

        if non_null_count > 1:
            raise ValueError(
                f'An interaction can only have one author. Check {self.__tablename__}.'
            )

        return value

    @property
    def author_info(self):
        """
        Helper to return standardized author info
        """
        if self.student_id:
            return {
                'role': 'student',
                'id': str(self.student_id),
                'name': self.student.name
                if getattr(self, 'student', None)
                else 'Unknown Student',
            }
        elif self.user_id:
            return {
                'role': 'teacher',
                'id': str(self.user_id),
                'name': self.user.username
                if getattr(self, 'user', None)
                else 'Unknown Teacher',
            }
        else:
            return {'role': 'guest', 'id': self.guest_name, 'name': self.guest_name}


# ==========================================
# Core Models
# ==========================================


class User(SoftDeleteMixin, Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    students = relationship('Student', back_populates='teacher')
    questions = relationship('Question', back_populates='owner')
    exams = relationship('Exam', back_populates='owner')


class Student(SoftDeleteMixin, Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    admission_year = Column(Integer, nullable=True)
    class_name = Column(String(50), nullable=True)
    teacher_id = Column(
        Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=True
    )

    teacher = relationship('User', back_populates='students')


class Question(SoftDeleteMixin, Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)
    reference_answer = Column(JSON, nullable=False)
    difficulty = Column(Integer, nullable=True, index=True)
    lesson = Column(String(100), nullable=True, index=True)
    literacy_tags = Column(JSON, nullable=True)
    needs_manual_grading = Column(
        Boolean, default=False, server_default='false', nullable=False
    )

    is_public = Column(Boolean, default=False, server_default='false', nullable=False)
    is_locked = Column(
        Boolean, default=False, server_default='false', nullable=False, index=True
    )
    is_archived = Column(
        Boolean, default=False, server_default='false', nullable=False, index=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner_id = Column(
        Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=True
    )

    owner = relationship('User', back_populates='questions')


class Exam(SoftDeleteMixin, Base):
    __tablename__ = 'exams'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(Date, nullable=True)

    is_locked = Column(
        Boolean, default=False, server_default='false', nullable=False, index=True
    )
    is_archived = Column(
        Boolean, default=False, server_default='false', nullable=False, index=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner_id = Column(
        Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=True
    )

    owner = relationship('User', back_populates='exams')
    exam_questions = relationship(
        'ExamQuestion',
        back_populates='exam',
        order_by='ExamQuestion.sort_order',
    )


class ExamQuestion(SoftDeleteMixin, Base):
    __tablename__ = 'exam_questions'

    sort_order = Column(Integer, default=0, nullable=False)
    score = Column(Integer, default=10, server_default='10', nullable=False)
    allow_peer_review = Column(Boolean, default=False)
    exam_id = Column(
        Integer, ForeignKey('exams.id', ondelete='RESTRICT'), primary_key=True
    )
    question_id = Column(
        Integer, ForeignKey('questions.id', ondelete='RESTRICT'), primary_key=True
    )

    exam = relationship('Exam', back_populates='exam_questions')
    question = relationship('Question')


class Media(SoftDeleteMixin, Base):
    __tablename__ = 'media'

    id = Column(Integer, primary_key=True, index=True)
    fid = Column(String, unique=True, index=True, nullable=False)
    uploader_id = Column(
        Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StudentSubmission(SoftDeleteMixin, Base):
    __tablename__ = 'student_submissions'

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(
        Integer, ForeignKey('exams.id', ondelete='RESTRICT'), nullable=False
    )
    student_id = Column(
        Integer, ForeignKey('students.id', ondelete='RESTRICT'), nullable=True
    )
    guest_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    record_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    discussion_score = Column(Integer, nullable=True)
    session_id = Column(String(36), nullable=True, index=True)

    exam = relationship('Exam')
    student = relationship('Student')
    answers = relationship('StudentAnswer', back_populates='submission')


class StudentAnswer(SoftDeleteMixin, Base):
    __tablename__ = 'student_answers'

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer,
        ForeignKey('student_submissions.id', ondelete='RESTRICT'),
        nullable=False,
    )
    exam_id = Column(
        Integer, ForeignKey('exams.id', ondelete='RESTRICT'), nullable=False
    )
    question_id = Column(
        Integer, ForeignKey('questions.id', ondelete='RESTRICT'), nullable=False
    )
    answer_content = Column(Text, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submission = relationship('StudentSubmission', back_populates='answers')
    exam = relationship('Exam')
    question = relationship('Question')
    grading_histories = relationship('AnswerGradingHistory', back_populates='answer')


class AnswerGradingHistory(SoftDeleteMixin, Base):
    __tablename__ = 'answer_grading_histories'

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(
        Integer, ForeignKey('student_answers.id', ondelete='RESTRICT'), nullable=False
    )
    old_score = Column(Integer, nullable=True)
    new_score = Column(Integer, nullable=True)
    teacher_id = Column(
        Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    answer = relationship('StudentAnswer', back_populates='grading_histories')
    teacher = relationship('User')


# ==========================================
# Social Interaction Models
# ==========================================


class InteractionComment(SoftDeleteMixin, InteractiveMixin, Base):
    __tablename__ = 'interaction_comments'

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(
        Integer, ForeignKey('student_answers.id', ondelete='RESTRICT'), nullable=True
    )
    question_id = Column(
        Integer, ForeignKey('questions.id', ondelete='RESTRICT'), nullable=True
    )
    option_index = Column(Integer, nullable=True)
    # Session anchor for option-level comments (NULL for answer-level since
    # the link is implicit via answer.submission_id)
    submission_id = Column(
        Integer, ForeignKey('student_submissions.id', ondelete='RESTRICT'), nullable=True
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    answer = relationship('StudentAnswer', backref='comments')
    question = relationship('Question')
    submission = relationship('StudentSubmission')

    @declared_attr
    def __table_args__(cls):
        mixin_args = cls._get_author_checks()
        target_args = (
            CheckConstraint(
                '(CASE WHEN answer_id IS NOT NULL THEN 1 ELSE 0 END + '
                'CASE WHEN (question_id IS NOT NULL AND option_index IS NOT NULL) '
                'THEN 1 ELSE 0 END) = 1',
                name=f'{cls.__tablename__}_single_target_check',
            ),
        )
        return mixin_args + target_args

    @validates('answer_id', 'question_id')
    def validate_single_target(self, key, value):
        """
        Ensure a comment targets strictly one answer OR one question option.
        """
        current_values = {
            'answer_id': self.answer_id,
            'question_id': self.question_id,
        }
        current_values[key] = value
        non_null_count = sum(1 for v in current_values.values() if v is not None)
        if non_null_count > 1:
            raise ValueError(
                'A comment can only target one item (either answer or question option).'
            )
        if non_null_count == 0 and value is None:
            raise ValueError(
                'A comment must target either an answer or a question option.'
            )
        return value


class InteractionLike(SoftDeleteMixin, InteractiveMixin, Base):
    __tablename__ = 'interaction_likes'

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(
        Integer, ForeignKey('student_answers.id', ondelete='RESTRICT'), nullable=True
    )
    comment_id = Column(
        Integer,
        ForeignKey('interaction_comments.id', ondelete='RESTRICT'),
        nullable=True,
    )
    question_id = Column(
        Integer, ForeignKey('questions.id', ondelete='RESTRICT'), nullable=True
    )
    option_index = Column(Integer, nullable=True)
    # Session anchor for option-level likes (NULL for answer/comment likes since
    # those link via answer.submission_id or comment.answer/comment.submission_id)
    submission_id = Column(
        Integer, ForeignKey('student_submissions.id', ondelete='RESTRICT'), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    answer = relationship('StudentAnswer', backref='likes')
    comment = relationship('InteractionComment', backref='likes')
    question = relationship('Question')
    submission = relationship('StudentSubmission')

    @declared_attr
    def __table_args__(cls):
        # Fetch the author constraints from the Mixin
        mixin_args = cls._get_author_checks()

        # Like can target exactly one of: answer / comment / question option
        target_args = (
            CheckConstraint(
                '(CASE WHEN answer_id IS NOT NULL THEN 1 ELSE 0 END + '
                'CASE WHEN comment_id IS NOT NULL THEN 1 ELSE 0 END + '
                'CASE WHEN (question_id IS NOT NULL AND option_index IS NOT NULL) '
                'THEN 1 ELSE 0 END) = 1',
                name=f'{cls.__tablename__}_single_target_check',
            ),
        )

        return mixin_args + target_args

    @validates('answer_id', 'comment_id', 'question_id')
    def validate_single_target(self, key, value):
        """
        Ensure a like targets strictly one of: answer / comment / question option.
        """
        current_values = {
            'answer_id': self.answer_id,
            'comment_id': self.comment_id,
            'question_id': self.question_id,
        }
        current_values[key] = value

        non_null_count = sum(1 for v in current_values.values() if v is not None)
        if non_null_count > 1:
            raise ValueError(
                'A like can only target one item (answer, comment, or question option).'
            )
        if non_null_count == 0 and value is None:
            raise ValueError(
                'A like must target exactly one item (answer, comment, or question option).'
            )

        return value
