from typing import Optional

import models
import schemas
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


# Get a single question by ID with data isolation
async def get_question(
    db: AsyncSession, question_db_id: int, current_user: models.User
):
    query = select(models.Question).where(models.Question.id == question_db_id)

    # Data isolation: Regular teachers can only view their own questions or public ones
    if not current_user.is_superuser:
        query = query.where(
            or_(
                models.Question.owner_id == current_user.id,
                models.Question.is_public.is_(True),
            )
        )

    result = await db.execute(query)
    return result.scalar_one_or_none()


# Get multiple questions with optional filters and data isolation
async def get_questions(
    db: AsyncSession,
    current_user: models.User,
    question_type: str = None,
    difficulty: int = None,
    lesson: str = None,
    is_locked: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
):
    query = select(models.Question)

    if not current_user.is_superuser:
        query = query.where(
            or_(
                models.Question.owner_id == current_user.id,
                models.Question.is_public.is_(True),
            )
        )

    if is_locked is not None:
        query = query.where(models.Question.is_locked == is_locked)

    if is_archived is not None:
        query = query.where(models.Question.is_archived == is_archived)

    if is_deleted is not None:
        query = (
            query.where(models.Question.deleted_at.is_not(None))
            if is_deleted
            else query.where(models.Question.deleted_at.is_(None))
        )

    if question_type:
        query = query.where(models.Question.type == question_type)

    if difficulty is not None:
        query = query.where(models.Question.difficulty == difficulty)

    if lesson:
        query = query.where(models.Question.lesson == lesson)

    query = query.order_by(models.Question.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


# Create a new question
async def create_question(
    db: AsyncSession, question: schemas.QuestionCreate, current_user: models.User
):
    question_data = question.model_dump()
    question_data['owner_id'] = current_user.id

    db_question = models.Question(**question_data)
    db.add(db_question)
    await db.flush()  # Flush to get the generated question ID

    await db.commit()
    return await get_question(db, db_question.id, current_user)


# Update an existing question
async def update_question(
    db: AsyncSession,
    db_question: models.Question,
    question_update: schemas.QuestionUpdate,
    current_user: models.User,
):
    # Core defense: Once locked, archived or deleted, a question cannot be modified
    if (
        db_question.is_locked
        or db_question.is_archived
        or db_question.deleted_at is not None
    ):
        raise ValueError('Cannot modify a protected question. Please clone it to edit.')

    # Security check: Only the owner or a superuser can modify the question
    if not current_user.is_superuser and db_question.owner_id != current_user.id:
        raise ValueError('Unauthorized access to the question.')

    update_data = question_update.model_dump(exclude_unset=True)

    # Prevent modification of locked or archived states through standard updates
    update_data.pop('is_locked', None)
    update_data.pop('is_archived', None)
    for key, value in update_data.items():
        setattr(db_question, key, value)

    db_question.updated_at = func.now()
    await db.commit()
    return await get_question(db, db_question.id, current_user)


# Lock a question
async def lock_question(
    db: AsyncSession, db_question: models.Question, current_user: models.User
):
    if db_question.is_locked:
        return db_question

    db_question.is_locked = True
    db_question.updated_at = func.now()
    await db.commit()
    return await get_question(db, db_question.id, current_user)


# Archive or Unarchive a question
async def toggle_archive_question(
    db: AsyncSession,
    db_question: models.Question,
    is_archived: bool,
    current_user: models.User,
):
    if not (db_question.is_archived ^ is_archived):
        return db_question

    db_question.is_archived = is_archived
    db_question.updated_at = func.now()
    await db.commit()
    return await get_question(db, db_question.id, current_user)


# Soft delete a question
async def toggle_delete_question(
    db: AsyncSession,
    db_question: models.Question,
    is_deleted: bool,
    current_user: models.User,
):
    current_is_deleted = db_question.deleted_at is not None
    if not (current_is_deleted ^ is_deleted):
        return db_question

    db_question.deleted_at = func.now() if is_deleted else None
    db_question.updated_at = func.now()
    await db.commit()
    return await get_question(db, db_question.id, current_user)
