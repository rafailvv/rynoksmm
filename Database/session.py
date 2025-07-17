import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from Bot.config import config

Base = declarative_base()


class SessionManager:
    def __init__(self, database_url) -> None:
        self.engine = create_async_engine(database_url, echo=False)
        self.session_local = sessionmaker(
            bind=self.engine, expire_on_commit=False, class_=AsyncSession
        )

    def get_session(self):
        return self.session_local

    async def create_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


class BaseDatabase:
    def __init__(self, config):
        database_url = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.database}"

        self.session_manager = SessionManager(database_url)
        self.db = self.session_manager.get_session()

    async def init_db(self):
        await self.session_manager.create_db()

async def get_db():
    bd = BaseDatabase(config=config)
    async with bd.db() as session:
        yield session