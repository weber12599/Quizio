import socketio
from fastapi import FastAPI
from routers import router as api_router
from sockets import sio

fastapi_app = FastAPI()
fastapi_app.include_router(api_router)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
