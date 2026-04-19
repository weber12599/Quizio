from typing import List, Optional

import models
import schemas
from core.deps import get_current_user
from crud import questions as crud_questions
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/questions', tags=['questions'])


# ==========================================
# Dependencies
# ==========================================


async def get_question_r(
    question_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Question:
    db_question = await crud_questions.get_question(db, question_db_id, current_user)
    if not db_question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Question not found'
        )
    return db_question


async def get_question_rwd(
    db_question: models.Question = Depends(get_question_r),
    current_user: models.User = Depends(get_current_user),
) -> models.Question:
    if not current_user.is_superuser and db_question.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Unauthorized access: You do not own this question.',
        )
    return db_question


@router.get('/', response_model=List[schemas.QuestionResponse])
async def read_questions(
    question_type: Optional[str] = None,
    difficulty: Optional[int] = None,
    lesson: Optional[str] = None,
    is_locked: Optional[bool] = Query(
        None, description='Filter questions by lock status'
    ),
    is_archived: Optional[bool] = Query(
        None, description='Filter questions by archive status (default False)'
    ),
    is_deleted: Optional[bool] = Query(
        None, description='Filter questions by deleted status (default False)'
    ),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_questions.get_questions(
        db,
        current_user,
        question_type=question_type,
        difficulty=difficulty,
        lesson=lesson,
        is_locked=is_locked,
        is_archived=is_archived,
        is_deleted=is_deleted,
    )


@router.get('/{question_db_id}', response_model=schemas.QuestionResponse)
async def read_question(db_question: models.Question = Depends(get_question_r)):
    return db_question


@router.post(
    '/', response_model=schemas.QuestionResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_question(
    question: schemas.QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return await crud_questions.create_question(db, question, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put('/{question_db_id}', response_model=schemas.QuestionResponse)
async def update_existing_question(
    question_in: schemas.QuestionUpdate,
    db_question: models.Question = Depends(get_question_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Business Rule: Once a question is public, it cannot be reverted to private
    if db_question.is_public and question_in.is_public is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Once a question is public, it cannot be made private.',
        )

    try:
        updated_question = await crud_questions.update_question(
            db, db_question, question_in, current_user
        )
        return updated_question
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==========================================
# Lifecycle Management Endpoints
# ==========================================


@router.post('/{question_db_id}/lock', response_model=schemas.QuestionResponse)
async def lock_existing_question(
    db_question: models.Question = Depends(get_question_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_questions.lock_question(db, db_question, current_user)


@router.put('/{question_db_id}/archive', response_model=schemas.QuestionResponse)
async def archive_existing_question(
    is_archived: bool = Query(
        ..., description='Set to true to archive, false to unarchive'
    ),
    db_question: models.Question = Depends(get_question_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_questions.toggle_archive_question(
        db, db_question, is_archived, current_user
    )


@router.post('/{question_db_id}/restore', response_model=schemas.QuestionResponse)
async def restore_deleted_question(
    db_question: models.Question = Depends(get_question_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_questions.toggle_delete_question(
        db, db_question, False, current_user
    )


@router.delete('/{question_db_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_question(
    db_question: models.Question = Depends(get_question_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    await crud_questions.toggle_delete_question(db, db_question, True, current_user)
