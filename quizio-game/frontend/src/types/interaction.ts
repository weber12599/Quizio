export interface PeerAnswer {
    player_id: string
    name: string
    is_guest: boolean
    answer: any
    question_id: number
}

export interface Like {
    from_id: string
    name: string
}

export interface Comment {
    id: string
    from_id: string
    name: string
    content: string
    is_host?: boolean
    likes: Like[]
}

export interface AnswerInteraction {
    likes: Like[]
    comments: Comment[]
}

// Record<answer_owner_player_id, AnswerInteraction>
export type QuestionInteractions = Record<string, AnswerInteraction>

// Prefix for option-level interaction owner IDs (e.g., 'opt_0', 'opt_1')
export const OPTION_OWNER_PREFIX = 'opt_'
