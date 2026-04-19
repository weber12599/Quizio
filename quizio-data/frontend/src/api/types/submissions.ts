import type { QuestionResponse } from './questions'

export interface StudentAnswerResponse {
    id: number
    submission_id: number
    exam_id: number
    question_id: number
    answer_content?: string | null
    is_correct?: boolean | null
    score?: number | null
    created_at: string
    question?: QuestionResponse | null
}

export interface StudentSubmissionResponse {
    id: number
    exam_id: number
    student_id?: number | null
    guest_name?: string | null
    record_at: string
    created_at: string
    answers: StudentAnswerResponse[]
}

export interface SubmissionScoreDetail {
    submission_id: number
    score: number
    record_at: string
}

export interface ExamGradeHeader {
    id: number
    title: string
    target_date?: string | null
    max_attempts: number
}

export interface StudentGradeEntry {
    student_db_id?: number | null
    student_id: string
    name: string
    class_name?: string | null
    exam_submissions: Record<string, SubmissionScoreDetail[]>
}

export interface GradeReportResponse {
    exams: ExamGradeHeader[]
    students: StudentGradeEntry[]
}

export interface GetGradeReport {
    class_name?: string
    student_id?: string
    date_start?: string
    date_end?: string
    exam_ids?: number[]
}

export interface AnswerGradingHistoryResponse {
    id: number
    answer_id: number
    old_score?: number | null
    new_score?: number | null
    teacher_id?: number | null
    created_at: string
}
