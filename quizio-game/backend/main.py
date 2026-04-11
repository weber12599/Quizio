import json
from typing import Dict

import socketio
from fastapi import FastAPI
from routers import router as api_router
from utils import (
    check_guest_credentials,
    check_student_credentials,
    compute_stats,
    generate_leaderboard,
    grade_answer,
    sanitize_rich_text,
    submit_batch_submissions,
)

# Initialize FastAPI app
fastapi_app = FastAPI()
fastapi_app.include_router(api_router)

# Initialize Socket.io AsyncServer
sio = socketio.AsyncServer(
    async_mode='asgi', cors_allowed_origins='*', ping_interval=25, ping_timeout=120
)

# Wrap FastAPI app with Socket.io ASGIApp
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# In-memory room state management
room_states: Dict[str, dict] = {}


@sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')


@sio.event
async def disconnect(sid):
    print(f'Client disconnected: {sid}')
    for room_pin, room_data in list(room_states.items()):
        players = room_data['players']
        if sid in players:
            player_info = players.pop(sid)

            if player_info.get('role') == 'client':
                room_data['client_names'].pop(sid, None)
                if player_info.get('is_guest'):
                    room_data['guest_count'] = max(
                        0, room_data.get('guest_count', 0) - 1
                    )
                else:
                    room_data['student_count'] = max(
                        0, room_data.get('student_count', 0) - 1
                    )

            if not players:
                del room_states[room_pin]
            else:
                await broadcast_room_state(room_pin)
            break


@sio.event
async def join_room(sid, data):
    room_pin = str(data.get('room_pin'))
    role = data.get('role')
    is_guest = data.get('is_guest', False)
    guest_name = data.get('guest_name', '')
    student_id = data.get('student_id', '')
    password = data.get('password', '')
    token = data.get('token', '')

    player_name = 'Unknown'
    student_db_id = None
    player_id = None

    if role == 'host':
        player_name = 'Host_Teacher'
        if room_pin not in room_states:
            room_states[room_pin] = {
                'token': token,
                'players': {},
                'client_names': {},
                'student_count': 0,
                'guest_count': 0,
                'broadcasted_questions': {},
                'displayed_question': None,
                'answers': {},
                'gradings': {},
                'current_screen': 'lobby',
                'target_class': data.get('target_class'),
                'allow_guests': data.get('allow_guests', True),
                'expected_students': data.get('expected_students', []),
            }
        else:
            room_states[room_pin]['token'] = token

    elif role == 'screen':
        player_name = 'Projector_Screen'
        if room_pin not in room_states:
            await sio.emit('error', {'message': 'Room does not exist'}, to=sid)
            await sio.disconnect(sid)
            return

    elif role == 'client':
        if room_pin not in room_states:
            await sio.emit('error', {'message': 'Room does not exist'}, to=sid)
            await sio.disconnect(sid)
            return

        room = room_states[room_pin]

        if not is_guest:
            token = room.get('token')
            student_info = await check_student_credentials(student_id, password, token)

            if not student_info:
                await sio.emit(
                    'error',
                    {'message': 'Invalid credentials.'},
                    to=sid,
                )
                await sio.disconnect(sid)
                return

            player_id = student_id
            player_name = student_info['name']
            upload_token = student_info.get('upload_token')
            student_db_id = student_info.get('id')

            await sio.emit('auth_success', {'upload_token': upload_token}, to=sid)
        elif not room.get('allow_guests', False):
            await sio.emit(
                'error',
                {'message': 'Guest access is disabled.'},
                to=sid,
            )
            await sio.disconnect(sid)
            return
        else:
            token = room.get('token')
            guest_info = await check_guest_credentials(guest_name, token)

            if not guest_info:
                await sio.emit(
                    'error',
                    {'message': 'Invalid credentials.'},
                    to=sid,
                )
                await sio.disconnect(sid)
                return

            player_id = guest_info.get('guest_id')
            player_name = guest_name
            upload_token = guest_info.get('upload_token')
            student_db_id = None

            await sio.emit('auth_success', {'upload_token': upload_token}, to=sid)
    else:
        await sio.disconnect(sid)
        return

    # append to player dict
    room_states[room_pin]['players'][sid] = {
        'role': role,
        'name': player_name,
        'player_id': player_id,
        'student_db_id': student_db_id,
        'is_guest': is_guest,
    }

    if role == 'client':
        room_states[room_pin]['client_names'][sid] = player_name
        if is_guest:
            room_states[room_pin]['guest_count'] += 1
        else:
            room_states[room_pin]['student_count'] += 1

    print(f'✅ {player_name} ({role}, Guest: {is_guest}) joined room {room_pin}')

    if role == 'host':
        room = room_states[room_pin]
        broadcasted_ids = [
            int(q_id) for q_id in room.get('broadcasted_questions', {}).keys()
        ]
        displayed_q = room.get('displayed_question')
        displayed_id = displayed_q['id'] if displayed_q else None
        is_leaderboard = room.get('current_screen') == 'leaderboard'

        await sio.emit(
            'host_recovered_state',
            {
                'broadcasted_ids': broadcasted_ids,
                'displayed_question_id': displayed_id,
                'is_leaderboard_displayed': is_leaderboard,
            },
            to=sid,
        )
    elif role == 'client':
        room = room_states[room_pin]

        broadcasted = []
        for q in room.get('broadcasted_questions', {}).values():
            client_q = q.copy()
            client_q.pop('reference_answer', None)
            broadcasted.append(client_q)

        if broadcasted:
            await sio.emit('new_questions', {'questions': broadcasted}, to=sid)

        recovered_answers = {}
        recovered_gradings = {}

        answers_dict = room.get('answers', {})
        for q_id, student_answers in answers_dict.items():
            if player_id in student_answers:
                recovered_answers[q_id] = student_answers[player_id]

        gradings_dict = room.get('gradings', {})
        for q_id, student_gradings in gradings_dict.items():
            if player_id in student_gradings:
                recovered_gradings[q_id] = student_gradings[player_id]

        if recovered_answers:
            await sio.emit(
                'recovered_answers',
                {'answers': recovered_answers, 'gradings': recovered_gradings},
                to=sid,
            )
    elif role == 'screen':
        room = room_states[room_pin]
        current_screen = room.get('current_screen', 'lobby')

        if current_screen == 'question':
            displayed_q = room.get('displayed_question')
            if displayed_q:
                await sio.emit('display_question', {'question': displayed_q}, to=sid)

                q_id = str(displayed_q['id'])
                q_type = displayed_q.get('type')
                answers_dict = room.get('answers', {}).get(q_id, {})
                stats, total = compute_stats(q_type, answers_dict)
                await sio.emit('update_stats', {'stats': stats, 'total': total}, to=sid)

        elif current_screen == 'leaderboard':
            leaderboard = generate_leaderboard(room)
            await sio.emit('show_leaderboard', {'leaderboard': leaderboard}, to=sid)

    await broadcast_room_state(room_pin)


