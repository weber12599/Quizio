from typing import List, Optional

import models
import schemas
from core.deps import get_current_user
from crud import exams as crud_exams
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/exams', tags=['exams'])


# ==========================================
# Dependencies
# ==========================================


async def get_exam_rwd(
    exam_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Exam:
    db_exam = await crud_exams.get_exam(db, exam_db_id, current_user)
    if not db_exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Exam not found'
        )
    return db_exam


@router.get('/', response_model=List[schemas.ExamResponse])
async def read_exams(
    is_locked: Optional[bool] = Query(None, description='Filter exams by lock status'),
    is_archived: Optional[bool] = Query(
        False, description='Filter exams by archive status (default False)'
    ),
    is_deleted: Optional[bool] = Query(
        False, description='Filter exams by deleted status (default False)'
    ),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_exams.get_exams(
        db,
        current_user,
        is_locked=is_locked,
        is_archived=is_archived,
        is_deleted=is_deleted,
    )


@router.get('/{exam_db_id}', response_model=schemas.ExamResponse)
async def read_exam(db_exam: models.Exam = Depends(get_exam_rwd)):
    return db_exam


@router.post(
    '/', response_model=schemas.ExamResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_exam(
    exam: schemas.ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return await crud_exams.create_exam(db, exam, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put('/{exam_db_id}', response_model=schemas.ExamResponse)
async def update_existing_exam(
    exam_in: schemas.ExamUpdate,
    db_exam: models.Exam = Depends(get_exam_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        updated_exam = await crud_exams.update_exam(db, db_exam, exam_in, current_user)
        return updated_exam
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ==========================================
# Lifecycle Management Endpoints
# ==========================================


@router.post('/{exam_db_id}/lock', response_model=schemas.ExamResponse)
async def lock_existing_exam(
    db_exam: models.Exam = Depends(get_exam_rwd),
    db: AsyncSession = Depends(get_db),
):
    return await crud_exams.lock_exam(db, db_exam)


@router.put('/{exam_db_id}/archive', response_model=schemas.ExamResponse)
async def archive_existing_exam(
    is_archived: bool = Query(
        ..., description='Set to true to archive, false to unarchive'
    ),
    db_exam: models.Exam = Depends(get_exam_rwd),
    db: AsyncSession = Depends(get_db),
):
    return await crud_exams.toggle_archive_exam(db, db_exam, is_archived)


@router.post('/{exam_db_id}/restore', response_model=schemas.ExamResponse)
async def restore_deleted_exam(
    db_exam: models.Exam = Depends(get_exam_rwd),
    db: AsyncSession = Depends(get_db),
):
    return await crud_exams.toggle_delete_exam(db, db_exam, is_deleted=False)


@router.delete('/{exam_db_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_exam(
    db_exam: models.Exam = Depends(get_exam_rwd),
    db: AsyncSession = Depends(get_db),
):
    await crud_exams.toggle_delete_exam(db, db_exam, is_deleted=True)
