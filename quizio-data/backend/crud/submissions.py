from datetime import date
from typing import List, Optional

import models
import schemas
from sqlalchemy import and_, func, select
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


async def get_grade_report(
    db: AsyncSession,
    teacher_id: int,
    class_name: Optional[str] = None,
    student_id_str: Optional[str] = None,
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
):
    # 1. 篩選該老師的考試 (依日期區間)
    exam_query = select(models.Exam).where(models.Exam.owner_id == teacher_id)
    if date_start:
        exam_query = exam_query.where(models.Exam.target_date >= date_start)
    if date_end:
        exam_query = exam_query.where(models.Exam.target_date <= date_end)

    exam_result = await db.execute(exam_query)
    exams = exam_result.scalars().all()
    exam_ids = [e.id for e in exams]

    if not exam_ids:
        return {'exams': [], 'students': []}

    # 2. 篩選該老師的學生 (依班級或學號)
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
        return {'exams': exams, 'students': []}

    # 3. 聚合查詢：計算每個學生在每場考試的總分
    # Join Submission 與 Answer，並依據 student_id 與 exam_id 分組
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
        .where(
            and_(
                models.StudentSubmission.exam_id.in_(exam_ids),
                models.StudentSubmission.student_id.in_(student_db_ids),
            )
        )
        .group_by(models.StudentSubmission.student_id, models.StudentSubmission.exam_id)
    )

    score_result = await db.execute(score_query)
    raw_scores = score_result.all()

    # 4. 整理成樞紐分析需要的結構
    # 建立一個 score_map: {(student_id, exam_id): score}
    score_map = {(row.student_id, row.exam_id): row.total_score for row in raw_scores}

    student_entries = []
    for s in students:
        s_scores = {}
        for e_id in exam_ids:
            # 如果沒參加該場考試，預設給 0 或 null，這裡採預設 0
            s_scores[str(e_id)] = score_map.get((s.id, e_id), 0)

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