async def broadcast_room_state(room_pin: str):
    if room_pin in room_states:
        room = room_states[room_pin]
        players_dict = room['players']

        players_list = list(room.get('client_names', {}).values())
        student_count = room.get('student_count', 0)
        guest_count = room.get('guest_count', 0)

        player_stats = {
            'student_count': student_count,
            'guest_count': guest_count,
            'total_count': student_count + guest_count,
        }

        print(
            f'📡 Broadcasting room {room_pin} | Clients: {len(players_list)} | Stats: {player_stats}'
        )

        for target_sid, client_data in players_dict.items():
            # 1. Public Data
            await sio.emit(
                'room_state',
                {
                    'room_pin': room_pin,
                    'players': players_list,
                    'player_stats': player_stats,
                },
                to=target_sid,
            )

            # 2. Private Host Data
            if client_data['role'] == 'host':
                clients_info = {
                    p['player_id']: {'name': p['name'], 'is_guest': p['is_guest']}
                    for p in players_dict.values()
                    if p['role'] == 'client' and p.get('player_id')
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
                    to=target_sid,
                )


@sio.event
async def host_broadcast_questions(sid, data):
    room_pin = str(data.get('room_pin'))
    questions = data.get('questions', [])

    room = room_states.get(room_pin)
    if not room:
        return

    player_info = room['players'].get(sid)
    if not player_info or player_info['role'] != 'host':
        return

    new_broadcasts = []
    for q in questions:
        q_id = str(q['id'])
        if q_id not in room['broadcasted_questions']:
            room['broadcasted_questions'][q_id] = q
            room['answers'][q_id] = {}

            client_q = q.copy()
            client_q.pop('reference_answer', None)
            new_broadcasts.append(client_q)

    if new_broadcasts:
        print(f'📢 Host send {len(new_broadcasts)} questions to clients')
        for target_sid, player in room['players'].items():
            if player['role'] == 'client':
                await sio.emit(
                    'new_questions', {'questions': new_broadcasts}, to=target_sid
                )


@sio.event
async def host_display_question(sid, data):
    room_pin = str(data.get('room_pin'))
    question = data.get('question')

    room = room_states.get(room_pin)
    if not room:
        return

    player_info = room['players'].get(sid)
    if not player_info or player_info['role'] != 'host':
        return

    room['displayed_question'] = question
    room['current_screen'] = 'question' if question else 'lobby'

    if question:
        print(f'🖥️ Host broadcast question ID {question["id"]} on the screen')
    else:
        print('🖥️ Host clear the screen')

    for target_sid, player in room['players'].items():
        if player['role'] == 'screen':
            await sio.emit('display_question', {'question': question}, to=target_sid)

            if question:
                q_id = str(question['id'])
                q_type = question.get('type')
                answers_dict = room['answers'].get(q_id, {})
                stats, total = compute_stats(q_type, answers_dict)
                await sio.emit(
                    'update_stats', {'stats': stats, 'total': total}, to=target_sid
                )


