import asyncio
import logging
import socket

from Bot.config import config
from Database.session import BaseDatabase
from Database.migrations.m20260419_add_smm_description_embedding import upgrade as upgrade_20260419


async def run_migrations() -> None:
    last_error = None
    for attempt in range(1, 11):
        try:
            database = BaseDatabase(config)
            async with database.session_manager.engine.begin() as conn:
                await upgrade_20260419(conn)
            return
        except socket.gaierror as exc:
            last_error = exc
            logging.warning(
                "Database host %s is not resolvable yet for migrations (attempt %s/10)",
                config.db.host,
                attempt,
            )
        except OSError as exc:
            last_error = exc
            logging.warning(
                "Database is not reachable at %s:%s for migrations yet (attempt %s/10): %s",
                config.db.host,
                config.db.port,
                attempt,
                exc,
            )

        if attempt == 10:
            raise last_error
        await asyncio.sleep(3)
