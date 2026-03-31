import os
from typing import Dict

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status

DATA_SERVICE_URL_BASE = os.getenv(
    'DATA_SERVICE_URL_BASE', 'http://host.docker.internal:8080'
)

DATA_SERVICE_AUTH_URL = f'{DATA_SERVICE_URL_BASE}/api/auth/student'

DATA_SERVICE_ADMIN_USERNAME = os.getenv('DATA_SERVICE_ADMIN_USERNAME', 'admin')

DATA_SERVICE_ADMIN_PASSWORD = os.getenv('DATA_SERVICE_ADMIN_PASSWORD', 'admin123')

CURRENT_DATA_SERVICE_TOKEN = ''


class GameManager:
    def __init__(self):
        self.rooms: Dict[str, Dict[str, dict]] = {}

    def is_player_in_room(self, room_pin: str, student_id: str) -> bool:
        return room_pin in self.rooms and student_id in self.rooms[room_pin]

    async def connect(
        self, websocket: WebSocket, room_pin: str, student_id: str, player_name: str
    ):
        await websocket.accept()
        if room_pin not in self.rooms:
            self.rooms[room_pin] = {}

        self.rooms[room_pin][student_id] = {'ws': websocket, 'name': player_name}
        await self.broadcast_room_state(room_pin)

    def disconnect(self, room_pin: str, student_id: str):
        if room_pin in self.rooms and student_id in self.rooms[room_pin]:
            del self.rooms[room_pin][student_id]
            if not self.rooms[room_pin]:
                del self.rooms[room_pin]

    async def broadcast_room_state(self, room_pin: str):
        if room_pin in self.rooms:
            players = [
                player_data['name'] for player_data in self.rooms[room_pin].values()
            ]
            message = {
                'type': 'room_state',
                'data': {'room_pin': room_pin, 'players': players},
            }
            for player_data in self.rooms[room_pin].values():
                await player_data['ws'].send_json(message)


async def verify_student(student_id: str, password: str):
    """
    Verify student credentials by calling the local 'quizio-data' API.
    """
    # 確保 Token 不是空的
    if not CURRENT_DATA_SERVICE_TOKEN:
        print('❌ 錯誤：沒有有效的 JWT，請確認伺服器啟動時是否有成功登入。')
        return None

    headers = {'Authorization': f'Bearer {CURRENT_DATA_SERVICE_TOKEN}'}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                DATA_SERVICE_AUTH_URL,
                json={'student_id': student_id, 'password': password},
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f'❌ 學生驗證失敗: 回傳狀態碼 {response.status_code} - {response.text}'
                )
                return None
        except Exception as e:
            print(f'❌ 網路連線錯誤 (無法連線至 quizio-data): {e}')
            return None


app = FastAPI()
manager = GameManager()


@app.on_event('startup')
async def startup_event():
    global CURRENT_DATA_SERVICE_TOKEN
    print(f'🔄 正在向資料中心 ({DATA_SERVICE_URL_BASE}) 申請存取權杖 (JWT)...')

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f'{DATA_SERVICE_URL_BASE}/api/auth/login',
                data={
                    'username': DATA_SERVICE_ADMIN_USERNAME,
                    'password': DATA_SERVICE_ADMIN_PASSWORD,
                },
                timeout=5.0,
            )
            response.raise_for_status()
            CURRENT_DATA_SERVICE_TOKEN = response.json()['access_token']
            print('✅ 成功取得 JWT 權杖！遊戲引擎已連線至資料中心。')
        except Exception as e:
            # 新增：更詳細的啟動失敗提示
            print(
                f'❌ 無法取得權杖！請確認：\n1. quizio-data 伺服器是否運行中。\n2. 帳號密碼是否正確。\n錯誤訊息: {e}'
            )


@app.websocket('/ws/{room_pin}/{student_id}/{password}')
async def websocket_endpoint(
    websocket: WebSocket, room_pin: str, student_id: str, password: str
):
    if student_id == 'Host_Teacher':
        player_name = 'Host_Teacher'
    else:
        student_info = await verify_student(student_id, password)
        if not student_info:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        player_name = student_info['name']

        if manager.is_player_in_room(room_pin, student_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await manager.connect(websocket, room_pin, student_id, player_name)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(room_pin, student_id)
        await manager.broadcast_room_state(room_pin)
