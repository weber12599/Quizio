import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Fetch database URL from environment variable
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+asyncpg://quizio_admin:your_secure_db_password@db:5432/quizio_data',
)

# Create asynchronous database engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

Base = declarative_base()


# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
