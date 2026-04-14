// ---------------------------------------------------------
// Payloads sent FROM Screen TO Server
// ---------------------------------------------------------
export interface ScreenJoinRoomPayload {
    room_pin: string
}

// ---------------------------------------------------------
// Payloads sent FROM Server TO Screen (and sometimes Host)
// ---------------------------------------------------------
export interface DisplayQuestionPayload {
    question: any | null
    display_state: string
    pinned_answer: any | null
}

export interface UpdateStatsPayload {
    stats: any // We will strictly type this when doing Wordcloud!
    total: number
}

export interface ShowLeaderboardPayload {
    leaderboard: any[]
}

export interface UpdatePinnedAnswerPayload {
    pinned_answer: any | null
}

// ---------------------------------------------------------
// Shared Payloads (Server TO All)
// ---------------------------------------------------------
export interface ErrorPayload {
    message: string
}

export interface RoomStatePayload {
    room_pin: string
    players: string[]
    player_stats: {
        student_count: number
        guest_count: number
        total_count: number
    }
}
