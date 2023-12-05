import psycopg2
from dotenv import dotenv_values


async def connect_db():
    config = dotenv_values(".env")
    db = psycopg2.connect(
        database=config["DATABASE"],
        user=config["USER"],
        password=config["PASSWORD"],
        host=config["HOST"],
        port=config["PORT"],
    )
    cursor = db.cursor()

    return db, cursor



async def disconnect_db(db,cursor):
    cursor.close()
    db.close()

async def get_all_target_audience():
    db, cur = await connect_db()
    cur.execute(f"""
               SELECT * FROM target_audience;
                """)
    ta = cur.fetchall()
    return ta
