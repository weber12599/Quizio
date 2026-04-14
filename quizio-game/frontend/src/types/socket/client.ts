// ---------------------------------------------------------
// Payloads sent FROM Client TO Server
// ---------------------------------------------------------
export interface ClientJoinRoomPayload {
    room_pin: string
    is_guest?: boolean
    guest_name?: string | null
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
}

export interface NewQuestionsPayload {
    questions: any[] // Consider typing Question if a common interface exists
}

export interface RecoveredAnswersPayload {
    answers: Record<string, any>
    gradings: Record<string, any>
}
