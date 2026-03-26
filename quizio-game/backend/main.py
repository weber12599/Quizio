from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from typing import Dict


class GameManager:
    def __init__(self):
        # Format: { 'room_pin': { 'student_id': {'ws': WebSocket, 'name': str} } }
        self.rooms: Dict[str, Dict[str, dict]] = {}

    def is_player_in_room(self, room_pin: str, student_id: str) -> bool:
        '''Check if a student_id is already taken in the room.'''
        return room_pin in self.rooms and student_id in self.rooms[room_pin]

    async def connect(self, websocket: WebSocket, room_pin: str, student_id: str, player_name: str):
        await websocket.accept()
        if room_pin not in self.rooms:
            self.rooms[room_pin] = {}
        
        # Store both WebSocket connection and the verified player name
        self.rooms[room_pin][student_id] = {
            'ws': websocket,
            'name': player_name
        }
        await self.broadcast_room_state(room_pin)

    def disconnect(self, room_pin: str, student_id: str):
        if room_pin in self.rooms and student_id in self.rooms[room_pin]:
            del self.rooms[room_pin][student_id]
            if not self.rooms[room_pin]:
                del self.rooms[room_pin]

    async def broadcast_room_state(self, room_pin: str):
        if room_pin in self.rooms:
            # Extract names for the frontend display
            players = [player_data['name'] for player_data in self.rooms[room_pin].values()]
            message = {
                'type': 'room_state',
                'data': {
                    'room_pin': room_pin,
                    'players': players
                }
            }
            # Send to all websockets in the room
            for player_data in self.rooms[room_pin].values():
                await player_data['ws'].send_json(message)

async def verify_student(room_pin: str, student_id: str, password: str):
    '''
    Verify student credentials. 
    Currently using a mock logic for testing. Later, this will call the API service.
    '''
    if password == '1234':
        return {'name': f'Student {student_id}'}
    return None


app = FastAPI()
manager = GameManager()


# Route updated to use student_id
@app.websocket('/ws/{room_pin}/{student_id}/{password}')
async def websocket_endpoint(websocket: WebSocket, room_pin: str, student_id: str, password: str):
    # 1. Verify identity (Teacher host bypasses verification)
    if student_id == 'Host_Teacher':
        player_name = 'Host_Teacher'
    else:
        student_info = await verify_student(room_pin, student_id, password)
        if not student_info:
            # Reject connection if verification fails
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        player_name = student_info['name']

        # 2. Anti-hijacking check based on student_id
        if manager.is_player_in_room(room_pin, student_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    # 3. Accept connection and join room
    await manager.connect(websocket, room_pin, student_id, player_name)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(room_pin, student_id)
        await manager.broadcast_room_state(room_pin)
