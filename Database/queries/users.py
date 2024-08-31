from Database.models import *
from Database.session import BaseDatabase
from sqlalchemy import *


from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_

class UsersQueries(BaseDatabase):
    # async def insert_user(self, tg_id: int, username: str):
    #     async with self.db()() as session:
    #         await session.execute(
    #             insert(models.Users).values(id=tg_id, username=username)
    #         )
    #         await session.commit()
    pass

    async def add_user(self, id, username):
        async with self.db() as session:
            try:
                new_user = Users(id=id, username=username)
                session.add(new_user)
                await session.commit()
            except:
                pass

    async def lst_of_users(self):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.user_id)
            )
            return result.fetchall()