from typing import Optional

import models
import schemas
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


# Get a single student by ID (primary key) with data isolation
async def get_student(db: AsyncSession, student_db_id: int, current_user: models.User):
    query = select(models.Student).where(models.Student.id == student_db_id)

    # Data isolation: Regular teachers can only view their own students
    if not current_user.is_superuser:
        query = query.where(models.Student.teacher_id == current_user.id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


# Get a single student by student ID with data isolation (for login/lookup)
async def get_student_by_student_id(
    db: AsyncSession, student_id: str, current_user: models.User
):
    # Prevent soft-deleted students from logging in or being looked up
    query = select(models.Student).where(
        models.Student.student_id == student_id, models.Student.deleted_at.is_(None)
    )

    # Data isolation: Regular teachers can only view their own students
    if not current_user.is_superuser:
        query = query.where(models.Student.teacher_id == current_user.id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


# Get classes belong to the teacher
async def get_teacher_classes(
    db: AsyncSession,
    current_user: models.User,
):
    # Filter out deleted students so empty classes don't show up
    query = select(models.Student.class_name).where(models.Student.deleted_at.is_(None))

    # Data isolation: Regular teachers can only view their own students
    if not current_user.is_superuser:
        query = query.where(models.Student.teacher_id == current_user.id)

    query = query.where(models.Student.class_name.is_not(None)).distinct()

    result = await db.execute(query)
    return [row[0] for row in result.all() if row[0]]


# Get multiple students with optional filters and data isolation
async def get_students(
    db: AsyncSession,
    current_user: models.User,
    admission_year: Optional[int] = None,
    class_name: Optional[str] = None,
    is_deleted: Optional[bool] = None,
):
    query = select(models.Student)

    if not current_user.is_superuser:
        query = query.where(models.Student.teacher_id == current_user.id)

    if is_deleted is not None:
        query = (
            query.where(models.Student.deleted_at.is_not(None))
            if is_deleted
            else query.where(models.Student.deleted_at.is_(None))
        )

    if admission_year is not None:
        query = query.where(models.Student.admission_year == admission_year)

    if class_name is not None:
        query = query.where(models.Student.class_name == class_name)

    query = query.order_by(
        models.Student.admission_year.desc(),
        models.Student.class_name,
        models.Student.student_id,
    )
    result = await db.execute(query)
    return result.scalars().all()


# Create a new student
async def create_student(
    db: AsyncSession, student: schemas.StudentCreate, current_user: models.User
):
    student_data = student.model_dump()
    student_data['teacher_id'] = current_user.id

    db_student = models.Student(**student_data)
    db.add(db_student)
    await db.flush()  # Flush to get the generated student ID

    await db.commit()
    return await get_student(db, db_student.id, current_user)


# Update an existing student
async def update_student(
    db: AsyncSession,
    db_student: models.Student,
    student_update: schemas.StudentUpdate,
    current_user: models.User,
):
    # Core defense: Once deleted, a student cannot be modified
    if db_student.deleted_at is not None:
        raise ValueError('Cannot modify a protected student.')

    # Security check: Only the owner or a superuser can modify the student
    if not current_user.is_superuser and db_student.teacher_id != current_user.id:
        raise ValueError('Unauthorized access to the student.')

    update_data = student_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        # Prevent empty password updates
        if key == 'password' and not value:
            continue
        setattr(db_student, key, value)

    await db.commit()
    return await get_student(db, db_student.id, current_user)


# Soft delete a student
async def toggle_delete_student(
    db: AsyncSession,
    db_student: models.Student,
    is_deleted: bool,
    current_user: models.User,
):
    current_is_deleted = db_student.deleted_at is not None
    if not (current_is_deleted ^ is_deleted):
        return db_student

    db_student.deleted_at = func.now() if is_deleted else None
    await db.commit()
    return await get_student(db, db_student.id, current_user)
