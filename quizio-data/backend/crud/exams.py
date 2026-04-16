from typing import List, Optional

import models
import schemas
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


# Verify question access
async def verify_questions_access(
    db: AsyncSession, question_ids: List[int], current_user: models.User
) -> bool:
    if not question_ids:
        return True

    # Remove duplicates for the database check
    unique_q_ids = list(set(question_ids))

    # Strict mode: Questions must be active, not archived, and explicitly locked
    query = select(models.Question).where(
        models.Question.id.in_(unique_q_ids),
        models.Question.deleted_at.is_(None),
        models.Question.is_archived.is_(False),
        models.Question.is_locked.is_(True),
    )

    # Data isolation: Superusers bypass this filter
    if not current_user.is_superuser:
        query = query.where(
            or_(
                models.Question.owner_id == current_user.id,
                models.Question.is_public.is_(True),
            )
        )

    result = await db.execute(query)
    valid_questions = result.scalars().all()

    # If the count matches, it means all requested questions exist and are authorized
    return len(valid_questions) == len(unique_q_ids)


# Get a single exam by ID, eagerly loading its questions
async def get_exam(db: AsyncSession, exam_db_id: int, current_user: models.User):
    query = (
        select(models.Exam)
        .options(
            # Eagerly load exam_questions and the nested question details
            selectinload(models.Exam.exam_questions).selectinload(
                models.ExamQuestion.question
            )
        )
        .where(models.Exam.id == exam_db_id)
    )

    # Data isolation: Regular teachers can only view their own exams
    if not current_user.is_superuser:
        query = query.where(models.Exam.owner_id == current_user.id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


# Get all exams for the current user
async def get_exams(
    db: AsyncSession,
    current_user: models.User,
    is_locked: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    is_deleted: Optional[bool] = None,
):
    query = select(models.Exam).options(
        selectinload(models.Exam.exam_questions).selectinload(
            models.ExamQuestion.question
        )
    )

    if not current_user.is_superuser:
        query = query.where(models.Exam.owner_id == current_user.id)

    if is_locked is not None:
        query = query.where(models.Exam.is_locked == is_locked)

    if is_archived is not None:
        query = query.where(models.Exam.is_archived == is_archived)

    if is_deleted is not None:
        query = (
            query.where(models.Exam.deleted_at.is_not(None))
            if is_deleted
            else query.where(models.Exam.deleted_at.is_(None))
        )

    query = query.order_by(models.Exam.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


# Create a new exam
async def create_exam(
    db: AsyncSession, exam: schemas.ExamCreate, current_user: models.User
):
    # Extract question IDs from the setup objects for permission verification
    question_ids = [q.question_id for q in exam.questions] if exam.questions else []

    # Verify if the user has access to the provided question_ids
    if question_ids:
        has_access = await verify_questions_access(db, question_ids, current_user)
        if not has_access:
            # Raise an appropriate error to be caught by the exception handler
            raise ValueError('Unauthorized access to one or more questions.')

    # Extract basic exam data, exclude questions for now
    exam_data = exam.model_dump(exclude={'questions'})
    exam_data['owner_id'] = current_user.id

    db_exam = models.Exam(**exam_data)
    db.add(db_exam)
    await db.flush()  # Flush to get the generated exam ID

    # Create associations for questions along with their scores
    if exam.questions:
        for index, q_setup in enumerate(exam.questions):
            db_exam_question = models.ExamQuestion(
                exam_id=db_exam.id,
                question_id=q_setup.question_id,
                score=q_setup.score,
                sort_order=index,  # Use array index as the sequence order
            )
            db.add(db_exam_question)

    await db.commit()
    # Fetch again to load all relationships properly for the response
    return await get_exam(db, db_exam.id, current_user)


# Update an existing exam
async def update_exam(
    db: AsyncSession,
    db_exam: models.Exam,
    exam_update: schemas.ExamUpdate,
    current_user: models.User,
):
    # Core defense: Once locked, archived or deleted, an exam cannot be modified
    if db_exam.is_locked or db_exam.is_archived or db_exam.deleted_at is not None:
        raise ValueError('Cannot modify a protected exam. Please clone it to edit.')

    # Verify if the user has access to the newly provided questions
    if exam_update.questions is not None:
        question_ids = [q.question_id for q in exam_update.questions]
        if question_ids:
            has_access = await verify_questions_access(db, question_ids, current_user)
            if not has_access:
                raise ValueError('Unauthorized access to one or more questions.')

    update_data = exam_update.model_dump(exclude_unset=True, exclude={'questions'})

    # Prevent modification of locked or archived states through standard updates
    update_data.pop('is_locked', None)
    update_data.pop('is_archived', None)
    for key, value in update_data.items():
        setattr(db_exam, key, value)

    # If questions are provided, replace the entire question list
    if exam_update.questions is not None:
        # Step 1: Remove existing questions for this exam
        await db.execute(
            delete(models.ExamQuestion).where(models.ExamQuestion.exam_id == db_exam.id)
        )

        # Step 2: Insert the new questions with their assigned scores
        for index, q_setup in enumerate(exam_update.questions):
            db_exam_question = models.ExamQuestion(
                exam_id=db_exam.id,
                question_id=q_setup.question_id,
                score=q_setup.score,
                sort_order=index,
            )
            db.add(db_exam_question)

    db_exam.updated_at = func.now()
    await db.commit()
    return await get_exam(db, db_exam.id, current_user)


# Lock an exam
async def lock_exam(db: AsyncSession, db_exam: models.Exam):
    if db_exam.is_locked:
        return db_exam

    db_exam.is_locked = True
    db_exam.updated_at = func.now()
    await db.commit()
    return db_exam


# Archive or Unarchive an exam
async def toggle_archive_exam(
    db: AsyncSession, db_exam: models.Exam, is_archived: bool
):
    if not (db_exam.is_archived ^ is_archived):
        return db_exam

    db_exam.is_archived = is_archived
    db_exam.updated_at = func.now()
    await db.commit()
    return db_exam


# Soft delete an exam
async def toggle_delete_exam(db: AsyncSession, db_exam: models.Exam, is_deleted: bool):
    current_is_deleted = db_exam.deleted_at is not None
    if not (current_is_deleted ^ is_deleted):
        return db_exam

    db_exam.deleted_at = func.now() if is_deleted else None
    db_exam.updated_at = func.now()
    await db.commit()
    return db_exam
