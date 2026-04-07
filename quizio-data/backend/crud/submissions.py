from typing import List

import models
import schemas
from sqlalchemy.ext.asyncio import AsyncSession


async def create_student_submission(
    db: AsyncSession, submission_in: schemas.StudentSubmissionCreate
) -> models.StudentSubmission:
    # Create the main submission record
    db_submission = models.StudentSubmission(
        exam_id=submission_in.exam_id,
        student_id=submission_in.student_id,
        guest_name=submission_in.guest_name,
    )
    db.add(db_submission)

    # Flush to get the generated db_submission.id without committing the transaction
    await db.flush()

    # Create associated student answers
    for answer_in in submission_in.answers:
        db_answer = models.StudentAnswer(
            submission_id=db_submission.id,
            exam_id=submission_in.exam_id,
            question_id=answer_in.question_id,
            answer_content=answer_in.answer_content,
            is_correct=answer_in.is_correct,
            score=answer_in.score,
        )
        db.add(db_answer)

    # Commit all changes as a single transaction
    await db.commit()

    # Refresh to load the relationships (answers) for the response model
    await db.refresh(db_submission, ['answers'])

    return db_submission


async def create_submissions_batch(
    db: AsyncSession, submissions_in: List[schemas.StudentSubmissionCreate]
) -> dict:
    """
    Process multiple student submissions in a single database transaction.
    """
    new_submissions = []

    # 1. Add all submission records to the session
    for sub_in in submissions_in:
        db_sub = models.StudentSubmission(
            exam_id=sub_in.exam_id,
            student_id=sub_in.student_id,
            guest_name=sub_in.guest_name,
        )
        db.add(db_sub)
        new_submissions.append((db_sub, sub_in.answers))

    # 2. Flush to generate IDs for all db_sub instances without committing
    await db.flush()

    # 3. Add all related answers using the newly generated submission IDs
    for db_sub, answers_in in new_submissions:
        for ans_in in answers_in:
            db_ans = models.StudentAnswer(
                submission_id=db_sub.id,
                exam_id=db_sub.exam_id,
                question_id=ans_in.question_id,
                answer_content=ans_in.answer_content,
                is_correct=ans_in.is_correct,
                score=ans_in.score,
            )
            db.add(db_ans)

    # 4. Commit everything as a single transaction
    await db.commit()

    return {'status': 'success', 'processed_count': len(submissions_in)}
