from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config_core import settings

DATABASE_URL = getattr(settings, "DATABASE_URL", "sqlite+aiosqlite:///./finbank.db")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
print(DATABASE_URL)
print(engine.url)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
