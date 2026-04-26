import { Socket } from 'socket.io-client'
import { SocketEvent } from './events'
import * as Client from './client'
import * as Host from './host'
import * as Screen from './screen'

export type { PeerAnswer } from '../interaction'

// ---------------------------------------------------------
// 1. Events received BY the Frontend (Server -> Client)
// ---------------------------------------------------------
export interface ServerToClientEvents {
    [SocketEvent.ERROR]: (payload: Screen.ErrorPayload) => void
    [SocketEvent.AUTH_SUCCESS]: (payload: Client.AuthSuccessPayload) => void

    // Shared
    [SocketEvent.ROOM_STATE]: (payload: Screen.RoomStatePayload) => void

    // Host specific
    [SocketEvent.HOST_RECOVERED_STATE]: (
        payload: Host.HostRecoveredStatePayload
    ) => void
    [SocketEvent.HOST_ROOM_STATS]: (payload: Host.HostRoomStatsPayload) => void

    // Client specific
    [SocketEvent.NEW_QUESTIONS]: (payload: Client.NewQuestionsPayload) => void
    [SocketEvent.RECOVERED_ANSWERS]: (
        payload: Client.RecoveredAnswersPayload
    ) => void
    [SocketEvent.PEER_ANSWERS]: (payload: Client.PeerAnswersPayload) => void
    [SocketEvent.INTERACTION_UPDATE]: (
        payload: Client.InteractionUpdatePayload
    ) => void

    // Screen (and Host) specific
    [SocketEvent.DISPLAY_QUESTION]: (
        payload: Screen.DisplayQuestionPayload
    ) => void
    [SocketEvent.UPDATE_STATS]: (payload: Screen.UpdateStatsPayload) => void
    [SocketEvent.SHOW_LEADERBOARD]: (
        payload: Screen.ShowLeaderboardPayload
    ) => void
    [SocketEvent.UPDATE_PINNED_ANSWER]: (
        payload: Screen.UpdatePinnedAnswerPayload
    ) => void
}

// ---------------------------------------------------------
// 2. Events sent BY the Frontend (Client -> Server)
// ---------------------------------------------------------
export interface ClientToServerEvents {
    // Join Events
    [SocketEvent.HOST_JOIN_ROOM]: (payload: Host.HostJoinRoomPayload) => void
    [SocketEvent.CLIENT_JOIN_ROOM]: (
        payload: Client.ClientJoinRoomPayload
    ) => void
    [SocketEvent.SCREEN_JOIN_ROOM]: (
        payload: Screen.ScreenJoinRoomPayload
    ) => void

    // Client Action
    [SocketEvent.SUBMIT_ANSWER]: (
        payload: Client.SubmitAnswerPayload,
        callback?: (response: any) => void
    ) => void

    // Host Actions
    [SocketEvent.HOST_BROADCAST_QUESTIONS]: (
        payload: Host.HostBroadcastQuestionsPayload
    ) => void
    [SocketEvent.HOST_DISPLAY_QUESTION]: (
        payload: Host.HostDisplayQuestionPayload
    ) => void
    [SocketEvent.HOST_PIN_ANSWER]: (payload: Host.HostPinAnswerPayload) => void
    [SocketEvent.HOST_SHOW_LEADERBOARD]: (
        payload: Host.HostShowLeaderboardPayload
    ) => void
    [SocketEvent.END_GAME]: (payload: Host.EndGamePayload) => void

    // Interaction Actions (Client / Host -> Server)
    [SocketEvent.LIKE_ANSWER]: (payload: Client.LikeAnswerPayload) => void
    [SocketEvent.UNLIKE_ANSWER]: (payload: Client.LikeAnswerPayload) => void
    [SocketEvent.COMMENT_ANSWER]: (payload: Client.CommentAnswerPayload) => void
    [SocketEvent.DELETE_COMMENT]: (payload: Host.HostDeleteCommentPayload) => void
    [SocketEvent.LIKE_COMMENT]: (payload: Client.LikeCommentPayload) => void
    [SocketEvent.UNLIKE_COMMENT]: (payload: Client.LikeCommentPayload) => void
}

// ---------------------------------------------------------
// 3. Export the custom typed Socket
// ---------------------------------------------------------
export type QuizioSocket = Socket<ServerToClientEvents, ClientToServerEvents>

// Also export the Enum for easy access in Vue components
export { SocketEvent } from './events'
