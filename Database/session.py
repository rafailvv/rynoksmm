import asyncio
import logging
import socket
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
        database_url = (
            f"postgresql+asyncpg://{config.db.user}:{config.db.password}"
            f"@{config.db.host}:{config.db.port}/{config.db.database}"
        )

        self.session_manager = SessionManager(database_url)
        self.db = self.session_manager.get_session()

    async def init_db(self):
        last_error = None
        for attempt in range(1, 11):
            try:
                await self.session_manager.create_db()
                return
            except socket.gaierror as exc:
                last_error = exc
                logging.warning(
                    "Database host %s is not resolvable yet (attempt %s/10)",
                    config.db.host,
                    attempt,
                )
            except OSError as exc:
                last_error = exc
                logging.warning(
                    "Database is not reachable at %s:%s yet (attempt %s/10): %s",
                    config.db.host,
                    config.db.port,
                    attempt,
                    exc,
                )

            if attempt == 10:
                raise last_error
            await asyncio.sleep(3)

async def get_db():
    bd = BaseDatabase(config=config)
    async with bd.db() as session:
        yield session
