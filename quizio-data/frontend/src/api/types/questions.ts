export interface QuestionResponse {
    id: number
    owner_id: number
    type: 'single' | 'boolean' | 'multiple' | 'short' | 'essay'
    difficulty: number | null
    lesson: string | null
    content: string
    options: string[] | null
    reference_answer: boolean | number | string | number[]
    literacy_tags: string[] | null
    is_public: boolean
    needs_manual_grading: boolean
    is_locked: boolean
    is_archived: boolean
    deleted_at?: string | null
    created_at: string
    updated_at: string
}

export interface QuestionsGet {
    question_type?: string | null
    difficulty?: number | null
    lesson?: string | null
    is_locked?: boolean | null
    is_archived?: boolean | null
    is_deleted?: boolean | null
}

export interface QuestionCreate {
    type: 'single' | 'boolean' | 'multiple' | 'short' | 'essay'
    difficulty: number | null
    lesson: string | null
    content: string
    options: string[] | null
    reference_answer: boolean | number | string | number[]
    literacy_tags: string[] | null
    is_public: boolean
    needs_manual_grading: boolean
}

export interface QuestionUpdate {
    type: 'single' | 'boolean' | 'multiple' | 'short' | 'essay'
    difficulty: number | null
    lesson: string | null
    content: string
    options: string[] | null
    reference_answer: boolean | number | string | number[]
    literacy_tags: string[] | null
    is_public: boolean
    needs_manual_grading: boolean
}
