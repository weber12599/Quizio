import os
from typing import Dict

import httpx
import socketio
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

DATA_SERVICE_URL_BASE = os.getenv('DATA_SERVICE_URL_BASE')

DATA_SERVICE_TEACHER_AUTH_URL = f'{DATA_SERVICE_URL_BASE}/api/auth/login'
DATA_SERVICE_STUDENT_AUTH_URL = f'{DATA_SERVICE_URL_BASE}/api/auth/student'


# Initialize FastAPI app
fastapi_app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

# Initialize Socket.io AsyncServer
sio = socketio.AsyncServer(
    async_mode='asgi', cors_allowed_origins='*', ping_interval=25, ping_timeout=120
)

# Wrap FastAPI app with Socket.io ASGIApp
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# In-memory room state management
# Structure:
# {
#     "room_pin": {
#         "token": "eyJhbG...",
#         "players": {
#             "sid": {"role": "host", "name": "Host_Teacher", "student_id": "Host_Teacher"}
#         }
#     }
# }
room_states: Dict[str, dict] = {}


class StudentLoginParams(BaseModel):
    student_id: str
    password: str
    token: str


async def check_student_credentials(student_id: str, password: str, token: str):
    if not token:
        print('Error: No valid host token provided for this room.')
        return None

    auth_header = f'Bearer {token}'

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                DATA_SERVICE_STUDENT_AUTH_URL,
                json={'student_id': student_id, 'password': password},
                headers={'Authorization': auth_header},
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f'Student verification failed: {response.status_code} - {response.text}'
                )
                return None
        except Exception as e:
            print(f'Network error (cannot connect to quizio-data): {e}')
            return None


def grade_answer(q_type: str, student_answer: any, correct_answer: any) -> bool:
    """
    Evaluate student's answer based on the question type.
    """
    if not correct_answer:
        return False

    if q_type == 'essay':
        # Essay requires manual grading, return False by default
        return False

    if q_type == 'multiple':
        # For multiple choices, check if both are lists and have exact same elements
        if not isinstance(student_answer, list) or not isinstance(correct_answer, list):
            return False
        return set(student_answer) == set(correct_answer)

    if q_type in ['single', 'boolean']:
        return str(student_answer).strip() == str(correct_answer).strip()

    if q_type == 'short':
        # Case-insensitive and trimmed string comparison for short answers
        return (
            str(student_answer).strip().lower() == str(correct_answer).strip().lower()
        )

    return False


def compute_stats(q_type: str, answers_dict: dict) -> tuple:
    """
    Compute answer statistics for the bar charts.
    Returns: (stats_dict, total_count)
    """
    stats = {}
    total = len(answers_dict)

    for sid, ans in answers_dict.items():
        if q_type == 'multiple' and isinstance(ans, list):
            for a in ans:
                stats[str(a)] = stats.get(str(a), 0) + 1
        elif q_type == 'boolean':
            # True maps to index "0", False maps to index "1"
            ans_idx = '0' if ans else '1'
            stats[ans_idx] = stats.get(ans_idx, 0) + 1
        elif q_type == 'single':
            stats[str(ans)] = stats.get(str(ans), 0) + 1

    return stats, total


def generate_leaderboard(room: dict) -> list:
    """Helper function to calculate scores and generate leaderboard."""
    scores = {}
    names = {}

    for p_sid, p in room['players'].items():
        if p['role'] == 'client':
            st_id = p['student_id']
            scores[st_id] = 0
            names[st_id] = p['name']

    gradings = room.get('gradings', {})
    for q_id, q_gradings in gradings.items():
        for st_id, result in q_gradings.items():
            if result.get('is_correct'):
                scores[st_id] = scores.get(st_id, 0) + 100

    leaderboard = [
        {'name': names.get(st_id, 'Unknown'), 'score': score}
        for st_id, score in scores.items()
    ]
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return leaderboard


