from contextlib import asynccontextmanager

# Import core components
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, questions, students


# Lifespan context to initialize database
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan, title='Quizio Data API')

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Register API routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(questions.router)
