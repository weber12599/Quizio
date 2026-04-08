from datetime import date
from typing import List, Optional

import models
import schemas
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_manual_grading_question_ids(db: AsyncSession, question_ids: set) -> set:
    """
    Helper function to fetch IDs of questions that require manual grading.
    """
    if not question_ids:
        return set()

    result = await db.execute(
        select(models.Question.id)
        .where(models.Question.id.in_(question_ids))
        .where(models.Question.needs_manual_grading == True)
    )
    return set(result.scalars().all())


async def create_student_submission(
    db: AsyncSession, submission_in: schemas.StudentSubmissionCreate
) -> models.StudentSubmission:
    # Prepare submission data dynamically to handle optional record_date
    sub_data = {
        'exam_id': submission_in.exam_id,
        'student_id': submission_in.student_id,
        'guest_name': submission_in.guest_name,
    }
    if submission_in.record_date:
        sub_data['record_date'] = submission_in.record_date

    db_submission = models.StudentSubmission(**sub_data)
    db.add(db_submission)
    await db.flush()

    # Identify which questions require manual grading to override their scores
    all_q_ids = {ans.question_id for ans in submission_in.answers}
    manual_q_ids = await get_manual_grading_question_ids(db, all_q_ids)

    # Create associated student answers
    for ans_in in submission_in.answers:
        is_manual = ans_in.question_id in manual_q_ids
        db_answer = models.StudentAnswer(
            submission_id=db_submission.id,
            exam_id=submission_in.exam_id,
            question_id=ans_in.question_id,
            answer_content=ans_in.answer_content,
            is_correct=None if is_manual else ans_in.is_correct,
            score=None if is_manual else ans_in.score,
        )
        db.add(db_answer)

    await db.commit()
    await db.refresh(db_submission, ['answers'])
    return db_submission


async def create_submissions_batch(
    db: AsyncSession, submissions_in: List[schemas.StudentSubmissionCreate]
) -> dict:
    new_submissions = []

    # 1. Add all submission records to the session
    for sub_in in submissions_in:
        sub_data = {
            'exam_id': sub_in.exam_id,
            'student_id': sub_in.student_id,
            'guest_name': sub_in.guest_name,
        }
        if sub_in.record_date:
            sub_data['record_date'] = sub_in.record_date

        db_sub = models.StudentSubmission(**sub_data)
        db.add(db_sub)
        new_submissions.append((db_sub, sub_in.answers))

    await db.flush()

    # 2. Identify questions requiring manual grading across the whole batch
    all_q_ids = {ans.question_id for sub in submissions_in for ans in sub.answers}
    manual_q_ids = await get_manual_grading_question_ids(db, all_q_ids)

    # 3. Add all related answers applying manual grading rules
    for db_sub, answers_in in new_submissions:
        for ans_in in answers_in:
            is_manual = ans_in.question_id in manual_q_ids
            db_ans = models.StudentAnswer(
                submission_id=db_sub.id,
                exam_id=db_sub.exam_id,
                question_id=ans_in.question_id,
                answer_content=ans_in.answer_content,
                is_correct=None if is_manual else ans_in.is_correct,
                score=None if is_manual else ans_in.score,
            )
            db.add(db_ans)

    await db.commit()
    return {'status': 'success', 'processed_count': len(submissions_in)}


async def grade_student_answer(
    db: AsyncSession, answer_id: int, new_score: int, teacher_id: int
) -> Optional[models.StudentAnswer]:
    """
    Manually update a student's answer score and record the grading history.
    """
    result = await db.execute(
        select(models.StudentAnswer)
        .options(selectinload(models.StudentAnswer.grading_histories))
        .where(models.StudentAnswer.id == answer_id)
    )
    db_answer = result.scalar_one_or_none()

    if not db_answer:
        return None

    # Record the history before changing the score
    history = models.AnswerGradingHistory(
        answer_id=db_answer.id,
        old_score=db_answer.score,
        new_score=new_score,
        teacher_id=teacher_id,
    )
    db.add(history)

    # Apply the new score
    db_answer.score = new_score

    await db.commit()
    await db.refresh(db_answer)
    return db_answer


async def get_grade_report(
    db: AsyncSession,
    teacher_id: int,
    class_name: Optional[str] = None,
    student_id_str: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    exam_ids: Optional[List[int]] = None,
):
    # 1. Filter target students assigned to the teacher
    student_query = select(models.Student).where(
        models.Student.teacher_id == teacher_id
    )

    if class_name:
        student_query = student_query.where(models.Student.class_name == class_name)
    if student_id_str:
        student_query = student_query.where(models.Student.student_id == student_id_str)

    student_result = await db.execute(student_query)
    students = student_result.scalars().all()
    student_db_ids = [s.id for s in students]

    if not student_db_ids:
        return {'exams': [], 'students': []}

    # 2. Base query for aggregating scores filtered by StudentSubmission's record_date
    score_query = (
        select(
            models.StudentSubmission.student_id,
            models.StudentSubmission.exam_id,
            func.sum(models.StudentAnswer.score).label('total_score'),
        )
        .join(
            models.StudentAnswer,
            models.StudentSubmission.id == models.StudentAnswer.submission_id,
        )
        .where(models.StudentSubmission.student_id.in_(student_db_ids))
    )

    if exam_ids:
        score_query = score_query.where(models.StudentSubmission.exam_id.in_(exam_ids))
    if date_start:
        score_query = score_query.where(
            models.StudentSubmission.record_date >= date_start
        )
    if date_end:
        score_query = score_query.where(
            models.StudentSubmission.record_date <= date_end
        )

    score_query = score_query.group_by(
        models.StudentSubmission.student_id, models.StudentSubmission.exam_id
    )

    score_result = await db.execute(score_query)
    raw_scores = score_result.all()

    # 3. Extract the active exams that actually have submissions within the filtered range
    active_exam_ids = list(set(row.exam_id for row in raw_scores))
    if not active_exam_ids:
        return {'exams': [], 'students': []}

    exam_result = await db.execute(
        select(models.Exam).where(models.Exam.id.in_(active_exam_ids))
    )
    exams = exam_result.scalars().all()

    # 4. Construct the pivot matrix
    score_map = {(row.student_id, row.exam_id): row.total_score for row in raw_scores}

    student_entries = []
    for s in students:
        s_scores = {}
        for e in exams:
            # Insert score or 0 if no record exists
            s_scores[str(e.id)] = score_map.get((s.id, e.id), 0)

        student_entries.append(
            {
                'student_db_id': s.id,
                'student_id': s.student_id,
                'name': s.name,
                'class_name': s.class_name,
                'scores': s_scores,
            }
        )

    return {'exams': exams, 'students': student_entries}
