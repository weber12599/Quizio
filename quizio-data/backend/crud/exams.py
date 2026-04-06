from typing import List

import models
import schemas
from sqlalchemy import delete, or_, select
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
    query = select(models.Question).where(models.Question.id.in_(unique_q_ids))

    # Data isolation: Superusers bypass this filter
    if not current_user.is_superuser:
        query = query.where(
            or_(
                models.Question.owner_id == current_user.id,
                models.Question.is_public == True,
            )
        )

    result = await db.execute(query)
    valid_questions = result.scalars().all()

    # If the count matches, it means all requested questions exist and are authorized
    return len(valid_questions) == len(unique_q_ids)


# Get a single exam by ID, eagerly loading its questions
async def get_exam(db: AsyncSession, exam_id: int, current_user: models.User):
    query = (
        select(models.Exam)
        .options(
            # Eagerly load exam_questions and the nested question details
            selectinload(models.Exam.exam_questions).selectinload(
                models.ExamQuestion.question
            )
        )
        .where(models.Exam.id == exam_id)
    )

    # Data isolation: Regular teachers can only view their own exams
    if not current_user.is_superuser:
        query = query.where(models.Exam.owner_id == current_user.id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


# Get all exams for the current user
async def get_exams(db: AsyncSession, current_user: models.User):
    query = select(models.Exam).options(
        selectinload(models.Exam.exam_questions).selectinload(
            models.ExamQuestion.question
        )
    )

    if not current_user.is_superuser:
        query = query.where(models.Exam.owner_id == current_user.id)

    query = query.order_by(models.Exam.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


# Create a new exam
async def create_exam(
    db: AsyncSession, exam: schemas.ExamCreate, current_user: models.User
):
    # Verify if the user has access to the provided question_ids
    if exam.question_ids:
        has_access = await verify_questions_access(db, exam.question_ids, current_user)
        if not has_access:
            # Raise an appropriate error to be caught by the exception handler
            raise ValueError('Unauthorized access to one or more questions.')

    # Extract basic exam data, exclude question_ids for now
    exam_data = exam.model_dump(exclude={'question_ids'})
    exam_data['owner_id'] = current_user.id

    db_exam = models.Exam(**exam_data)
    db.add(db_exam)
    await db.flush()  # Flush to get the generated exam ID

    # Create associations for questions if any were provided
    if exam.question_ids:
        for index, q_id in enumerate(exam.question_ids):
            db_exam_question = models.ExamQuestion(
                exam_id=db_exam.id,
                question_id=q_id,
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
    # Verify if the user has access to the provided question_ids
    if exam_update.question_ids:
        has_access = await verify_questions_access(
            db, exam_update.question_ids, current_user
        )
        if not has_access:
            # Raise an appropriate error to be caught by the exception handler
            raise ValueError('Unauthorized access to one or more questions.')

    update_data = exam_update.model_dump(exclude_unset=True, exclude={'question_ids'})

    # Update basic fields (title, description, is_locked)
    for key, value in update_data.items():
        setattr(db_exam, key, value)

    # If question_ids are provided, replace the entire question list
    if exam_update.question_ids is not None:
        # Step 1: Remove existing questions for this exam
        await db.execute(
            delete(models.ExamQuestion).where(models.ExamQuestion.exam_id == db_exam.id)
        )

        # Step 2: Insert the new questions
        for index, q_id in enumerate(exam_update.question_ids):
            db_exam_question = models.ExamQuestion(
                exam_id=db_exam.id,
                question_id=q_id,
                sort_order=index,
            )
            db.add(db_exam_question)

    await db.commit()
    return await get_exam(db, db_exam.id, current_user)


# Delete an exam
async def delete_exam(
    db: AsyncSession, db_exam: models.Exam, current_user: models.User
):
    await db.delete(db_exam)
    await db.commit()
    return True
