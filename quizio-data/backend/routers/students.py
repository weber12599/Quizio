from typing import Annotated, List, Optional

import models
import schemas
from core.deps import get_current_user
from crud import students as crud_students
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/students', tags=['students'])


# ==========================================
# Dependencies
# ==========================================


async def get_student_rwd(
    student_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Student:
    db_student = await crud_students.get_student(db, student_db_id, current_user)
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Student not found'
        )
    return db_student


@router.get('/classes', response_model=List[str])
async def get_unique_classes(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_students.get_teacher_classes(db, current_user)


@router.get('/', response_model=List[schemas.StudentResponse])
async def read_students(
    admission_year: Optional[int] = None,
    class_name: Optional[str] = None,
    is_deleted: Optional[bool] = Query(
        None, description='Filter students by deleted status (default False)'
    ),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_students.get_students(
        db,
        current_user,
        admission_year=admission_year,
        class_name=class_name,
        is_deleted=is_deleted,
    )


@router.get('/{student_db_id}', response_model=schemas.StudentResponse)
async def read_student(db_student: models.Student = Depends(get_student_rwd)):
    return db_student


@router.post(
    '/', response_model=schemas.StudentResponse, status_code=status.HTTP_201_CREATED
)
async def create_new_student(
    student: schemas.StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        return await crud_students.create_student(db, student, current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Student ID {student.student_id} exists',
        )


@router.post('/bulk', response_model=schemas.StudentBulkUpsertResponse)
async def bulk_upsert_students(
    students: Annotated[List[schemas.StudentCreate], Field(max_length=500)],
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    created, updated, failed = await crud_students.upsert_students_batch(
        db, students, current_user
    )
    return schemas.StudentBulkUpsertResponse(
        created=created, updated=updated, failed=failed
    )


@router.patch('/batch', response_model=schemas.StudentBatchUpdateResponse)
async def batch_update_existing_students(
    updates: List[schemas.StudentBatchUpdateItem],
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    updated_ids, failed_ids = await crud_students.batch_update_students(
        db, updates, current_user
    )
    return schemas.StudentBatchUpdateResponse(updated=updated_ids, failed=failed_ids)


@router.put('/{student_db_id}', response_model=schemas.StudentResponse)
async def update_existing_student(
    student_in: schemas.StudentUpdate,
    db_student: models.Student = Depends(get_student_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        updated_student = await crud_students.update_student(
            db, db_student, student_in, current_user
        )
        return updated_student
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Student ID {student_in.student_id} exists',
        )


# ==========================================
# Lifecycle Management Endpoints
# ==========================================


@router.post('/{student_db_id}/restore', response_model=schemas.StudentResponse)
async def restore_deleted_student(
    db_student: models.Student = Depends(get_student_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_students.toggle_delete_student(
        db, db_student, False, current_user
    )


@router.delete('/{student_db_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_student(
    db_student: models.Student = Depends(get_student_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    await crud_students.toggle_delete_student(db, db_student, True, current_user)
