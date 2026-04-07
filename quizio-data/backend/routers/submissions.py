from typing import List

import models
import schemas
from core.deps import get_current_user
from crud import submissions as crud_submissions
from database import get_db
from fastapi import APIRouter, Depends, status
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
    # Require authentication to ensure only authorized backend calls can submit data
    current_user: models.User = Depends(get_current_user),
):
    """
    Receive student submissions and answers from the game-backend
    when a quiz room is closed.
    """
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
    return await crud_submissions.create_submissions_batch(db, submissions)
