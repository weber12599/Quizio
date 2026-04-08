from typing import List, Optional

import models
import schemas
from core.deps import get_current_user
from crud import students as crud_students
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/students', tags=['students'])


@router.get('/classes', response_model=List[str])
async def get_unique_classes(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_classes = await crud_students.get_teacher_classes(db, current_user)
    if not db_classes:
        raise HTTPException(status_code=404, detail='Class not found')
    return db_classes


@router.get('/', response_model=List[schemas.Student])
async def read_students(
    admission_year: Optional[int] = None,
    class_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_students.get_students(
        db=db,
        current_user=current_user,
        admission_year=admission_year,
        class_name=class_name,
    )


@router.get('/{student_id}', response_model=schemas.Student)
async def read_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_student = await crud_students.get_student_by_student_id(
        db, student_id, current_user
    )
    if not db_student:
        raise HTTPException(status_code=404, detail='Student not found')
    return db_student


@router.post('/', response_model=schemas.Student, status_code=status.HTTP_201_CREATED)
async def create_new_student(
    student: schemas.StudentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_students.create_student(db, student, current_user)


@router.put('/{student_id}', response_model=schemas.Student)
async def update_existing_student(
    student_id: str,
    student_in: schemas.StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Retrieve the existing student first
    db_student = await crud_students.get_student_by_student_id(
        db, student_id, current_user
    )
    if not db_student:
        raise HTTPException(status_code=404, detail='Student not found')

    # Attempt to update it
    updated_student = await crud_students.update_student(
        db, db_student, student_in, current_user
    )

    # Check if ownership validation failed
    if not updated_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not authorized to update this student',
        )

    return updated_student


@router.delete('/{student_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Retrieve the existing student first
    db_student = await crud_students.get_student_by_student_id(
        db, student_id, current_user
    )
    if not db_student:
        raise HTTPException(status_code=404, detail='Student not found')

    # Attempt to delete it
    success = await crud_students.delete_student(db, db_student, current_user)

    # Check if ownership validation failed
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not authorized to delete this student',
        )
