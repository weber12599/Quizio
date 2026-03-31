import models
import schemas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# Get a single student by ID
async def get_student_by_student_id(db: AsyncSession, student_id: str):
    result = await db.execute(
        select(models.Student).where(models.Student.student_id == student_id)
    )
    return result.scalar_one_or_none()


# Get multiple students with optional filters
async def get_students(
    db: AsyncSession, admission_year: int = None, class_name: str = None
):
    query = select(models.Student)

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
async def create_student(db: AsyncSession, student: schemas.StudentCreate):
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    await db.commit()
    await db.refresh(db_student)
    return db_student


# Update an existing student dynamically
async def update_student(
    db: AsyncSession, db_student: models.Student, student_update: schemas.StudentUpdate
):
    # exclude_unset=True automatically filters out fields that were not explicitly provided
    update_data = student_update.model_dump(exclude_unset=True)

    # Apply updates without repetitive if-statements
    for key, value in update_data.items():
        # Prevent empty password updates
        if key == 'password' and not value:
            continue
        setattr(db_student, key, value)

    await db.commit()
    await db.refresh(db_student)
    return db_student


# Delete a student
async def delete_student(db: AsyncSession, db_student: models.Student):
    await db.delete(db_student)
    await db.commit()
