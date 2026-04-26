from collections import defaultdict
from datetime import date
from typing import List, Optional

import models
import schemas
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, contains_eager


async def get_manual_grading_question_ids(db: AsyncSession, question_ids: set) -> set:
    """
    Helper function to fetch IDs of questions that require manual grading.
    """
    if not question_ids:
        return set()

    result = await db.execute(
        select(models.Question.id)
        .where(models.Question.id.in_(question_ids))
        .where(models.Question.needs_manual_grading.is_(True))
    )
    return set(result.scalars().all())


async def get_student_answer(db: AsyncSession, answer_db_id: int):
    result = await db.execute(
        select(models.StudentAnswer)
        .options(
            selectinload(models.StudentAnswer.grading_histories),
            selectinload(models.StudentAnswer.question),
            selectinload(models.StudentAnswer.exam),
        )
        .where(models.StudentAnswer.id == answer_db_id)
    )
    return result.scalar_one_or_none()


async def create_student_submission(
    db: AsyncSession, submission_in: schemas.StudentSubmissionCreate
) -> models.StudentSubmission:
    sub_data = {
        'exam_id': submission_in.exam_id,
        'student_id': submission_in.student_id,
        'guest_name': submission_in.guest_name,
    }
    if submission_in.record_at is not None:
        sub_data['record_at'] = submission_in.record_at

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
            'record_at': sub_in.record_at,
        }

        db_sub = models.StudentSubmission(**sub_data)
        db.add(db_sub)
        new_submissions.append((db_sub, sub_in.answers))

    await db.flush()

    # 2. Identify questions requiring manual grading across the whole batch
    all_q_ids = {ans.question_id for sub in submissions_in for ans in sub.answers}
    manual_q_ids = await get_manual_grading_question_ids(db, all_q_ids)

    # 3. Add all related answers applying manual grading rules
    all_db_answers: List[tuple[models.StudentAnswer, models.StudentSubmission]] = []
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
            all_db_answers.append((db_ans, db_sub))

    # Flush so all answer IDs are populated before commit
    await db.flush()

    answer_ids = [
        {
            'student_id': db_sub.student_id,
            'guest_name': db_sub.guest_name,
            'question_id': db_ans.question_id,
            'answer_id': db_ans.id,
            'submission_id': db_sub.id,
        }
        for db_ans, db_sub in all_db_answers
    ]

    await db.commit()
    return {
        'status': 'success',
        'processed_count': len(submissions_in),
        'answer_ids': answer_ids,
    }


