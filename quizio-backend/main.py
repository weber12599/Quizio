from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        # Store all active websocket connections
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # Accept the connection and add it to the active list
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        # Remove the disconnected websocket from the list
        self.active_connections.remove(websocket)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # Handle incoming client connection
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive and wait for incoming messages
            # For now, we just receive the data without processing game logic
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        # Handle client disconnection
        manager.disconnect(websocket)