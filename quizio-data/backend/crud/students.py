import models
import schemas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# Get a single student by ID with data isolation
async def get_student_by_student_id(
    db: AsyncSession, student_id: str, current_user: models.User
):
    query = select(models.Student).where(models.Student.student_id == student_id)

    # Data isolation: Regular teachers can only view their own students
    if not current_user.is_superuser:
        query = query.where(models.Student.teacher_id == current_user.id)

    result = await db.execute(query)
    return result.scalar_one_or_none()


# Get multiple students with optional filters and data isolation
async def get_students(
    db: AsyncSession,
    current_user: models.User,
    admission_year: int = None,
    class_name: str = None,
):
    query = select(models.Student)

    # Data isolation: Regular teachers only see their own students
    if not current_user.is_superuser:
        query = query.where(models.Student.teacher_id == current_user.id)

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

    # Automatically assign the current user as the teacher if not provided
    if student_data.get('teacher_id') is None:
        student_data['teacher_id'] = current_user.id

    db_student = models.Student(**student_data)
    db.add(db_student)
    await db.commit()
    await db.refresh(db_student)
    return db_student


# Update an existing student dynamically with ownership check
async def update_student(
    db: AsyncSession,
    db_student: models.Student,
    student_update: schemas.StudentUpdate,
    current_user: models.User,
):
    # Security check: Only the assigned teacher or a superuser can modify the student
    if not current_user.is_superuser and db_student.teacher_id != current_user.id:
        return None

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


# Delete a student with ownership check
async def delete_student(
    db: AsyncSession, db_student: models.Student, current_user: models.User
):
    # Security check: Only the assigned teacher or a superuser can delete the student
    if not current_user.is_superuser and db_student.teacher_id != current_user.id:
        return False

    await db.delete(db_student)
    await db.commit()
    return True
