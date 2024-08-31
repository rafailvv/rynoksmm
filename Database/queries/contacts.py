from Database.models import *
from Database.session import BaseDatabase
from sqlalchemy import *

from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_


class ContactsQueries(BaseDatabase):
    # async def insert_user(self, tg_id: int, username: str):
    #     async with self.db()() as session:
    #         await session.execute(
    #             insert(models.Users).values(id=tg_id, username=username)
    #         )
    #         await session.commit()
    async def add_bought_contact(self, user_id, smm_id):
        async with self.db() as session:
            new_contact = Contacts(user_id=user_id, smm_id=smm_id)
            session.add(new_contact)
            await session.commit()

    async def get_bought_contacts(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(Contacts.smm_id).where(Contacts.user_id == user_id)
            )
            list_of_smm_id = result.fetchall()
            dict_of_smm = {}
            for smm_id in list_of_smm_id:
                dict_of_smm[smm_id[0]] = list(await self.get_profile_by_id_str(smm_id[0]))
            return dict_of_smm

    async def get_profile_by_id_str(self, id):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.id, Smm.full_name, Smm.phone, Smm.user_id, Smm.age, Smm.town, Smm.cost, Smm.photo,
                       Users.username, Smm.description)
                .join(Users, Users.id == Smm.user_id)
                .where(Smm.user_id == id)
            )
            return result.fetchone()

