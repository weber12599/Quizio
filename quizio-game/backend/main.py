import socketio
from fastapi import FastAPI
from routers import router as api_router
from sockets import sio

fastapi_app = FastAPI(
    title='Quizio Game API',
    description='API document for Quizio Game',
    version='0.2.0',
)
fastapi_app.include_router(api_router)

app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
