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
    await disconnect_db(db, cur)
    return ta


async def add_user(id, username):
    db, cur = await connect_db()
    cur.execute(f"""
                    INSERT INTO users(id, username) VALUES ({id}, '{username}') ON CONFLICT (id) DO NOTHING
                """)
    db.commit()
    await disconnect_db(db,cur)


async def get_smm_by_ta(ta):
    db, cur = await connect_db()
    cur.execute(f"""
                    SELECT full_name, age, town, photo
                    FROM smm 
                    INNER JOIN target_audience_smm
                    ON target_audience_smm.smm_id = smm.id
                    WHERE target_audience_id = {ta} 
                """)
    smm = cur.fetchall()
    await disconnect_db(db, cur)
    return smm
