import models
import schemas
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession


# Get a single question by ID with data isolation
async def get_question(db: AsyncSession, question_id: int, current_user: models.User):
    query = select(models.Question).where(models.Question.id == question_id)

    # Data isolation: Regular teachers can only view their own questions or public ones
    if not current_user.is_superuser:
        query = query.where(
            or_(
                models.Question.owner_id == current_user.id,
                models.Question.is_public == True,
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
):
    query = select(models.Question).where(models.Question.is_archived.is_not(True))

    # Data isolation: Regular teachers see their own questions + public questions
    if not current_user.is_superuser:
        query = query.where(
            or_(
                models.Question.owner_id == current_user.id,
                models.Question.is_public == True,
            )
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

    # Automatically assign the current user as the owner if not provided
    if question_data.get('owner_id') is None:
        question_data['owner_id'] = current_user.id

    db_question = models.Question(**question_data)
    db.add(db_question)
    await db.commit()
    await db.refresh(db_question)
    return db_question


# Update an existing question dynamically with ownership check
async def update_question(
    db: AsyncSession,
    db_question: models.Question,
    question_update: schemas.QuestionUpdate,
    current_user: models.User,
):
    # Security check: Only the owner or a superuser can modify the question
    if not current_user.is_superuser and db_question.owner_id != current_user.id:
        return None

    update_data = question_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_question, key, value)

    await db.commit()
    await db.refresh(db_question)
    return db_question


# Delete a question (Soft Delete) with ownership check
async def delete_question(
    db: AsyncSession, db_question: models.Question, current_user: models.User
):
    # Security check: Only the owner or a superuser can delete the question
    if not current_user.is_superuser and db_question.owner_id != current_user.id:
        return False

    db_question.is_archived = True
    await db.commit()
    return True
