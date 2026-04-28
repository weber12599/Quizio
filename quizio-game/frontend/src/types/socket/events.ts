export const SocketEvent = {
    // Built-in events
    CONNECT: 'connect',
    DISCONNECT: 'disconnect',

    // Client -> Server (Join events)
    HOST_JOIN_ROOM: 'host_join_room',
    CLIENT_JOIN_ROOM: 'client_join_room',
    SCREEN_JOIN_ROOM: 'screen_join_room',

    // Client -> Server (Action events)
    SUBMIT_ANSWER: 'submit_answer',
    END_GAME: 'end_game',
    HOST_BROADCAST_QUESTIONS: 'host_broadcast_questions',
    HOST_DISPLAY_QUESTION: 'host_display_question',
    HOST_PIN_ANSWER: 'host_pin_answer',
    HOST_SHOW_LEADERBOARD: 'host_show_leaderboard',

    // Interaction events (Client / Host -> Server)
    LIKE_ANSWER: 'like_answer',
    UNLIKE_ANSWER: 'unlike_answer',
    COMMENT_ANSWER: 'comment_answer',
    DELETE_COMMENT: 'delete_comment',
    LIKE_COMMENT: 'like_comment',
    UNLIKE_COMMENT: 'unlike_comment',

    // Server -> Client (Broadcast events)
    ERROR: 'error',
    AUTH_SUCCESS: 'auth_success',
    HOST_RECOVERED_STATE: 'host_recovered_state',
    ROOM_STATE: 'room_state',
    HOST_ROOM_STATS: 'host_room_stats',
    NEW_QUESTIONS: 'new_questions',
    RECOVERED_ANSWERS: 'recovered_answers',
    DISPLAY_QUESTION: 'display_question',
    UPDATE_STATS: 'update_stats',
    SHOW_LEADERBOARD: 'show_leaderboard',
    UPDATE_PINNED_ANSWER: 'update_pinned_answer',

    // Interaction events (Server -> Client)
    PEER_ANSWERS: 'peer_answers',
    INTERACTION_UPDATE: 'interaction_update'
} as const

// Create a type representing the values of the SocketEvent object
export type SocketEventType = (typeof SocketEvent)[keyof typeof SocketEvent]
