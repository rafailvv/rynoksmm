from Database.models import *
from Database.session import BaseDatabase
from sqlalchemy import *

from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_


class SmmQueries(BaseDatabase):
    # async def insert_user(self, tg_id: int, username: str):
    #     async with self.db()() as session:
    #         await session.execute(
    #             insert(models.Users).values(id=tg_id, username=username)
    #         )
    #         await session.commit()

    async def get_ta_id(self, ta):
        async with self.db() as session:
            result = await session.execute(
                select(TargetAudience.id).where(TargetAudience.name == ta)
            )
            return result.scalar()

    async def get_smm_by_ta(self, t):
        async with self.db() as session:
            print(t)
            tn = [await self.get_ta_id(ta) for ta in t]
            print(tn)
            if len(tn) > 1:
                result = await session.execute(
                    select(Smm.full_name, Smm.age, Smm.town, Smm.photo, Smm.cost, Smm.description, Smm.user_id)
                    .join(TargetAudienceSmm, TargetAudienceSmm.smm_id == Smm.user_id)
                    .where(TargetAudienceSmm.target_audience_id.in_(tn), Smm.date_sub > datetime.utcnow())
                )
            elif len(tn) == 1:
                result = await session.execute(
                    select(Smm.full_name, Smm.age, Smm.town, Smm.photo, Smm.cost, Smm.description, Smm.user_id)
                    .join(TargetAudienceSmm, TargetAudienceSmm.smm_id == Smm.user_id)
                    .where(TargetAudienceSmm.target_audience_id == tn[0], Smm.date_sub > datetime.utcnow())
                )
            else:
                return []
            smm = result.fetchall()
            dict_of_smm = {}
            for x in smm:
                v = dict_of_smm.get(x[-1], list(x[:-1]) + [0])
                dict_of_smm[x[-1]] = v[:-1] + [v[-1] + 1]
            dict_of_smm = sorted(dict_of_smm.items(), key=lambda x: -x[1][-1])
            return dict_of_smm

    async def get_profile_by_id(self, id):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.id, Smm.full_name, Smm.phone, Smm.user_id, Smm.age, Smm.town, Smm.cost, Smm.photo,
                       Users.username, Smm.description, Smm.date_sub)
                .join(Users, Users.id == Smm.user_id)
                .where(Smm.user_id == id)
            )
            return result.fetchone()

    async def get_profile_by_id_str(self, id):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.id, Smm.full_name, Smm.phone, Smm.user_id, Smm.age, Smm.town, Smm.cost, Smm.photo,
                       Users.username, Smm.description)
                .join(Users, Users.id == Smm.user_id)
                .where(Smm.user_id == id)
            )
            return result.fetchone()

    async def add_smm(self, user_id, date):
        async with self.db() as session:
            new_smm = Smm(user_id=user_id, date_sub=date)
            session.add(new_smm)
            await session.commit()

    async def add_fullname(self, user_id, fullname):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(full_name=fullname)
            )
            await session.commit()

    async def add_phone(self, user_id, phone):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(phone=phone)
            )
            await session.commit()

    async def add_age(self, user_id, age):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(age=age)
            )
            await session.commit()

    async def add_town(self, user_id, town):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(town=town)
            )
            await session.commit()

    async def add_photo(self, user_id, photo):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(photo=photo)
            )
            await session.commit()

    async def add_cost(self, user_id, cost):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(cost=cost)
            )
            await session.commit()

    async def updt_user(self, user_id, fullname, phone, age, town, cost, description):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id)
                .values(full_name=fullname, phone=phone, age=age, town=town, cost=cost, description=description)
            )
            await session.commit()

    async def get_category_by_smm(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(TargetAudience.name, TargetAudience.category)
                .join(TargetAudienceSmm, TargetAudienceSmm.target_audience_id == TargetAudience.id)
                .where(TargetAudienceSmm.smm_id == user_id)
            )
            return result.fetchall()

    async def edit_categories(self, categories):
        async with self.db() as session:
            await session.execute(
                delete(TargetAudienceSmm).where(TargetAudienceSmm.smm_id == categories.user_id)
            )
            for category in categories.categories:
                ta_id = await self.get_ta_id(category)
                new_ta_smm = TargetAudienceSmm(smm_id=categories.user_id, target_audience_id=ta_id)
                session.add(new_ta_smm)
            await session.commit()

    async def get_phone_by_user_id(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.phone).where(Smm.user_id == user_id)
            )
            return result.scalar()

    async def get_tg_by_user_id(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(Users.username).where(Users.id == user_id)
            )
            return result.scalar()

    async def is_used_free_sub(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.free_sub).where(Smm.user_id == user_id)
            )
            return bool(result.scalar())

    async def use_free_sub(self, user_id):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(free_sub=1)
            )
            await session.commit()

    async def add_description(self, user_id, description):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(description=description)
            )
            await session.commit()

    async def is_smm(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.user_id).where(Smm.user_id == user_id)
            )
            return bool(result.scalar())

    async def get_date_sub(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.date_sub).where(Smm.user_id == user_id)
            )
            return result.scalar()

    async def add_date_sub(self, user_id, date_sub):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(date_sub=date_sub)
            )
            await session.commit()

    async def delete_smm(self, user_id):
        async with self.db() as session:
            await session.execute(
                delete(Smm).where(Smm.user_id == user_id)
            )
            await session.commit()

    async def add_payment(self, user_id, start_time=None, finish_time=None, cost=0, payment_id=None):
        async with self.db() as session:
            new_payment = Payments(user_id=user_id, start_time=start_time, finish_time=finish_time, cost=cost, payment_id=payment_id)
            session.add(new_payment)
            await session.commit()

    async def get_active_payment(self):
        async with self.db() as session:
            result = await session.execute(
                select(Payments.user_id, Users.username, Payments.start_time, Payments.finish_time, Payments.cost)
                .join(Users, Users.id == Payments.user_id)
                .where(Payments.finish_time > datetime.utcnow())
            )
            return result.fetchall()

    async def get_payments_for_last_days(self, days_from, days_to):
        async with self.db() as session:
            result = await session.execute(
                select(Payments.user_id, Users.username, Payments.start_time, Payments.finish_time, Payments.cost)
                .join(Users, Users.id == Payments.user_id)
                .where((datetime.utcnow() - timedelta(days=days_to)) >= Payments.start_time)
                .where(Payments.start_time >= (datetime.utcnow() - timedelta(days=days_from)))
            )
            return result.fetchall()

    async def get_total_cost_for_last_days(self, days_from, days_to):
        async with self.db() as session:
            result = await session.execute(
                select(func.sum(Payments.cost)).where(
                    (datetime.utcnow() - timedelta(days=days_to)) >= Payments.start_time).where(
                    Payments.start_time >= (datetime.utcnow() - timedelta(days=days_from)))
            )
            rs = result.scalar()
            return 0 if rs is None else rs

    async def use_promo(self, promo, user_id):
        async with self.db() as session:
            await session.execute(
                update(Smm).where(Smm.user_id == user_id).values(promos=Promocodes.promo + "," + promo)
            )
            await session.execute(
                update(Promocodes).where(Promocodes.promo == promo).values(usage=Promocodes.usage - 1)
            )
            await session.commit()

    async def get_users_promos(self, user_id):
        async with self.db() as session:
            result = await session.execute(
                select(Smm.promos).where(Smm.user_id == user_id)
            )
            return result.fetchall()

    async def get_promo_usage(self, promo):
        async with self.db() as session:
            result = await session.execute(
                select(Promocodes.usage).where(Promocodes.promo == promo)
            )
            return result.scalar()

    async def get_all_promos(self):
        async with self.db() as session:
            result = await session.execute(
                select(Promocodes.promo, Promocodes.usage, Promocodes.users, Promocodes.duration, Promocodes.text_)
            )

            result = result.fetchall()
            promos = dict()
            for i in range(len(result)):
                promos[result[i][0]] = (result[i][1], result[i][2], result[i][3], result[i][4])
            return promos

