from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Database URL (change as per your DB config)
DATABASE_URL = "postgresql+asyncpg://postgres:6666@localhost:5432/fast_db"

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
