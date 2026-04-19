import type { QuestionResponse } from './questions'

export interface ExamQuestionSetup {
    question_id: number
    score: number
}

export interface ExamQuestionResponse {
    exam_id: number
    question_id: number
    sort_order: number
    score: number
    question: QuestionResponse
}

export interface ExamResponse {
    id: number
    owner_id: number
    title: string
    description?: string | null
    target_date?: string | null
    is_locked: boolean
    is_archived: boolean
    created_at: string
    updated_at: string
    deleted_at?: string | null
    exam_questions: ExamQuestionResponse[]
}

export interface ExamsGet {
    is_locked?: boolean | null
    is_archived?: boolean | null
    is_deleted?: boolean | null
}

export interface ExamCreate {
    title: string
    description?: string | null
    target_date?: string | null
    questions: ExamQuestionSetup[]
}

export interface ExamUpdate {
    title?: string | null
    description?: string | null
    target_date?: string | null
    questions?: ExamQuestionSetup[] | null
}
