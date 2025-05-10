from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = 'postgresql+asyncpg://grsu:1111@db/grsudb'
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with async_session() as session:
        yield session