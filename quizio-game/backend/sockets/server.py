import socketio

sio = socketio.AsyncServer(
    async_mode='asgi', cors_allowed_origins='*', ping_interval=25, ping_timeout=120
)
