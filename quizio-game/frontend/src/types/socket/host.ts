// ---------------------------------------------------------
// Payloads sent FROM Host TO Server
// ---------------------------------------------------------
export interface HostJoinRoomPayload {
    room_pin: string
    token: string
    exam_id: number
    target_class?: string | null
    allow_guests?: boolean
    expected_students?: string[]
}

export interface HostBroadcastQuestionsPayload {
    room_pin: string
    questions: any[]
}

export interface HostDisplayQuestionPayload {
    room_pin: string
    question: any | null
    display_state?: string // 'question' | 'stats' | 'answer' | 'lobby'
}

export interface HostPinAnswerPayload {
    room_pin: string
    question_id: number
    pinned_answer: any | null
}

export interface HostShowLeaderboardPayload {
    room_pin: string
}

export interface EndGamePayload {
    room_pin: string
}

// ---------------------------------------------------------
// Payloads sent FROM Server TO Host
// ---------------------------------------------------------
export interface HostRecoveredStatePayload {
    broadcasted_ids: number[]
    displayed_question_id: number | null
    display_state: string
    is_leaderboard_displayed: boolean
    pinned_answer: any | null
}

export interface ClientInfo {
    name: string
    is_guest: boolean
    is_online: boolean
}

export interface HostRoomStatsPayload {
    target_class: string | null
    allow_guests: boolean
    expected_students: string[]
    answers: Record<string, Record<string, any>>
    gradings: Record<string, Record<string, any>>
    clients_info: Record<string, ClientInfo>
}
