from datetime import date
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


@router.post(
    '/',
    response_model=schemas.StudentSubmission,
    status_code=status.HTTP_201_CREATED,
)
async def create_submission(
    submission: schemas.StudentSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Receive student submissions and answers from the game-backend
    when a quiz room is closed.
    """
    # Verify the exam exists and is strictly locked before accepting submissions
    db_exam = await crud_exams.get_exam(db, submission.exam_id, current_user)
    if not db_exam:
        raise HTTPException(status_code=404, detail='Exam not found.')
    if not db_exam.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Cannot submit grades for an unlocked (draft) exam.',
        )

    return await crud_submissions.create_student_submission(db, submission)


@router.post(
    '/batch',
    status_code=status.HTTP_201_CREATED,
)
async def create_submission_batch(
    submissions: List[schemas.StudentSubmissionCreate],
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Receive a batch of student submissions and answers from the game-backend
    when a quiz room is closed.
    """
    if not submissions:
        return await crud_submissions.create_submissions_batch(db, submissions)

    # Gather all unique exam IDs in the batch
    exam_ids = {sub.exam_id for sub in submissions}

    # Verify all involved exams are locked
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


@router.put('/answers/{answer_id}/grade', response_model=schemas.StudentAnswer)
async def grade_student_answer(
    answer_id: int,
    score: int = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Manually grade or override a student's answer score.
    Automatically creates an entry in the grading history ledger.
    """
    try:
        updated_answer = await crud_submissions.grade_student_answer(
            db=db, answer_id=answer_id, new_score=score, teacher_id=current_user.id
        )
    except ValueError as e:
        if str(e) == 'UNAUTHORIZED_GRADING':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You can only grade answers for exams you created.',
            )
        raise e

    if not updated_answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Student answer not found'
        )

    return updated_answer


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
    """
    Retrieve the pivot-table formatted grade report.
    Supports filtering by class, student, exam IDs, and record dates.
    """
    return await crud_submissions.get_grade_report(
        db=db,
        teacher_id=current_user.id,
        class_name=class_name,
        student_id_str=student_id,
        date_start=date_start,
        date_end=date_end,
        exam_ids=exam_ids,
    )


@router.get('/details/{submission_id}', response_model=schemas.StudentSubmission)
async def read_student_submission_details(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Fetch a specific student's submission details for manual grading using its unique ID.
    """
    submission = await crud_submissions.get_student_submission_details(
        db, submission_id
    )
    if not submission:
        raise HTTPException(status_code=404, detail='Submission not found')

    if not current_user.is_superuser and submission.exam.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not have permission to view the details of this exam.',
        )
    return submission
