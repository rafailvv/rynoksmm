from Database.models import *
from Database.session import BaseDatabase
from sqlalchemy import *

from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_

class TaQueries(BaseDatabase):
    # async def insert_user(self, tg_id: int, username: str):
    #     async with self.db()()() as session:
    #         await session.execute(
    #             insert(models.Users).values(id=tg_id, username=username)
    #         )
    #         await session.commit()
    async def get_ta_by_field(self, f):
        async with self.db() as session:
            result = await session.execute(
                select(TargetAudience.name)
                .where(TargetAudience.category == f)
            )
            return result.fetchall()

    async def get_all_field(self):
        async with self.db() as session:
            result = await session.execute(
                select(TargetAudience.category).distinct()
            )
            return result.fetchall()

    async def get_ta_id(self, ta):
        async with self.db() as session:
            result = await session.execute(
                select(TargetAudience.id).where(TargetAudience.name == ta)
            )
            return result.scalar()

    async def add_ta(self, id, t):
        async with self.db() as session:
            for ta in t:
                ta_id = await self.get_ta_id(ta)
                new_ta_smm = TargetAudienceSmm(smm_id=id, target_audience_id=ta_id)
                session.add(new_ta_smm)
            await session.commit()

    async def get_all_ta(self):
        async with self.db() as session:
            result = await session.execute(
                select(TargetAudience.name, TargetAudience.category)
            )
            return result.fetchall()

    async def delete_user_ta(self, user_id):
        async with self.db() as session:
            await session.execute(
                delete(TargetAudienceSmm).where(TargetAudienceSmm.smm_id == user_id)
            )
            await session.commit()

    async def get_ta_by_user_id(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(TargetAudienceSmm.target_audience_id).where(TargetAudienceSmm.smm_id == user_id)
            )
            return result.fetchall()