@fastapi_app.post('/api/auth/login')
async def proxy_auth_teacher(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate host (teacher) by verifying credentials against Data Backend.
    Returns the JWT token if successful.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                DATA_SERVICE_TEACHER_AUTH_URL,
                data={'username': form_data.username, 'password': form_data.password},
                timeout=5.0,
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Incorrect username or password',
                )
            return response.json()
        except httpx.RequestError as e:
            print(f'Login proxy error: {e}')
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail='Data service is unavailable',
            )


@fastapi_app.post('/api/auth/student')
async def proxy_auth_student(params: StudentLoginParams):
    """
    Verify student credentials by calling Data API.
    """
    student_info = await check_student_credentials(
        params.student_id, params.password, params.token
    )
    if not student_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Student verification failed',
        )
    return student_info


@fastapi_app.get('/api/exams/')
async def proxy_get_my_exams(token: str = Depends(oauth2_scheme)):
    """
    Proxy request to get the currently logged-in teacher's exams.
    Extracts the Authorization header and passes it to the Data Backend.
    """
    auth_header = f'Bearer {token}'

    async with httpx.AsyncClient() as client:
        # Request Data Backend's /api/exams/ endpoint (exact match with trailing slash)
        response = await client.get(
            f'{DATA_SERVICE_URL_BASE}/api/exams/',
            headers={'Authorization': auth_header},
            timeout=5.0,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@fastapi_app.get('/api/exams/{exam_id}')
async def proxy_get_exam_details(exam_id: int, token: str = Depends(oauth2_scheme)):
    """
    Proxy request to get a specific exam with its questions.
    """
    auth_header = f'Bearer {token}'

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'{DATA_SERVICE_URL_BASE}/api/exams/{exam_id}',
            headers={'Authorization': auth_header},
            timeout=5.0,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@sio.event
async def connect(sid, environ):
    print(f'Client connected: {sid}')


@sio.event
async def disconnect(sid):
    print(f'Client disconnected: {sid}')
    for room_pin, room_data in list(room_states.items()):
        players = room_data['players']
        if sid in players:
            del players[sid]
            # Clean up the room if everyone left
            if not players:
                del room_states[room_pin]
            else:
                await broadcast_room_state(room_pin)
            break


@sio.event
async def join_room(sid, data):
    """
    Client requests to join a room.
    Host must provide the JWT token in data['token'] to initialize the room.
    """
    room_pin = str(data.get('room_pin'))

    role = data.get('role')
    student_id = data.get('student_id')
    password = data.get('password')
    token = data.get('token')

    player_name = 'Unknown'

    if role == 'host':
        player_name = 'Host_Teacher'
        if room_pin not in room_states:
            room_states[room_pin] = {
                'token': token,
                'players': {},
                'broadcasted_questions': {},
                'displayed_question': None,
                'answers': {},
                'gradings': {},
                'current_screen': 'lobby',
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

        token = room_states[room_pin].get('token')
        student_info = await check_student_credentials(student_id, password, token)

        if not student_info:
            await sio.emit(
                'error',
                {'message': 'Verification failed or student not in your class'},
                to=sid,
            )
            await sio.disconnect(sid)
            return

        player_name = student_info['name']

    else:
        await sio.disconnect(sid)
        return

    room_states[room_pin]['players'][sid] = {
        'role': role,
        'name': player_name,
        'student_id': student_id,
    }

    print(f'✅ {player_name} ({role}) joined room {room_pin}')

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

        # Recover questions but STRIP reference_answer
        broadcasted = []
        for q in room.get('broadcasted_questions', {}).values():
            client_q = q.copy()
            client_q.pop('reference_answer', None)  # Prevent cheating
            broadcasted.append(client_q)

        if broadcasted:
            await sio.emit('new_questions', {'questions': broadcasted}, to=sid)

        # Recover answers AND gradings
        recovered_answers = {}
        recovered_gradings = {}

        answers_dict = room.get('answers', {})
        for q_id, student_answers in answers_dict.items():
            if student_id in student_answers:
                recovered_answers[q_id] = student_answers[student_id]

        gradings_dict = room.get('gradings', {})
        for q_id, student_gradings in gradings_dict.items():
            if student_id in student_gradings:
                recovered_gradings[q_id] = student_gradings[student_id]

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
    """
    Broadcast current players in the room to everyone in that room.
    """
    if room_pin in room_states:
        players_dict = room_states[room_pin]['players']
        players_list = [
            client_data['name']
            for client_data in players_dict.values()
            if client_data['role'] == 'client'
        ]

        print(
            f'📡 Ready for broadcasting room state to room {room_pin} ({len(players_dict)} connections): {players_list}'
        )

        for target_sid in players_dict.keys():
            await sio.emit(
                'room_state',
                {'room_pin': room_pin, 'players': players_list},
                to=target_sid,
            )
        print('✅ Done')


@sio.event
async def host_broadcast_questions(sid, data):
    """
    Host selects multiple questions and broadcasts them to clients.
    """
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
            room['broadcasted_questions'][q_id] = q  # Store full question in backend
            room['answers'][q_id] = {}

            # Create a safe copy for clients without the correct answer
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
    """
    Host selects a specific question to display on the Projector Screen,
    or sends null to clear the screen.
    """
    room_pin = str(data.get('room_pin'))
    question = data.get('question')  # Nullable

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

            # 🚀 NEW: Sync existing stats immediately upon displaying
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
    """
    Receive student's answer, grade it, save state, and return the grading result.
    """
    room_pin = str(data.get('room_pin'))
    q_id = str(data.get('question_id'))
    answer = data.get('answer')

    room = room_states.get(room_pin)
    if not room:
        return {'error': 'Room not found'}

    player_info = room['players'].get(sid)
    if not player_info or player_info['role'] != 'client':
        return {'error': 'Unauthorized'}

    student_id = player_info['student_id']

    # Initialize gradings dict if it doesn't exist
    if 'gradings' not in room:
        room['gradings'] = {}
    if q_id not in room['gradings']:
        room['gradings'][q_id] = {}

    # Save student's answer
    if q_id not in room['answers']:
        room['answers'][q_id] = {}
    room['answers'][q_id][student_id] = answer

    # Retrieve question data to get the reference_answer
    question = room['broadcasted_questions'].get(q_id)
    if not question:
        return {'error': 'Question not found'}

    q_type = question.get('type')
    correct_answer = question.get('reference_answer')

    # Evaluate the answer
    is_correct = grade_answer(q_type, answer, correct_answer)

    # Prepare grading result
    grading_result = {'is_correct': is_correct, 'correct_answer': correct_answer}

    # Save grading state for future reconnection recovery
    room['gradings'][q_id][student_id] = grading_result

    # Update stats instantly if this question is currently being displayed
    displayed_q = room.get('displayed_question')
    if displayed_q and str(displayed_q['id']) == q_id:
        answers_dict = room['answers'].get(q_id, {})
        stats, total = compute_stats(q_type, answers_dict)

        for target_sid, p in room['players'].items():
            if p['role'] == 'screen':
                await sio.emit(
                    'update_stats', {'stats': stats, 'total': total}, to=target_sid
                )

    # Return to trigger frontend acknowledgement callback
    return grading_result


@sio.event
async def host_show_leaderboard(sid, data):
    """
    Calculate scores and broadcast leaderboard to the screen.
    """
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
    """
    Host ends the game. Disconnect everyone and completely clean up memory.
    """
    room_pin = str(data.get('room_pin'))
    room = room_states.get(room_pin)
    if not room:
        return

    player_info = room['players'].get(sid)
    if not player_info or player_info['role'] != 'host':
        return

    print(f'🛑 Host ended game. Cleaning up room {room_pin}')

    # Notify and disconnect all other players (students and screen)
    for target_sid, player in list(room['players'].items()):
        if target_sid != sid:
            await sio.emit(
                'error',
                {'message': 'The host has ended the game. Disconnecting...'},
                to=target_sid,
            )
            await sio.disconnect(target_sid)

    # Clean up room memory dictionary
    if room_pin in room_states:
        del room_states[room_pin]
