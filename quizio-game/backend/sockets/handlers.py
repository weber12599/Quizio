import asyncio
import json
import uuid
from functools import wraps
from typing import Dict

from pydantic import ValidationError
from utils import (
    check_guest_credentials,
    check_student_credentials,
    compute_stats,
    generate_leaderboard,
    grade_answer,
    submit_batch_interactions,
    submit_batch_submissions,
)

from .events import SocketEvent
from .schemas import (
    ClientJoinRoomPayload,
    CommentAnswerPayload,
    DeleteCommentPayload,
    EndGamePayload,
    HostBroadcastQuestionsPayload,
    HostDisplayQuestionPayload,
    HostJoinRoomPayload,
    HostPinAnswerPayload,
    HostShowLeaderboardPayload,
    LikeAnswerPayload,
    LikeCommentPayload,
    ScreenJoinRoomPayload,
    SubmitAnswerPayload,
)
from .server import sio

# In-memory room state management (O(1) Optimized Structure)
room_states: Dict[str, dict] = {}

# Prefix for option-level interaction owner IDs (e.g., 'opt_0', 'opt_1')
OPTION_OWNER_PREFIX = 'opt_'


def validate_payload(schema_class):
    """
    Decorator to automatically parse and validate Socket.IO event payloads.
    Returns an error dictionary if validation fails.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(sid: str, data: dict, *args, **kwargs):
            try:
                payload = schema_class(**data)
            except ValidationError as e:
                print(f'Validation error from {sid} for {schema_class.__name__}: {e}')
                return {'error': 'Invalid payload format'}
            return await func(sid, payload, *args, **kwargs)

        return wrapper

    return decorator


async def auto_clean_zombie_room(room_pin: str, token: str, delay_seconds: int = 1800):
    """
    Background task to clean up a room if the host doesn't reconnect within the delay period.
    Default delay is 1800 seconds (30 minutes).
    """
    await asyncio.sleep(delay_seconds)

    room = room_states.get(room_pin)
    # Check if room still exists, host is STILL disconnected, and token matches (no takeover happened)
    if room and room.get('host_sid') is None and room.get('token') == token:
        print(
            f'🧹 Auto-cleaning zombie room {room_pin} after {delay_seconds}s of host inactivity.'
        )

        # Disconnect all active clients
        for client in room.get('clients', {}).values():
            if client.get('is_online') and client.get('sid'):
                await sio.emit(
                    'error',
                    {'message': 'The room was closed due to host inactivity.'},
                    to=client['sid'],
                )
                await sio.disconnect(client['sid'])

        # Disconnect all screens
        for screen_sid in room.get('screen_sids', set()):
            await sio.emit(
                'error',
                {'message': 'The room was closed due to host inactivity.'},
                to=screen_sid,
            )
            await sio.disconnect(screen_sid)

        # Free up the memory
        del room_states[room_pin]


@sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')


@sio.event
async def disconnect(sid):
    print(f'Client disconnected: {sid}')
    for room_pin, room in list(room_states.items()):
        # 1. Check if the disconnected client is the Host (O(1))
        if room.get('host_sid') == sid:
            room['host_sid'] = None
            print(
                f'⚠️ Host disconnected from room {room_pin}. Starting cleanup timer...'
            )
            asyncio.create_task(
                auto_clean_zombie_room(room_pin, room['token'], delay_seconds=1800)
            )
            break

        # 2. Check if the disconnected client is a Screen (O(1))
        if 'screen_sids' in room and sid in room['screen_sids']:
            room['screen_sids'].remove(sid)
            print(f'🖥️ Screen disconnected from room {room_pin}')
            break

        # 3. Check if the disconnected client is a Student/Guest (O(1) via reverse lookup)
        if 'client_sids' in room and sid in room['client_sids']:
            player_id = room['client_sids'].pop(sid)  # Remove sid mapping
            if player_id in room.get('clients', {}):
                room['clients'][player_id]['is_online'] = False
                room['clients'][player_id]['sid'] = None
                print(f'🔌 Client {player_id} went offline in room {room_pin}')

            await broadcast_room_state(room_pin)
            break


@sio.on(SocketEvent.HOST_JOIN_ROOM.value)
@validate_payload(HostJoinRoomPayload)
async def host_join_room(sid: str, payload: HostJoinRoomPayload):
    room_pin = payload.room_pin

    if room_pin in room_states:
        room = room_states[room_pin]

        # 1. Collision Check: Different teacher trying to use the same PIN
        if room['token'] != payload.token:
            print(f'❌ Room PIN collision: {room_pin}')
            await sio.emit(
                'error',
                {
                    'message': 'This Room PIN is already in use by another active session.'
                },
                to=sid,
            )
            await sio.disconnect(sid)
            return

        # 2. Takeover Mechanism: Same teacher, reconnecting or logging in from a new device
        old_host_sid = room.get('host_sid')
        if old_host_sid and old_host_sid != sid:
            print(f'🔄 Host session takeover in room {room_pin}')
            await sio.emit(
                'error',
                {'message': 'Logged in from another device. Disconnected.'},
                to=old_host_sid,
            )
            await sio.disconnect(old_host_sid)

        # Update host sid
        room['host_sid'] = sid
        print(f'✅ Host_Teacher reconnected / took over room {room_pin}')

    else:
        # 3. Initialize NEW room state (O(1) Optimized Structure)
        room_states[room_pin] = {
            'token': payload.token,
            'exam_id': payload.exam_id,
            'host_sid': sid,
            'host_name': payload.host_name,
            'screen_sids': set(),
            'clients': {},  # Key: player_id, Value: client data dict
            'client_sids': {},  # Reverse lookup -> Key: sid, Value: player_id
            'broadcasted_questions': {},
            'displayed_question': None,
            'display_state': 'question',
            'pinned_answer': None,
            'answers': {},
            'gradings': {},
            'interactions': {},  # {q_id: {owner_player_id: {likes: [], comments: []}}}
            'current_screen': 'lobby',
            'target_class': payload.target_class,
            'allow_guests': payload.allow_guests,
            'expected_students': payload.expected_students,
            'expected_students_set': set(payload.expected_students),
        }
        print(f'✅ Host_Teacher created room {room_pin}')

    room = room_states[room_pin]

    # 4. Recover host state
    broadcasted_ids = [q_id for q_id in room.get('broadcasted_questions', {}).keys()]
    displayed_q = room.get('displayed_question')

    await sio.emit(
        'host_recovered_state',
        {
            'broadcasted_ids': broadcasted_ids,
            'displayed_question_id': displayed_q['id'] if displayed_q else None,
            'display_state': room.get('display_state', 'question'),
            'is_leaderboard_displayed': room.get('current_screen') == 'leaderboard',
            'pinned_answer': room.get('pinned_answer'),
        },
        to=sid,
    )

    await broadcast_room_state(room_pin)


@sio.on(SocketEvent.CLIENT_JOIN_ROOM.value)
@validate_payload(ClientJoinRoomPayload)
async def client_join_room(sid: str, payload: ClientJoinRoomPayload):
    room_pin = payload.room_pin

    if room_pin not in room_states:
        await sio.emit('error', {'message': 'Room does not exist'}, to=sid)
        await sio.disconnect(sid)
        return

    room = room_states[room_pin]
    player_name = 'Unknown'
    student_db_id = None
    player_id = None

    # 1. Authentication Logic
    if not payload.is_guest:
        if (
            room.get('target_class') is not None
            and payload.student_id not in room['expected_students_set']
        ):
            await sio.emit('error', {'message': 'Unexpected student id.'}, to=sid)
            await sio.disconnect(sid)
            return

        token = room.get('token')
        student_info = await check_student_credentials(
            payload.student_id, payload.password, token
        )

        if not student_info:
            await sio.emit('error', {'message': 'Invalid credentials.'}, to=sid)
            await sio.disconnect(sid)
            return

        player_id = payload.student_id
        player_name = student_info.get('name')
        upload_token = student_info.get('upload_token')
        student_db_id = student_info.get('id')

    else:
        if not room.get('allow_guests', False):
            await sio.emit('error', {'message': 'Guest access is disabled.'}, to=sid)
            await sio.disconnect(sid)
            return

        token = room.get('token')

        existing = room['clients'].get(payload.player_id) if payload.player_id else None
        if existing and existing.get('is_guest'):
            player_id = payload.player_id
            player_name = existing['name']
            guest_info = await check_guest_credentials(player_name, token)
            if not guest_info:
                await sio.emit('error', {'message': 'Invalid credentials.'}, to=sid)
                await sio.disconnect(sid)
                return
            upload_token = guest_info.get('upload_token')
        else:
            guest_info = await check_guest_credentials(payload.guest_name, token)
            if not guest_info:
                await sio.emit('error', {'message': 'Invalid credentials.'}, to=sid)
                await sio.disconnect(sid)
                return
            player_id = guest_info.get('guest_id')
            player_name = payload.guest_name
            upload_token = guest_info.get('upload_token')

    await sio.emit('auth_success', {'upload_token': upload_token, 'player_id': player_id}, to=sid)

    # 2. Register or Update client state (O(1) & Reconnection support)
    is_reconnect = player_id in room['clients']

    room['clients'][player_id] = {
        'sid': sid,
        'name': player_name,
        'student_db_id': student_db_id,
        'is_guest': payload.is_guest,
        'is_online': True,
    }

    # Add reverse lookup mapping
    room['client_sids'][sid] = player_id

    print(
        f'✅ {player_name} (Client, Guest: {payload.is_guest}, Reconnect: {is_reconnect}) joined room {room_pin}'
    )

    # 3. Recover client state (Questions & Answers)
    broadcasted = []
    for q in room.get('broadcasted_questions', {}).values():
        client_q = q.copy()
        client_q.pop('reference_answer', None)
        broadcasted.append(client_q)

    if broadcasted:
        await sio.emit('new_questions', {'questions': broadcasted}, to=sid)

    recovered_answers = {}
    recovered_gradings = {}

    for q_id, student_answers in room.get('answers', {}).items():
        if player_id in student_answers:
            recovered_answers[q_id] = student_answers[player_id]

    for q_id, student_gradings in room.get('gradings', {}).items():
        if player_id in student_gradings:
            recovered_gradings[q_id] = student_gradings[player_id]

    if recovered_answers:
        await sio.emit(
            'recovered_answers',
            {'answers': recovered_answers, 'gradings': recovered_gradings},
            to=sid,
        )

    # Recover peer answers and interactions for all questions the student has already submitted
    for sub_q_id, student_answers in room.get('answers', {}).items():
        if player_id not in student_answers:
            continue
        q_def = room.get('broadcasted_questions', {}).get(sub_q_id)
        if not q_def:
            continue
        if q_def.get('type') in ('essay', 'short'):
            peer_answers = _build_peer_answers(room, sub_q_id)
            await sio.emit(
                'peer_answers', {'question_id': sub_q_id, 'answers': peer_answers}, to=sid
            )
        for owner_id, ia in room.get('interactions', {}).get(sub_q_id, {}).items():
            await sio.emit(
                'interaction_update',
                {'question_id': sub_q_id, 'answer_owner_id': owner_id, 'answer_interactions': ia},
                to=sid,
            )

    # 4. Broadcast room updates
    await broadcast_room_state(room_pin)


@sio.on(SocketEvent.SCREEN_JOIN_ROOM.value)
@validate_payload(ScreenJoinRoomPayload)
async def screen_join_room(sid: str, payload: ScreenJoinRoomPayload):
    room_pin = payload.room_pin

    if room_pin not in room_states:
        await sio.emit('error', {'message': 'Room does not exist'}, to=sid)
        await sio.disconnect(sid)
        return

    # 1. Register screen player (O(1) Set)
    room_states[room_pin]['screen_sids'].add(sid)
    print(f'✅ Projector_Screen joined room {room_pin}')

    # 2. Recover screen state
    room = room_states[room_pin]
    current_screen = room.get('current_screen', 'lobby')

    if current_screen == 'question':
        displayed_q = room.get('displayed_question')
        if displayed_q:
            await sio.emit(
                'display_question',
                {
                    'question': displayed_q,
                    'display_state': room.get('display_state', 'question'),
                    'pinned_answer': room.get('pinned_answer'),
                },
                to=sid,
            )
            q_id = displayed_q['id']
            stats, total = compute_stats(
                displayed_q.get('type'), room.get('answers', {}).get(q_id, {})
            )
            await sio.emit('update_stats', {'stats': stats, 'total': total}, to=sid)

    elif current_screen == 'leaderboard':
        await sio.emit(
            'show_leaderboard', {'leaderboard': generate_leaderboard(room)}, to=sid
        )

    # 3. Broadcast room updates
    await broadcast_room_state(room_pin)


def _build_peer_answers(room: dict, q_id: int) -> list:
    """Build the peer-answers list for a given question from room state."""
    answers_for_q = room.get('answers', {}).get(q_id, {})
    clients_info = room.get('clients', {})
    return [
        {
            'player_id': owner_id,
            'name': clients_info.get(owner_id, {}).get('name', 'Unknown'),
            'is_guest': clients_info.get(owner_id, {}).get('is_guest', False),
            'answer': answer,
            'question_id': q_id,
        }
        for owner_id, answer in answers_for_q.items()
    ]


async def broadcast_peer_answers(room_pin: str, q_id: int):
    """Emit peer_answers to all online clients in the room."""
    room = room_states.get(room_pin)
    if not room:
        return
    peer_answers = _build_peer_answers(room, q_id)
    payload = {'question_id': q_id, 'answers': peer_answers}
    for client in room.get('clients', {}).values():
        if client.get('is_online') and client.get('sid'):
            await sio.emit('peer_answers', payload, to=client['sid'])


async def broadcast_interaction_update(room_pin: str, q_id: int, owner_id: str):
    """Emit interaction_update for one answer to all clients + host."""
    room = room_states.get(room_pin)
    if not room:
        return
    answer_ia = room.get('interactions', {}).get(q_id, {}).get(owner_id)
    if answer_ia is None:
        return
    payload = {
        'question_id': q_id,
        'answer_owner_id': owner_id,
        'answer_interactions': answer_ia,
    }
    for client in room.get('clients', {}).values():
        if client.get('is_online') and client.get('sid'):
            await sio.emit('interaction_update', payload, to=client['sid'])
    host_sid = room.get('host_sid')
    if host_sid:
        await sio.emit('interaction_update', payload, to=host_sid)


async def broadcast_room_state(room_pin: str):
    if room_pin in room_states:
        room = room_states[room_pin]

        # Calculate dynamic stats based on online clients
        online_clients = [c for c in room['clients'].values() if c['is_online']]
        players_list = [c['name'] for c in online_clients]

        student_count = sum(1 for c in online_clients if not c['is_guest'])
        guest_count = sum(1 for c in online_clients if c['is_guest'])

        player_stats = {
            'student_count': student_count,
            'guest_count': guest_count,
            'total_count': student_count + guest_count,
        }

        print(
            f'📡 Broadcasting room {room_pin} | Online Clients: {len(players_list)} | Stats: {player_stats}'
        )

        # 1. Broadcast to all online clients
        for client in online_clients:
            if client['sid']:
                await sio.emit(
                    'room_state',
                    {
                        'room_pin': room_pin,
                        'players': players_list,
                        'player_stats': player_stats,
                    },
                    to=client['sid'],
                )

        # 2. Broadcast to all screens
        for screen_sid in room.get('screen_sids', set()):
            await sio.emit(
                'room_state',
                {
                    'room_pin': room_pin,
                    'players': players_list,
                    'player_stats': player_stats,
                },
                to=screen_sid,
            )

        # 3. Broadcast to Host (Includes private info like who is offline)
        host_sid = room.get('host_sid')
        if host_sid:
            await sio.emit(
                'room_state',
                {
                    'room_pin': room_pin,
                    'players': players_list,
                    'player_stats': player_stats,
                },
                to=host_sid,
            )

            clients_info = {
                pid: {
                    'name': c['name'],
                    'is_guest': c['is_guest'],
                    'is_online': c['is_online'],
                }
                for pid, c in room['clients'].items()
            }
            await sio.emit(
                'host_room_stats',
                {
                    'target_class': room.get('target_class'),
                    'allow_guests': room.get('allow_guests', True),
                    'expected_students': room.get('expected_students', []),
                    'answers': room.get('answers', {}),
                    'gradings': room.get('gradings', {}),
                    'clients_info': clients_info,
                },
                to=host_sid,
            )


@sio.on(SocketEvent.HOST_BROADCAST_QUESTIONS.value)
@validate_payload(HostBroadcastQuestionsPayload)
async def host_broadcast_questions(sid: str, payload: HostBroadcastQuestionsPayload):
    room = room_states.get(payload.room_pin)
    if not room or room.get('host_sid') != sid:
        return

    new_broadcasts = []
    for q in payload.questions:
        q_id = q['id']
        if q_id not in room['broadcasted_questions']:
            room['broadcasted_questions'][q_id] = q
            room['answers'][q_id] = {}

            client_q = q.copy()
            client_q.pop('reference_answer', None)
            new_broadcasts.append(client_q)

    if new_broadcasts:
        for client in room.get('clients', {}).values():
            if client['is_online'] and client['sid']:
                await sio.emit(
                    'new_questions', {'questions': new_broadcasts}, to=client['sid']
                )


@sio.on(SocketEvent.HOST_DISPLAY_QUESTION.value)
@validate_payload(HostDisplayQuestionPayload)
async def host_display_question(sid: str, payload: HostDisplayQuestionPayload):
    room = room_states.get(payload.room_pin)
    if not room or room.get('host_sid') != sid:
        return

    current_displayed = room.get('displayed_question')
    if not payload.question or (
        current_displayed and current_displayed.get('id') != payload.question.get('id')
    ):
        room['pinned_answer'] = None

    room['displayed_question'] = payload.question
    room['display_state'] = payload.display_state if payload.question else 'question'
    room['current_screen'] = 'question' if payload.question else 'lobby'

    for screen_sid in room.get('screen_sids', set()):
        await sio.emit(
            'display_question',
            {
                'question': payload.question,
                'display_state': payload.display_state,
                'pinned_answer': room.get('pinned_answer'),
            },
            to=screen_sid,
        )

        if payload.question:
            q_id = payload.question['id']
            stats, total = compute_stats(
                payload.question.get('type'), room['answers'].get(q_id, {})
            )
            await sio.emit(
                'update_stats', {'stats': stats, 'total': total}, to=screen_sid
            )


@sio.on(SocketEvent.HOST_PIN_ANSWER.value)
@validate_payload(HostPinAnswerPayload)
async def host_pin_answer(sid: str, payload: HostPinAnswerPayload):
    room = room_states.get(payload.room_pin)
    if not room or room.get('host_sid') != sid:
        return

    if payload.pinned_answer and payload.question_id:
        payload.pinned_answer['question_id'] = payload.question_id

    room['pinned_answer'] = payload.pinned_answer

    # Emit to all screens and back to host (for state sync)
    targets = list(room.get('screen_sids', set())) + [sid]
    for target_sid in targets:
        await sio.emit(
            'update_pinned_answer',
            {'pinned_answer': payload.pinned_answer},
            to=target_sid,
        )


@sio.on(SocketEvent.SUBMIT_ANSWER.value)
@validate_payload(SubmitAnswerPayload)
async def submit_answer(sid: str, payload: SubmitAnswerPayload):
    room = room_states.get(payload.room_pin)
    if not room:
        return {'error': 'Room not found'}

    # O(1) Auth check using reverse lookup
    player_id = room.get('client_sids', {}).get(sid)
    if not player_id:
        return {'error': 'Unauthorized'}

    q_id = payload.question_id

    room.setdefault('gradings', {}).setdefault(q_id, {})
    room.setdefault('answers', {}).setdefault(q_id, {})

    room['answers'][q_id][player_id] = payload.answer

    question = room['broadcasted_questions'].get(q_id)
    if not question:
        return {'error': 'Question not found'}

    q_type = question.get('type')
    correct_answer = question.get('reference_answer')
    is_correct = (
        None
        if question.get('needs_manual_grading', False)
        else grade_answer(q_type, payload.answer, correct_answer)
    )

    grading_result = {'is_correct': is_correct, 'correct_answer': correct_answer}
    room['gradings'][q_id][player_id] = grading_result

    displayed_q = room.get('displayed_question')
    if displayed_q and displayed_q['id'] == q_id:
        stats, total = compute_stats(q_type, room['answers'].get(q_id, {}))
        for screen_sid in room.get('screen_sids', set()):
            await sio.emit(
                'update_stats', {'stats': stats, 'total': total}, to=screen_sid
            )

    # Unlock peer interaction immediately upon submission
    submitters = set(room['answers'].get(q_id, {}).keys())
    if q_type in ('essay', 'short'):
        peer_answers = _build_peer_answers(room, q_id)
        pa_payload = {'question_id': q_id, 'answers': peer_answers}
        for client_id, client in room.get('clients', {}).items():
            if client_id in submitters and client.get('is_online') and client.get('sid'):
                await sio.emit('peer_answers', pa_payload, to=client['sid'])

    # Send existing interactions for this question to the new submitter
    for owner_id, ia in room.get('interactions', {}).get(q_id, {}).items():
        await sio.emit(
            'interaction_update',
            {'question_id': q_id, 'answer_owner_id': owner_id, 'answer_interactions': ia},
            to=sid,
        )

    await broadcast_room_state(payload.room_pin)
    return grading_result


@sio.on(SocketEvent.HOST_SHOW_LEADERBOARD.value)
@validate_payload(HostShowLeaderboardPayload)
async def host_show_leaderboard(sid: str, payload: HostShowLeaderboardPayload):
    room = room_states.get(payload.room_pin)
    if not room or room.get('host_sid') != sid:
        return

    room['current_screen'] = 'leaderboard'
    leaderboard = generate_leaderboard(room)

    for screen_sid in room.get('screen_sids', set()):
        await sio.emit('show_leaderboard', {'leaderboard': leaderboard}, to=screen_sid)


@sio.on(SocketEvent.LIKE_ANSWER.value)
@validate_payload(LikeAnswerPayload)
async def like_answer(sid: str, payload: LikeAnswerPayload):
    room = room_states.get(payload.room_pin)
    if not room:
        return

    is_host = room.get('host_sid') == sid
    player_id = room.get('client_sids', {}).get(sid)
    if not is_host and not player_id:
        return

    caller_id = '__host__' if is_host else player_id
    caller_name = room.get('host_name', '老師') if is_host else room['clients'].get(player_id, {}).get('name', 'Unknown')

    q_id = payload.question_id
    owner_id = payload.answer_owner_id

    q_ia = room.setdefault('interactions', {}).setdefault(q_id, {})
    answer_ia = q_ia.setdefault(owner_id, {'likes': [], 'comments': []})

    if any(like['from_id'] == caller_id for like in answer_ia['likes']):
        return  # already liked — no-op

    answer_ia['likes'].append({'from_id': caller_id, 'name': caller_name})
    await broadcast_interaction_update(payload.room_pin, q_id, owner_id)


@sio.on(SocketEvent.UNLIKE_ANSWER.value)
@validate_payload(LikeAnswerPayload)
async def unlike_answer(sid: str, payload: LikeAnswerPayload):
    room = room_states.get(payload.room_pin)
    if not room:
        return

    is_host = room.get('host_sid') == sid
    player_id = room.get('client_sids', {}).get(sid)
    if not is_host and not player_id:
        return

    caller_id = '__host__' if is_host else player_id

    q_id = payload.question_id
    owner_id = payload.answer_owner_id
    answer_ia = room.get('interactions', {}).get(q_id, {}).get(owner_id)
    if not answer_ia:
        return

    answer_ia['likes'] = [like for like in answer_ia['likes'] if like['from_id'] != caller_id]
    await broadcast_interaction_update(payload.room_pin, q_id, owner_id)


@sio.on(SocketEvent.COMMENT_ANSWER.value)
@validate_payload(CommentAnswerPayload)
async def comment_answer(sid: str, payload: CommentAnswerPayload):
    room = room_states.get(payload.room_pin)
    if not room:
        return

    is_host = room.get('host_sid') == sid
    player_id = room.get('client_sids', {}).get(sid)
    if not is_host and not player_id:
        return

    caller_id = '__host__' if is_host else player_id
    caller_name = room.get('host_name', '老師') if is_host else room['clients'].get(player_id, {}).get('name', 'Unknown')

    q_id = payload.question_id
    owner_id = payload.answer_owner_id

    q_ia = room.setdefault('interactions', {}).setdefault(q_id, {})
    answer_ia = q_ia.setdefault(owner_id, {'likes': [], 'comments': []})

    answer_ia['comments'].append({
        'id': str(uuid.uuid4()),
        'from_id': caller_id,
        'name': caller_name,
        'content': payload.content,
        'is_host': is_host,
        'likes': [],
    })
    await broadcast_interaction_update(payload.room_pin, q_id, owner_id)


@sio.on(SocketEvent.DELETE_COMMENT.value)
@validate_payload(DeleteCommentPayload)
async def delete_comment(sid: str, payload: DeleteCommentPayload):
    room = room_states.get(payload.room_pin)
    if not room or room.get('host_sid') != sid:
        return

    q_id = payload.question_id
    owner_id = payload.answer_owner_id
    answer_ia = room.get('interactions', {}).get(q_id, {}).get(owner_id)
    if not answer_ia:
        return

    answer_ia['comments'] = [
        c for c in answer_ia['comments'] if c['id'] != payload.comment_id
    ]
    await broadcast_interaction_update(payload.room_pin, q_id, owner_id)


@sio.on(SocketEvent.LIKE_COMMENT.value)
@validate_payload(LikeCommentPayload)
async def like_comment(sid: str, payload: LikeCommentPayload):
    room = room_states.get(payload.room_pin)
    if not room:
        return

    is_host = room.get('host_sid') == sid
    player_id = room.get('client_sids', {}).get(sid)
    if not is_host and not player_id:
        return

    caller_id = '__host__' if is_host else player_id
    caller_name = room.get('host_name', '老師') if is_host else room['clients'].get(player_id, {}).get('name', 'Unknown')

    answer_ia = room.get('interactions', {}).get(payload.question_id, {}).get(payload.answer_owner_id)
    if not answer_ia:
        return

    comment = next((c for c in answer_ia['comments'] if c['id'] == payload.comment_id), None)
    if not comment:
        return

    if 'likes' not in comment:
        comment['likes'] = []

    if any(like['from_id'] == caller_id for like in comment['likes']):
        return  # already liked — no-op

    comment['likes'].append({'from_id': caller_id, 'name': caller_name})
    await broadcast_interaction_update(payload.room_pin, payload.question_id, payload.answer_owner_id)


@sio.on(SocketEvent.UNLIKE_COMMENT.value)
@validate_payload(LikeCommentPayload)
async def unlike_comment(sid: str, payload: LikeCommentPayload):
    room = room_states.get(payload.room_pin)
    if not room:
        return

    is_host = room.get('host_sid') == sid
    player_id = room.get('client_sids', {}).get(sid)
    if not is_host and not player_id:
        return

    caller_id = '__host__' if is_host else player_id

    answer_ia = room.get('interactions', {}).get(payload.question_id, {}).get(payload.answer_owner_id)
    if not answer_ia:
        return

    comment = next((c for c in answer_ia['comments'] if c['id'] == payload.comment_id), None)
    if not comment or 'likes' not in comment:
        return

    comment['likes'] = [like for like in comment['likes'] if like['from_id'] != caller_id]
    await broadcast_interaction_update(payload.room_pin, payload.question_id, payload.answer_owner_id)


async def _submit_interactions(room: dict, token: str, answer_ids: list) -> None:
    """
    Build and submit all in-memory interaction records to quizio-data.

    Two interaction shapes coexist:
      - answer-level (short / essay): owner_player_id is a real player_id;
        keyed to a StudentAnswer.id created during batch submission.
      - option-level (single / multiple / boolean): owner_player_id is
        'opt_{index}'; keyed to (question_id, option_index). All option-level
        rows share the session anchor submission_id (any submission from the
        batch) so the read endpoint can scope them to this session.

    Best-effort: errors are caught and logged.
    """
    if not answer_ids:
        return

    clients = room.get('clients', {})
    interactions = room.get('interactions', {})

    # answer_lookup: (student_id, guest_name, q_id) → answer_db_id
    answer_lookup: Dict[tuple, int] = {}
    for mapping in answer_ids:
        key = (mapping.get('student_id'), mapping.get('guest_name'), mapping.get('question_id'))
        answer_lookup[key] = mapping['answer_id']

    # session anchor: any submission_id from this batch
    session_anchor: int | None = next(
        (m.get('submission_id') for m in answer_ids if m.get('submission_id')),
        None,
    )

    def resolve_from_id(from_id: str) -> dict | None:
        if from_id == '__host__':
            return {'is_host': True}
        client_data = clients.get(from_id)
        if not client_data:
            return None
        if client_data.get('student_db_id'):
            return {'student_id': client_data['student_db_id']}
        return {'guest_name': client_data['name']}

    def build_likes(ia_likes: list) -> list:
        out = []
        for like in ia_likes:
            author = resolve_from_id(like['from_id'])
            if author:
                out.append(author)
        return out

    def build_comments(ia_comments: list) -> list:
        out = []
        for comment in ia_comments:
            author = resolve_from_id(comment['from_id'])
            if not author:
                continue
            comment_likes = []
            for cl in comment.get('likes', []):
                cl_author = resolve_from_id(cl['from_id'])
                if cl_author:
                    comment_likes.append({'author': cl_author})
            out.append({
                'content': comment['content'],
                'author': author,
                'comment_likes': comment_likes,
            })
        return out

    answer_interactions = []
    option_interactions = []

    for q_id, owner_map in interactions.items():
        for owner_player_id, ia_data in owner_map.items():
            likes_payload = build_likes(ia_data.get('likes', []))
            comments_payload = build_comments(ia_data.get('comments', []))

            if not likes_payload and not comments_payload:
                continue

            if isinstance(owner_player_id, str) and owner_player_id.startswith(OPTION_OWNER_PREFIX):
                # Option-level interaction (single / multiple / boolean)
                try:
                    option_index = int(owner_player_id[len(OPTION_OWNER_PREFIX):])
                except ValueError:
                    continue
                option_interactions.append({
                    'question_id': q_id,
                    'option_index': option_index,
                    'option_likes': likes_payload,
                    'comments': comments_payload,
                })
            else:
                # Answer-level interaction (short / essay)
                client_data = clients.get(owner_player_id)
                if not client_data:
                    continue
                student_db_id = client_data.get('student_db_id')
                guest_name = client_data['name'] if not student_db_id else None
                answer_db_id = answer_lookup.get((student_db_id, guest_name, q_id))
                if not answer_db_id:
                    continue
                answer_interactions.append({
                    'answer_id': answer_db_id,
                    'answer_likes': likes_payload,
                    'comments': comments_payload,
                })

    if not answer_interactions and not option_interactions:
        return

    payload = {
        'session_anchor_submission_id': session_anchor,
        'answer_interactions': answer_interactions,
        'option_interactions': option_interactions,
    }

    try:
        await submit_batch_interactions(token, payload)
    except Exception as e:
        print(f'Error submitting interactions: {e}')


@sio.on(SocketEvent.END_GAME.value)
@validate_payload(EndGamePayload)
async def end_game(sid: str, payload: EndGamePayload):
    room = room_states.get(payload.room_pin)
    if not room or room.get('host_sid') != sid:
        return

    exam_id = room.get('exam_id')
    token = room.get('token')
    if exam_id and token:
        batch_payload = []
        for player_id, client_data in room.get('clients', {}).items():
            answers_payload = []
            for q_id, student_answers in room.get('answers', {}).items():
                if player_id in student_answers:
                    ans_content = student_answers[player_id]
                    ans_content_str = (
                        json.dumps(ans_content)
                        if isinstance(ans_content, list)
                        else (str(ans_content) if ans_content is not None else None)
                    )

                    grading = room.get('gradings', {}).get(q_id, {}).get(player_id, {})
                    is_correct = grading.get('is_correct')
                    earned_score = (
                        room.get('broadcasted_questions', {})
                        .get(q_id, {})
                        .get('score', 0)
                        if is_correct is True
                        else (0 if is_correct is False else None)
                    )

                    answers_payload.append(
                        {
                            'question_id': q_id,
                            'answer_content': ans_content_str,
                            'is_correct': grading.get('is_correct'),
                            'score': earned_score,
                        }
                    )

            if answers_payload:
                batch_payload.append(
                    {
                        'exam_id': exam_id,
                        'student_id': client_data.get('student_db_id'),
                        'guest_name': client_data.get('name')
                        if not client_data.get('student_db_id')
                        else None,
                        'answers': answers_payload,
                    }
                )

        if batch_payload:
            batch_result = await submit_batch_submissions(token, batch_payload)
            answer_ids = batch_result.get('answer_ids', [])
            if not answer_ids:
                print(f'[warn] end_game: batch submission returned no answer_ids for room {payload.room_pin}')
            await _submit_interactions(room, token, answer_ids)

    # Disconnect all active clients (snapshot to avoid mutation during iteration)
    for client in list(room.get('clients', {}).values()):
        if client.get('is_online') and client.get('sid'):
            await sio.emit(
                'error',
                {'message': 'The host has ended the game. Disconnecting...'},
                to=client['sid'],
            )
            await sio.disconnect(client['sid'])

    # Disconnect all screens (snapshot to avoid mutation during iteration)
    for screen_sid in list(room.get('screen_sids', set())):
        await sio.emit(
            'error',
            {'message': 'The host has ended the game. Disconnecting...'},
            to=screen_sid,
        )
        await sio.disconnect(screen_sid)

    room_states.pop(payload.room_pin, None)
