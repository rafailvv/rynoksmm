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

    async def add_support_request(self, request, user_id, tg_url):
        async with self.db() as session:
            support_request = Support(request=request, user_id=user_id, answered=0, tg_url=tg_url)
            session.add(support_request)
            await session.commit()

    async def get_support_requests(self):
        async with self.db() as session:
            result = await session.execute(
                select(Support.request, Support.user_id, Support.tg_url).where(Support.answered == 0)
            )
            return result.fetchall()

    async def answer_request(self, request, user_id):
        async with self.db() as session:
            support_request = await session.execute(
                update(Support).where(Support.request == request).where(Support.user_id == user_id).values(answered=1)
            )
            await session.commit()

    async def is_answered(self, request, user_id):
        async with self.db() as session:
            support_request = await session.execute(
                select(Support.answered).where(Support.request == request).where(Support.user_id == user_id)
            )

            return support_request == 1

    async def get_purchase_by_payment_id(self, payment_id):
        async with self.db() as session:
            result = await session.execute(
                select(Payments).where(Payments.payment_id == payment_id)
            )

            return result.first()