@sio.event
async def submit_answer(sid, data):
    if 'answer' in data and data['answer']:
        if isinstance(data['answer'], str):
            data['answer'] = sanitize_rich_text(data['answer'])
        elif isinstance(data['answer'], list):
            # Sanitize each string element inside the list for multiple choice questions
            data['answer'] = [
                sanitize_rich_text(item) if isinstance(item, str) else item
                for item in data['answer']
            ]

    room_pin = str(data.get('room_pin'))
    q_id = str(data.get('question_id'))
    answer = data.get('answer')

    room = room_states.get(room_pin)
    if not room:
        return {'error': 'Room not found'}

    player_info = room['players'].get(sid)
    if not player_info or player_info['role'] != 'client':
        return {'error': 'Unauthorized'}

    player_id = player_info['player_id']

    if 'gradings' not in room:
        room['gradings'] = {}
    if q_id not in room['gradings']:
        room['gradings'][q_id] = {}

    if q_id not in room['answers']:
        room['answers'][q_id] = {}
    room['answers'][q_id][player_id] = answer

    question = room['broadcasted_questions'].get(q_id)
    if not question:
        return {'error': 'Question not found'}

    q_type = question.get('type')
    correct_answer = question.get('reference_answer')

    is_correct = grade_answer(q_type, answer, correct_answer)
    grading_result = {'is_correct': is_correct, 'correct_answer': correct_answer}
    room['gradings'][q_id][player_id] = grading_result

    displayed_q = room.get('displayed_question')
    if displayed_q and str(displayed_q['id']) == q_id:
        answers_dict = room['answers'].get(q_id, {})
        stats, total = compute_stats(q_type, answers_dict)

        for target_sid, p in room['players'].items():
            if p['role'] == 'screen':
                await sio.emit(
                    'update_stats', {'stats': stats, 'total': total}, to=target_sid
                )

    await broadcast_room_state(room_pin)

    return grading_result


@sio.event
async def host_show_leaderboard(sid, data):
    room_pin = str(data.get('room_pin'))
    room = room_states.get(room_pin)
    if not room:
        return

    player_info = room['players'].get(sid)
    if not player_info or player_info['role'] != 'host':
        return

    room['current_screen'] = 'leaderboard'
    leaderboard = generate_leaderboard(room)

    print(f'🏆 Host triggered leaderboard for room {room_pin}')
    for target_sid, player in room['players'].items():
        if player['role'] == 'screen':
            await sio.emit(
                'show_leaderboard', {'leaderboard': leaderboard}, to=target_sid
            )


@sio.event
async def end_game(sid, data):
    room_pin = str(data.get('room_pin'))
    exam_id = data.get('exam_id')

    room = room_states.get(room_pin)
    if not room:
        return

    player_info = room['players'].get(sid)
    if not player_info or player_info['role'] != 'host':
        return

    print('🛑 Host ended game.')
    # --- Start Batch Submission Persistence Logic ---
    if exam_id and 'token' in room:
        print(f'🛑 Submitting batch data & cleaning up room {room_pin}')
        token = room['token']
        batch_payload = []

        for p_sid, p_data in room['players'].items():
            if p_data['role'] == 'client':
                player_id = p_data.get('player_id')
                student_db_id = p_data.get('student_db_id')

                answers_payload = []
                for q_id_str, student_answers in room.get('answers', {}).items():
                    if player_id in student_answers:
                        ans_content = student_answers[player_id]

                        if isinstance(ans_content, list):
                            ans_content_str = json.dumps(ans_content)
                        else:
                            ans_content_str = (
                                str(ans_content) if ans_content is not None else None
                            )

                        grading = (
                            room.get('gradings', {})
                            .get(q_id_str, {})
                            .get(player_id, {})
                        )

                        answers_payload.append(
                            {
                                'question_id': int(q_id_str),
                                'answer_content': ans_content_str,
                                'is_correct': grading.get('is_correct'),
                                'score': 100 if grading.get('is_correct') else 0,
                            }
                        )

                if answers_payload:
                    submission_payload = {
                        'exam_id': int(exam_id),
                        'student_id': student_db_id,
                        'guest_name': p_data['name'] if not student_db_id else None,
                        'answers': answers_payload,
                    }
                    batch_payload.append(submission_payload)

        # Execute ONE single HTTP request for the entire room
        if batch_payload:
            print(f'📦 Submitting a batch of {len(batch_payload)} student records...')
            await submit_batch_submissions(token, batch_payload)
            print('✅ Batch submission archived successfully.')
    # --- End Batch Submission Persistence Logic ---

    for target_sid, player in list(room['players'].items()):
        if target_sid != sid:
            await sio.emit(
                'error',
                {'message': 'The host has ended the game. Disconnecting...'},
                to=target_sid,
            )
            await sio.disconnect(target_sid)

    if room_pin in room_states:
        del room_states[room_pin]
