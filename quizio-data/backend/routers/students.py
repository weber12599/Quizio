from typing import List, Optional

import crud
import schemas
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status

# Import the oauth2_scheme we just created in auth.py
from routers.auth import oauth2_scheme
from sqlalchemy.ext.asyncio import AsyncSession

# Add the dependency here to protect ALL routes in this router
# This will also make the "lock" icon appear next to these endpoints in Swagger UI
router = APIRouter(
    prefix='/api/students', tags=['students'], dependencies=[Depends(oauth2_scheme)]
)


@router.get('', response_model=List[schemas.StudentOut])
async def read_students(
    admission_year: Optional[int] = None,
    class_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_students(
        db, admission_year=admission_year, class_name=class_name
    )


@router.post('', response_model=schemas.StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(
    student: schemas.StudentCreate, db: AsyncSession = Depends(get_db)
):
    db_student = await crud.get_student_by_student_id(db, student_id=student.student_id)
    if db_student:
        raise HTTPException(status_code=400, detail='Student ID already registered')
    return await crud.create_student(db=db, student=student)


@router.put('/{student_id}', response_model=schemas.StudentOut)
async def update_student(
    student_id: str,
    student_update: schemas.StudentUpdate,
    db: AsyncSession = Depends(get_db),
):
    db_student = await crud.get_student_by_student_id(db, student_id=student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail='Student not found')
    return await crud.update_student(
        db=db, db_student=db_student, student_update=student_update
    )


@router.delete('/{student_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(student_id: str, db: AsyncSession = Depends(get_db)):
    db_student = await crud.get_student_by_student_id(db, student_id=student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail='Student not found')
    await crud.delete_student(db=db, db_student=db_student)
