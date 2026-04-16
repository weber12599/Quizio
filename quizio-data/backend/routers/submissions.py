from datetime import date, datetime, timezone
from typing import List, Optional

import models
import schemas
from core.deps import get_current_user
from crud import exams as crud_exams
from crud import submissions as crud_submissions
from database import get_db
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix='/api/submissions', tags=['submissions'])

# ==========================================
# Dependencies
# ==========================================


async def get_answer_rwd(
    answer_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.StudentAnswer:
    db_answer = await crud_submissions.get_student_answer(db, answer_db_id)
    if not db_answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Student answer not found'
        )

    if not current_user.is_superuser and db_answer.exam.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only grade answers for exams you created.',
        )
    return db_answer


async def get_submission_r(
    submission_db_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.StudentSubmission:
    db_submission = await crud_submissions.get_student_submission_details(
        db, submission_db_id
    )
    if not db_submission:
        raise HTTPException(status_code=404, detail='Submission not found')

    if not current_user.is_superuser and db_submission.exam.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not have permission to view the details of this exam.',
        )
    return db_submission


@router.post(
    '/',
    response_model=schemas.StudentSubmission,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_submission(
    submission: schemas.StudentSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_exam = await crud_exams.get_exam(db, submission.exam_id, current_user)
    if not db_exam:
        raise HTTPException(status_code=404, detail='Exam not found.')
    if not db_exam.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Cannot submit grades for an unlocked (draft) exam.',
        )

    return await crud_submissions.create_student_submission(db, submission)


@router.post('/batch', status_code=status.HTTP_201_CREATED)
async def create_new_submission_batch(
    submissions: List[schemas.StudentSubmissionCreate],
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not submissions:
        return await crud_submissions.create_submissions_batch(db, submissions)

    unified_time = datetime.now(timezone.utc)
    for sub in submissions:
        sub.record_at = unified_time

    exam_ids = {sub.exam_id for sub in submissions}

    for e_id in exam_ids:
        db_exam = await crud_exams.get_exam(db, e_id, current_user)
        if not db_exam:
            raise HTTPException(status_code=404, detail=f'Exam {e_id} not found.')
        if not db_exam.is_locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Cannot submit grades for an unlocked exam (ID: {e_id}).',
            )

    return await crud_submissions.create_submissions_batch(db, submissions)


@router.put('/answers/{answer_db_id}/grade', response_model=schemas.StudentAnswer)
async def grade_student_answer(
    score: int = Body(..., embed=True),
    db_answer: models.StudentAnswer = Depends(get_answer_rwd),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_submissions.grade_student_answer(
        db, db_answer, score, current_user
    )


@router.get('/', response_model=schemas.GradeReportResponse)
async def read_submissions_report(
    class_name: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    date_start: Optional[date] = Query(None),
    date_end: Optional[date] = Query(None),
    exam_ids: Optional[List[int]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await crud_submissions.get_grade_report(
        db=db,
        teacher_id=current_user.id,
        class_name=class_name,
        student_id_str=student_id,
        date_start=date_start,
        date_end=date_end,
        exam_ids=exam_ids,
    )


@router.get('/{submission_db_id}', response_model=schemas.StudentSubmission)
async def read_student_submission_details(
    db_submission: models.StudentSubmission = Depends(get_submission_r),
):
    return db_submission
