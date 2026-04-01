from typing import List, Optional

import models
import schemas
from core.deps import get_current_user
from crud import questions as crud_questions
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/questions', tags=['questions'])


@router.get('/', response_model=List[schemas.Question])
async def read_questions(
    question_type: Optional[str] = None,
    difficulty: Optional[int] = None,
    lesson: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_questions.get_questions(
        db=db,
        current_user=current_user,
        question_type=question_type,
        difficulty=difficulty,
        lesson=lesson,
    )


@router.get('/{question_id}', response_model=schemas.Question)
async def read_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_question = await crud_questions.get_question(db, question_id, current_user)
    if not db_question:
        raise HTTPException(status_code=404, detail='Question not found')
    return db_question


@router.post('/', response_model=schemas.Question, status_code=status.HTTP_201_CREATED)
async def create_new_question(
    question: schemas.QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_questions.create_question(db, question, current_user)


@router.put('/{question_id}', response_model=schemas.Question)
async def update_existing_question(
    question_id: int,
    question_in: schemas.QuestionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Retrieve the existing question first
    db_question = await crud_questions.get_question(db, question_id, current_user)
    if not db_question:
        raise HTTPException(status_code=404, detail='Question not found')

    # Attempt to update it
    updated_question = await crud_questions.update_question(
        db, db_question, question_in, current_user
    )

    # Check if ownership validation failed
    if not updated_question:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not authorized to update this question',
        )

    return updated_question


@router.delete('/{question_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Retrieve the existing question first
    db_question = await crud_questions.get_question(db, question_id, current_user)
    if not db_question:
        raise HTTPException(status_code=404, detail='Question not found')

    # Attempt to delete it
    success = await crud_questions.delete_question(db, db_question, current_user)

    # Check if ownership validation failed
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not authorized to delete this question',
        )
