from typing import List, Optional

import models
import schemas
from core.deps import get_current_user
from crud import exams as crud_exams
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/exams', tags=['exams'])


@router.get('/', response_model=List[schemas.ExamResponse])
async def read_exams(
    is_locked: Optional[bool] = Query(None, description='Filter exams by lock status'),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_exams.get_exams(db, current_user, is_locked=is_locked)


@router.get('/{exam_id}', response_model=schemas.ExamResponse)
async def read_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_exam = await crud_exams.get_exam(db, exam_id, current_user)
    if not db_exam:
        raise HTTPException(status_code=404, detail='Exam not found')
    return db_exam


@router.post(
    '/', response_model=schemas.ExamResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_exam(
    exam: schemas.ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Verify question access before creating the exam
    if exam.questions:
        question_ids = [q.question_id for q in exam.questions]
        has_access = await crud_exams.verify_questions_access(
            db, question_ids, current_user
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='One or more questions are not found or you do not have permission to use them.',
            )

    return await crud_exams.create_exam(db, exam, current_user)


@router.put('/{exam_id}', response_model=schemas.ExamResponse)
async def update_existing_exam(
    exam_id: int,
    exam_in: schemas.ExamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_exam = await crud_exams.get_exam(db, exam_id, current_user)
    if not db_exam:
        raise HTTPException(status_code=404, detail='Exam not found')

    # Business Rule: Cannot modify a locked exam
    if db_exam.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='This exam is locked and cannot be edited.',
        )

    # Verify question access before updating the exam
    if exam_in.questions is not None:
        question_ids = [q.question_id for q in exam_in.questions]
        if question_ids:
            has_access = await crud_exams.verify_questions_access(
                db, question_ids, current_user
            )
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail='One or more questions are not found or you do not have permission to use them.',
                )

    updated_exam = await crud_exams.update_exam(db, db_exam, exam_in, current_user)
    return updated_exam


@router.delete('/{exam_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_exam = await crud_exams.get_exam(db, exam_id, current_user)
    if not db_exam:
        raise HTTPException(status_code=404, detail='Exam not found')

    # Business Rule: Cannot delete a locked exam
    if db_exam.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='This exam is locked and cannot be deleted.',
        )

    await crud_exams.delete_exam(db, db_exam, current_user)