async def grade_student_answer(
    db: AsyncSession,
    db_answer: models.StudentAnswer,
    new_score: int,
    current_user: models.User,
) -> Optional[models.StudentAnswer]:
    """
    Manually update a student's answer score and record the grading history.
    """
    # Record the history before changing the score
    history = models.AnswerGradingHistory(
        answer_id=db_answer.id,
        old_score=db_answer.score,
        new_score=new_score,
        teacher_id=current_user.id,
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

    # 1. 依據「每一次的 submission_id」進行分組與加總
    score_query = (
        select(
            models.StudentSubmission.id.label('submission_id'),
            models.StudentSubmission.student_id,
            models.StudentSubmission.exam_id,
            models.StudentSubmission.record_at,
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
            func.date(models.StudentSubmission.record_at) >= date_start
        )
    if date_end:
        score_query = score_query.where(
            func.date(models.StudentSubmission.record_at) <= date_end
        )

    score_query = score_query.group_by(
        models.StudentSubmission.id,
        models.StudentSubmission.student_id,
        models.StudentSubmission.exam_id,
        models.StudentSubmission.record_at,
        models.StudentSubmission.created_at,  # 必須加入 group_by 避免 SQL 報錯
    ).order_by(
        models.StudentSubmission.created_at.asc()
    )  # 依時間遞增，確保 1, 2, 3 次順序正確

    score_result = await db.execute(score_query)
    raw_scores = score_result.all()

    # 2. 統計每張考卷的最大作答次數與學生作答紀錄
    exam_attempts_count = defaultdict(int)
    student_exam_subs = defaultdict(lambda: defaultdict(list))

    for row in raw_scores:
        sub_score = row.total_score if row.total_score is not None else 0
        student_exam_subs[row.student_id][row.exam_id].append(
            {
                'submission_id': row.submission_id,
                'score': sub_score,
                'record_at': row.record_at,
            }
        )

    for s_id, exams_dict in student_exam_subs.items():
        for e_id, subs in exams_dict.items():
            if len(subs) > exam_attempts_count[e_id]:
                exam_attempts_count[e_id] = len(subs)

    active_exam_ids = list(exam_attempts_count.keys())
    if not active_exam_ids:
        return {'exams': [], 'students': []}

    exam_result = await db.execute(
        select(models.Exam).where(models.Exam.id.in_(active_exam_ids))
    )
    exams = exam_result.scalars().all()

    # 3. 組合回傳資料
    exams_data = []
    for e in exams:
        exams_data.append(
            {
                'id': e.id,
                'title': e.title,
                'target_date': e.target_date,
                'max_attempts': exam_attempts_count[e.id],
            }
        )

    student_entries = []
    for s in students:
        s_submissions = {}
        for e_id in active_exam_ids:
            s_submissions[str(e_id)] = student_exam_subs[s.id][e_id]

        student_entries.append(
            {
                'student_db_id': s.id,
                'student_id': s.student_id,
                'name': s.name,
                'class_name': s.class_name,
                'exam_submissions': s_submissions,
            }
        )

    return {'exams': exams_data, 'students': student_entries}


async def create_batch_interactions(
    db: AsyncSession,
    host_user_id: int,
    payload: schemas.InteractionBatchPayload,
) -> None:
    def resolve_author(author: schemas.InteractionAuthor) -> dict:
        if author.is_host:
            return {'user_id': host_user_id, 'student_id': None, 'guest_name': None}
        if author.student_id is not None:
            return {'student_id': author.student_id, 'user_id': None, 'guest_name': None}
        return {'guest_name': author.guest_name, 'student_id': None, 'user_id': None}

    # Per-answer interactions (short / essay)
    for item in payload.answer_interactions:
        db_comments: List[tuple[models.InteractionComment, schemas.CommentCreate]] = []
        for comment_in in item.comments:
            db_comment = models.InteractionComment(
                answer_id=item.answer_id,
                content=comment_in.content,
                **resolve_author(comment_in.author),
            )
            db.add(db_comment)
            db_comments.append((db_comment, comment_in))

        if db_comments:
            await db.flush()

        for db_comment, comment_in in db_comments:
            for like_in in comment_in.comment_likes:
                db.add(models.InteractionLike(
                    comment_id=db_comment.id,
                    **resolve_author(like_in.author),
                ))

        for like_author in item.answer_likes:
            db.add(models.InteractionLike(
                answer_id=item.answer_id,
                **resolve_author(like_author),
            ))

    # Per-option interactions (single / multiple / boolean)
    # All option-level rows share the session anchor submission_id so the
    # read endpoint can scope them to a specific game session.
    anchor = payload.session_anchor_submission_id
    for item in payload.option_interactions:
        if anchor is None:
            # Without an anchor, option interactions cannot be scoped to a
            # session — skip them rather than orphan the rows.
            continue

        db_comments = []
        for comment_in in item.comments:
            db_comment = models.InteractionComment(
                question_id=item.question_id,
                option_index=item.option_index,
                submission_id=anchor,
                content=comment_in.content,
                **resolve_author(comment_in.author),
            )
            db.add(db_comment)
            db_comments.append((db_comment, comment_in))

        if db_comments:
            await db.flush()

        for db_comment, comment_in in db_comments:
            for like_in in comment_in.comment_likes:
                db.add(models.InteractionLike(
                    comment_id=db_comment.id,
                    **resolve_author(like_in.author),
                ))

        for like_author in item.option_likes:
            db.add(models.InteractionLike(
                question_id=item.question_id,
                option_index=item.option_index,
                submission_id=anchor,
                **resolve_author(like_author),
            ))

    await db.commit()


async def get_session_interactions(
    db: AsyncSession,
    submission_id: int,
    teacher_id: int,
) -> List[schemas.QuestionInteractionRead]:
    # Load the target submission to get exam_id and record_at
    sub_result = await db.execute(
        select(models.StudentSubmission).where(
            models.StudentSubmission.id == submission_id
        )
    )
    target_sub = sub_result.scalar_one_or_none()
    if not target_sub:
        return []

    # Load all submissions in this session with answer-level interaction data
    result = await db.execute(
        select(models.StudentSubmission)
        .options(
            selectinload(models.StudentSubmission.student),
            selectinload(models.StudentSubmission.answers).options(
                selectinload(models.StudentAnswer.question),
                selectinload(models.StudentAnswer.comments).options(
                    selectinload(models.InteractionComment.student),
                    selectinload(models.InteractionComment.user),
                    selectinload(models.InteractionComment.likes).options(
                        selectinload(models.InteractionLike.student),
                        selectinload(models.InteractionLike.user),
                    ),
                ),
                selectinload(models.StudentAnswer.likes).options(
                    selectinload(models.InteractionLike.student),
                    selectinload(models.InteractionLike.user),
                ),
            ),
        )
        .where(models.StudentSubmission.exam_id == target_sub.exam_id)
        .where(models.StudentSubmission.record_at == target_sub.record_at)
    )
    submissions = result.scalars().all()
    session_submission_ids = [s.id for s in submissions]

    # Build per-question entry: meta (type/options/title) + answers list
    question_map: dict = {}
    for sub in submissions:
        if sub.student_id:
            sub_author = {'role': 'student', 'id': str(sub.student_id), 'name': sub.student.name if sub.student else 'Unknown'}
        else:
            sub_author = {'role': 'guest', 'id': sub.guest_name or '', 'name': sub.guest_name or ''}

        for ans in sub.answers:
            if ans.question_id not in question_map:
                q = ans.question
                question_map[ans.question_id] = {
                    'question_id': ans.question_id,
                    'question_title': q.content if q else '',
                    'question_type': q.type if q else '',
                    'question_options': q.options if q else None,
                    'answers': [],
                    'options': [],
                }

            answer_likes = [
                {'id': like.id, 'author': like.author_info}
                for like in ans.likes
                if like.deleted_at is None
            ]
            comments = []
            for comment in ans.comments:
                if comment.deleted_at is not None:
                    continue
                comment_likes = [
                    {'id': cl.id, 'author': cl.author_info}
                    for cl in comment.likes
                    if cl.deleted_at is None
                ]
                comments.append({
                    'id': comment.id,
                    'content': comment.content,
                    'author': comment.author_info,
                    'created_at': comment.created_at,
                    'comment_likes': comment_likes,
                })

            question_map[ans.question_id]['answers'].append({
                'answer_id': ans.id,
                'submission_id': sub.id,
                'answer_content': ans.answer_content,
                'author': sub_author,
                'answer_likes': answer_likes,
                'comments': comments,
            })

    # Load option-level comments for this session, with author and like data
    if session_submission_ids:
        opt_comments_result = await db.execute(
            select(models.InteractionComment)
            .options(
                selectinload(models.InteractionComment.student),
                selectinload(models.InteractionComment.user),
                selectinload(models.InteractionComment.likes).options(
                    selectinload(models.InteractionLike.student),
                    selectinload(models.InteractionLike.user),
                ),
            )
            .where(models.InteractionComment.submission_id.in_(session_submission_ids))
            .where(models.InteractionComment.option_index.is_not(None))
            .where(models.InteractionComment.deleted_at.is_(None))
        )
        opt_comments = opt_comments_result.scalars().all()

        opt_likes_result = await db.execute(
            select(models.InteractionLike)
            .options(
                selectinload(models.InteractionLike.student),
                selectinload(models.InteractionLike.user),
            )
            .where(models.InteractionLike.submission_id.in_(session_submission_ids))
            .where(models.InteractionLike.option_index.is_not(None))
            .where(models.InteractionLike.deleted_at.is_(None))
        )
        opt_likes = opt_likes_result.scalars().all()

        # Group by (question_id, option_index)
        opt_map: dict = {}

        def get_opt_entry(q_id: int, idx: int) -> dict:
            key = (q_id, idx)
            if key not in opt_map:
                # Fetch option text from question entry if available
                opt_text = ''
                q_entry = question_map.get(q_id)
                if q_entry and q_entry.get('question_options'):
                    opts = q_entry['question_options']
                    if isinstance(opts, list) and 0 <= idx < len(opts):
                        opt_text = opts[idx]
                opt_map[key] = {
                    'option_index': idx,
                    'option_text': opt_text,
                    'option_likes': [],
                    'comments': [],
                }
            return opt_map[key]

        for c in opt_comments:
            entry = get_opt_entry(c.question_id, c.option_index)
            comment_likes = [
                {'id': cl.id, 'author': cl.author_info}
                for cl in c.likes
                if cl.deleted_at is None
            ]
            entry['comments'].append({
                'id': c.id,
                'content': c.content,
                'author': c.author_info,
                'created_at': c.created_at,
                'comment_likes': comment_likes,
            })

        for like in opt_likes:
            entry = get_opt_entry(like.question_id, like.option_index)
            entry['option_likes'].append({'id': like.id, 'author': like.author_info})

        # Attach option entries to their question_map entries (creating an
        # entry for questions that have only option-level activity).
        for (q_id, idx), entry in opt_map.items():
            if q_id not in question_map:
                # Question wasn't covered by any answers in the session
                # (rare — happens if no student answered it). Load it lazily.
                q_result = await db.execute(
                    select(models.Question).where(models.Question.id == q_id)
                )
                q = q_result.scalar_one_or_none()
                question_map[q_id] = {
                    'question_id': q_id,
                    'question_title': q.content if q else '',
                    'question_type': q.type if q else '',
                    'question_options': q.options if q else None,
                    'answers': [],
                    'options': [],
                }
                if q and q.options and 0 <= idx < len(q.options):
                    entry['option_text'] = q.options[idx]
            question_map[q_id]['options'].append(entry)

        # Sort each question's options by option_index for stable rendering
        for entry in question_map.values():
            entry['options'].sort(key=lambda o: o['option_index'])

    return list(question_map.values())


async def update_discussion_score(
    db: AsyncSession,
    submission_id: int,
    score: Optional[int],
) -> Optional[models.StudentSubmission]:
    result = await db.execute(
        select(models.StudentSubmission).where(
            models.StudentSubmission.id == submission_id
        )
    )
    db_sub = result.scalar_one_or_none()
    if not db_sub:
        return None
    db_sub.discussion_score = score
    await db.commit()
    await db.refresh(db_sub)
    return db_sub


async def get_student_submission_details(db: AsyncSession, submission_id: int):
    query = (
        select(models.StudentSubmission)
        .options(
            selectinload(models.StudentSubmission.answers).selectinload(
                models.StudentAnswer.question
            ),
            selectinload(models.StudentSubmission.exam).selectinload(
                models.Exam.exam_questions
            ),
        )
        .where(models.StudentSubmission.id == submission_id)
    )
    result = await db.execute(query)
    submission = result.scalar_one_or_none()

    if submission:
        sort_map = {
            eq.question_id: eq.sort_order for eq in submission.exam.exam_questions
        }
        submission.answers.sort(key=lambda ans: sort_map.get(ans.question_id, 999))
    return submission
