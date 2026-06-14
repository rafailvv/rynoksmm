from sqlalchemy import inspect, text


async def upgrade(conn) -> None:
    def _get_columns(sync_conn):
        inspector = inspect(sync_conn)
        if "smm" not in inspector.get_table_names():
            return None
        return {col["name"] for col in inspector.get_columns("smm")}

    columns = await conn.run_sync(_get_columns)
    if columns is None:
        return

    if "description_embedding" in columns:
        return

    await conn.execute(text("ALTER TABLE smm ADD COLUMN description_embedding JSON"))
