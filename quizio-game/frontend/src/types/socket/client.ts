// ---------------------------------------------------------
// Payloads sent FROM Client TO Server
// ---------------------------------------------------------
export interface ClientJoinRoomPayload {
    room_pin: string
    is_guest?: boolean
    guest_name?: string | null
    player_id?: string | null
    student_id?: string | null
    password?: string | null
}

export interface SubmitAnswerPayload {
    room_pin: string
    question_id: number
    answer: string | number | number[] | null
}

// ---------------------------------------------------------
// Payloads sent FROM Server TO Client
// ---------------------------------------------------------
export interface AuthSuccessPayload {
    upload_token?: string
    player_id?: string
}

// ---------------------------------------------------------
// Interaction payloads (Client -> Server)
// ---------------------------------------------------------
export interface LikeAnswerPayload {
    room_pin: string
    question_id: number
    answer_owner_id: string
}

export interface CommentAnswerPayload {
    room_pin: string
    question_id: number
    answer_owner_id: string
    content: string
}

// ---------------------------------------------------------
// Interaction payloads (Server -> Client)
// ---------------------------------------------------------
export interface PeerAnswersPayload {
    question_id: number
    answers: Array<{
        player_id: string
        name: string
        is_guest: boolean
        answer: any
        question_id: number
    }>
}

export interface InteractionUpdatePayload {
    question_id: number
    answer_owner_id: string
    answer_interactions: {
        likes: Array<{ from_id: string; name: string }>
        comments: Array<{
            id: string
            from_id: string
            name: string
            content: string
            is_host?: boolean
        }>
    }
}

export interface NewQuestionsPayload {
    questions: any[] // Consider typing Question if a common interface exists
}

export interface RecoveredAnswersPayload {
    answers: Record<string, any>
    gradings: Record<string, any>
}
