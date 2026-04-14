from enum import Enum


class SocketEvent(str, Enum):
    # Built-in events
    CONNECT = 'connect'
    DISCONNECT = 'disconnect'

    # Specific Join Room Events
    HOST_JOIN_ROOM = 'host_join_room'
    CLIENT_JOIN_ROOM = 'client_join_room'
    SCREEN_JOIN_ROOM = 'screen_join_room'

    # Client (student / guest) to Server
    SUBMIT_ANSWER = 'submit_answer'

    # Client (host) to Server
    END_GAME = 'end_game'

    # Server to Client
    HOST_BROADCAST_QUESTIONS = 'host_broadcast_questions'
    HOST_DISPLAY_QUESTION = 'host_display_question'
    HOST_PIN_ANSWER = 'host_pin_answer'
    HOST_SHOW_LEADERBOARD = 'host_show_leaderboard'
