import os
from typing import Dict

import httpx
import socketio
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

DATA_SERVICE_URL_BASE = os.getenv(
    'DATA_SERVICE_URL_BASE', 'http://host.docker.internal:8080'
)

DATA_SERVICE_TEACHER_AUTH_URL = f'{DATA_SERVICE_URL_BASE}/api/auth/login'
DATA_SERVICE_STUDENT_AUTH_URL = f'{DATA_SERVICE_URL_BASE}/api/auth/student'


# Initialize FastAPI app
fastapi_app = FastAPI()

# Initialize Socket.io AsyncServer
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Wrap FastAPI app with Socket.io ASGIApp
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# In-memory room state management
# Structure:
# {
#     "room_pin": {
#         "host_token": "eyJhbG...",
#         "players": {
#             "sid": {"role": "host", "name": "Host_Teacher", "student_id": "Host_Teacher"}
#         }
#     }
# }
room_states: Dict[str, dict] = {}


class StudentLoginParams(BaseModel):
    student_id: str
    password: str
    host_token: str


async def check_student_credentials(student_id: str, password: str, host_token: str):
    if not host_token:
        print('Error: No valid host token provided for this room.')
        return None

    headers = {'Authorization': f'Bearer {host_token}'}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                DATA_SERVICE_STUDENT_AUTH_URL,
                json={'student_id': student_id, 'password': password},
                headers=headers,
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


@fastapi_app.post('/api/auth/login')
async def host_login(form_data: OAuth2PasswordRequestForm = Depends()):
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
async def verify_student_endpoint(params: StudentLoginParams):
    """
    Verify student credentials by calling Data API.
    """
    student_info = await check_student_credentials(
        params.student_id, params.password, params.host_token
    )
    if not student_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Student verification failed',
        )
    return student_info


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
        # Initialize room state and save the host's token
        if room_pin not in room_states:
            room_states[room_pin] = {'host_token': token, 'players': {}}
        else:
            # Update token if host reconnects
            room_states[room_pin]['host_token'] = token

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

        host_token = room_states[room_pin].get('host_token')
        student_info = await check_student_credentials(student_id, password, host_token)

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
