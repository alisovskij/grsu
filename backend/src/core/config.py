import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from redis.asyncio import Redis

redis = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/1"), decode_responses=True)

DATABASE_URL = 'postgresql+asyncpg://grsu:1111@db/grsudb'
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with async_session() as session:
        yield session