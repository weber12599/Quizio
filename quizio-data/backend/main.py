import asyncio
import os
from contextlib import asynccontextmanager

import models
from core.security import get_password_hash
from core.tasks import media_garbage_collection_task

# Ensure this matches the name of your async session maker in database.py
from database import AsyncSessionLocal
from fastapi import FastAPI

# Import all your routers
from routers import auth, exams, media, questions, students, submissions, users
from sqlalchemy import select

# Load initial admin credentials from environment variables
# Provide default values just in case they are missing during local dev
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ==========================================
    # Startup Event Logic
    # ==========================================
    print('Starting up: Checking database initialization...')

    # Open an async session to interact with the database
    async with AsyncSessionLocal() as db:
        # 1. Check if the superuser already exists
        result = await db.execute(
            select(models.User).where(models.User.username == ADMIN_USERNAME)
        )
        admin_user = result.scalars().first()

        # 2. If not found, create the initial superuser directly via models
        if not admin_user:
            print(f"Superuser '{ADMIN_USERNAME}' not found. Creating one now...")

            new_admin = models.User(
                username=ADMIN_USERNAME,
                email=None,
                full_name='System Administrator',
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                is_superuser=True,
            )

            db.add(new_admin)
            await db.commit()
            print('Superuser created successfully!')
        else:
            print(f"Superuser '{ADMIN_USERNAME}' already exists. Skipping creation.")

    # Start the background Garbage Collection task
    print('Starting background task: Media Garbage Collection...')
    gc_task = asyncio.create_task(media_garbage_collection_task())

    # Yield control back to FastAPI to start accepting requests
    yield

    # ==========================================
    # Shutdown Event Logic
    # ==========================================
    print('Shutting down the application safely...')

    # Gracefully cancel the GC task when the server shuts down
    gc_task.cancel()
    try:
        await gc_task
    except asyncio.CancelledError:
        print('Background Garbage Collection task cancelled successfully.')


# Initialize the FastAPI app and attach the lifespan context manager
app = FastAPI(
    title='Quizio Data API',
    description='API document for Quizio Data',
    version='0.1.4',
    lifespan=lifespan,
)

# Register all routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(students.router)
app.include_router(questions.router)
app.include_router(exams.router)
app.include_router(media.router)
app.include_router(submissions.router)
