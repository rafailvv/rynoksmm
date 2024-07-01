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


async def disconnect_db(db, cursor):
    cursor.close()
    db.close()


async def get_profile_by_id(id):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    SELECT (smm.id, full_name, phone, user_id, age, town, cost, photo, username) 
                    FROM smm
                    INNER JOIN users
                    ON users.id = smm.user_id
                    WHERE user_id = {id}
                """
    )
    profile = cur.fetchone()
    await disconnect_db(db, cur)
    return profile


async def get_ta_by_field(f):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    SELECT name FROM target_audience WHERE category='{f}'; 
                """
    )
    ta = cur.fetchall()
    await disconnect_db(db, cur)
    return ta


async def get_all_field():
    db, cur = await connect_db()
    cur.execute(
        f"""
                    SELECT DISTINCT category FROM target_audience;
                """
    )
    ta = cur.fetchall()
    await disconnect_db(db, cur)
    return ta


async def add_user(id, username):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    INSERT INTO users(id, username) VALUES ({id}, '{username}') ON CONFLICT (id) DO NOTHING
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def get_smm_by_ta(t):
    db, cur = await connect_db()

    tn = []
    for ta in t:
        if ta[0] == "✅":
            tn.append(await get_ta_id(ta[2:]))
    t = tn
    if len(t) > 1:
        cur.execute(
            f"""
                        SELECT full_name, age, town, photo, cost, user_id
                        FROM smm 
                        INNER JOIN target_audience_smm
                        ON target_audience_smm.smm_id = smm.user_id
                        WHERE target_audience_id IN {tuple(t)} 
                    """
        )
    else:
        cur.execute(
            f"""
                        SELECT full_name, age, town, photo, cost, user_id
                        FROM smm 
                        INNER JOIN target_audience_smm
                        ON target_audience_smm.smm_id = smm.user_id
                        WHERE target_audience_id = '{t[0]}' 
                    """
        )
    smm = cur.fetchall()
    dict_of_smm = dict()  # Словарь из смм
    for (
        x
    ) in (
        smm
    ):  # Идем по всем смм, у которых хотя бы какая-то ца есть в помеченных галочкой
        v = dict_of_smm.get(x[-1], list(x[:-1]) + [0])
        dict_of_smm[x[-1]] = v[:-1] + [
            v[-1] + 1
        ]  # Если человек уже в словаре - добавляем к кол-ву его вхождений +1, если нету, создаем с 0 и делаем +1
    dict_of_smm = sorted(
        dict_of_smm.items(), key=lambda x: -x[1][-1]
    )  # Сортируем по кол-ву вхождений - чем больше => больше всего совпадающих ца
    await disconnect_db(db, cur)
    return dict_of_smm


async def add_smm(user_id):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    INSERT INTO smm(user_id) VALUES ({user_id}) ON CONFLICT (user_id) DO NOTHING
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def add_fullname(user_id, fullname):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    UPDATE smm SET full_name = '{fullname}' WHERE user_id = {user_id}
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def add_phone(user_id, phone):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    UPDATE smm SET phone = '{phone}' WHERE user_id = {user_id}
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def add_age(user_id, age):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    UPDATE smm SET age = {age} WHERE user_id = {user_id}
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def add_town(user_id, town):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    UPDATE smm SET town = '{town}' WHERE user_id = {user_id}
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def add_photo(user_id, photo):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    UPDATE smm SET photo = '{photo}' WHERE user_id = {user_id}
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def add_cost(user_id, cost):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    UPDATE smm SET cost = {cost} WHERE user_id = {user_id}
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def get_ta_id(ta):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    SELECT id FROM target_audience WHERE name = '{ta}'
                """
    )
    ta_id = cur.fetchone()
    ta_id = int(ta_id[0])
    await disconnect_db(db, cur)
    return ta_id


async def add_ta(id, t):
    db, cur = await connect_db()
    for ta in t:
        if ta[0] == "✅":
            #  ON CONFLICT (smm_id, target_audience_id) DO NOTHING
            cur.execute(
                f"""
                            INSERT INTO target_audience_smm(smm_id, target_audience_id) VALUES ({id}, {await get_ta_id(ta[2:])})
                        """
            )
    db.commit()
    await disconnect_db(db, cur)


async def add_bought_contact(user_id, smm_id):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    INSERT INTO contacts(user_id, smm_id) 
                    VALUES ({user_id}, {smm_id})
                """
    )
    db.commit()
    await disconnect_db(db, cur)


async def get_bought_contacts(user_id):
    db, cur = await connect_db()
    cur.execute(
        f"""
                    SELECT smm_id FROM contacts WHERE user_id = {user_id}
                """
    )
    list_of_smm_id = cur.fetchall()
    dict_of_smm = dict()
    for smm_id in list_of_smm_id:
        dict_of_smm[smm_id[0]] = await get_profile_by_id(smm_id[0])
    await disconnect_db(db, cur)
    return dict_of_smm


async def updt_user(user_id, fullname, phone, age, town, cost):
    db, cur = await connect_db()
    cur.execute(f"""
                UPDATE smm SET full_name='{fullname}',
                               phone='{phone}',
                               age={age},
                               town='{town}',
                               cost={cost}
                WHERE user_id={user_id}
                """)
    db.commit()
    await disconnect_db(db, cur)


async def get_category_by_smm(user_id):
    db, cur = await connect_db()
    cur.execute(f"""
                    SELECT name, category FROM target_audience
                    INNER JOIN target_audience_smm ON target_audience_smm.target_audience_id = target_audience.id
                    WHERE target_audience_smm.smm_id = {user_id}
                    """)
    ta = cur.fetchall()
    await disconnect_db(db, cur)
    return ta


async def get_all_ta():
    db, cur = await connect_db()
    cur.execute(f"""
                    SELECT name, category FROM target_audience
                """)
    ta = cur.fetchall()
    await disconnect_db(db, cur)
    return ta


async def delete_user_ta(user_id):
    db, cur = await connect_db()
    cur.execute(f"""
                        DELETE FROM target_audience_smm WHERE smm_id = {user_id}
                    """)
    db.commit()
    await disconnect_db(db, cur)


async def lst_of_users():
    db, cur = await connect_db()
    cur.execute(f"""
                    SELECT user_id FROM smm
                        """)
    ans = cur.fetchall()
    await disconnect_db(db, cur)
    return ans


async def edit_categories(categories):
    print(categories.categories)
    db, cur = await connect_db()
    cur.execute(f"DELETE FROM target_audience_smm WHERE smm_id = {categories.user_id}")
    for category in categories.categories:
        cur.execute(f"INSERT INTO target_audience_smm (smm_id, target_audience_id) VALUES ({categories.user_id}, {await get_ta_id(category)})")
    db.commit()
    await disconnect_db(db, cur)


async def get_phone_by_user_id(user_id):
    db, cur = await connect_db()
    cur.execute(f"""
                    SELECT phone FROM smm WHERE user_id = {user_id}
                        """)
    phone = cur.fetchone()
    await disconnect_db(db, cur)
    return phone


async def get_tg_by_user_id(user_id):
    db, cur = await connect_db()
    cur.execute(f"""
                    SELECT username FROM users WHERE id = {user_id}
                        """)
    username = cur.fetchone()
    await disconnect_db(db, cur)
    return username
