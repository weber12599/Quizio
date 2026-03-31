from typing import List, Optional

import crud
import schemas
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status

# Import the oauth2_scheme to protect these routes
from routers.auth import oauth2_scheme
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix='/api/questions', tags=['questions'], dependencies=[Depends(oauth2_scheme)]
)


@router.get('', response_model=List[schemas.QuestionOut])
async def read_questions(
    type: Optional[str] = None,
    difficulty: Optional[int] = None,
    lesson: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_questions(
        db, question_type=type, difficulty=difficulty, lesson=lesson
    )


@router.post(
    '', response_model=schemas.QuestionOut, status_code=status.HTTP_201_CREATED
)
async def create_question(
    question: schemas.QuestionCreate, db: AsyncSession = Depends(get_db)
):
    return await crud.create_question(db=db, question=question)


@router.put('/{question_id}', response_model=schemas.QuestionOut)
async def update_question(
    question_id: int,
    question_update: schemas.QuestionUpdate,
    db: AsyncSession = Depends(get_db),
):
    db_question = await crud.get_question(db, question_id=question_id)
    if not db_question:
        raise HTTPException(status_code=404, detail='Question not found')
    return await crud.update_question(
        db=db, db_question=db_question, question_update=question_update
    )


@router.delete('/{question_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, db: AsyncSession = Depends(get_db)):
    db_question = await crud.get_question(db, question_id=question_id)
    if not db_question:
        raise HTTPException(status_code=404, detail='Question not found')
    await crud.delete_question(db=db, db_question=db_question)
