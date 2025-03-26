from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from Bot.config import config
from Database.models import *
import uvicorn
from fastapi.responses import HTMLResponse
import secrets
from fastapi.requests import Request

security = HTTPBasic()


class BasicAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        credentials = await request.form()
        username = credentials.get("username")
        password = credentials.get("password")

        correct_username = config.db.user
        correct_password = config.db.password

        # is_correct_username = secrets.compare_digest(credentials.username, correct_username)
        # is_correct_password = secrets.compare_digest(credentials.password, correct_password)

        if username == correct_username and password == correct_password:
            request.session.update({"authenticated": True})
            return True
            # next_url = request.query_params.get("next", "/admin")
            # return RedirectResponse(url=next_url)
        else:
            return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("authenticated", False)


class Promocodes(ModelView, model=Promocodes):
    column_list = [Promocodes.id, Promocodes.promo, Promocodes.usage, Promocodes.users, Promocodes.duration]


class TargetAudience(ModelView, model=TargetAudience):
    column_list = [TargetAudience.id, TargetAudience.name, TargetAudience.category]


class Support(ModelView, model=Support):
    column_list = [Support.id, Support.request, Support.user_id, Support.answered, Support.tg_url]


class Users(ModelView, model=Users):
    column_list = [Users.id, Users.username]


class Payments(ModelView, model=Payments):
    column_list = [Payments.id, Payments.user_id, Payments.start_time, Payments.finish_time, Payments.cost,
                   Payments.payment_id]


class Smm(ModelView, model=Smm):
    column_list = [Smm.id, Smm.user_id, Smm.full_name, Smm.phone, Smm.age, Smm.town, Smm.cost, Smm.photo, Smm.free_sub,
                   Smm.description, Smm.date_sub, Smm.promos]


class SubscribeNotifications(ModelView, model=SubscribeNotifications):
    column_list = [SubscribeNotifications.id, SubscribeNotifications.ta, SubscribeNotifications.town,
                   SubscribeNotifications.cost, SubscribeNotifications.user_id]


class TargetAudienceSmm(ModelView, model=TargetAudienceSmm):
    column_list = [TargetAudienceSmm.id, TargetAudienceSmm.smm_id, TargetAudienceSmm.target_audience_id]


class Cases(ModelView, model=Cases):
    column_list = [Cases.id, Cases.smm_id, Cases.name, Cases.link]


class Contacts(ModelView, model=Contacts):
    column_list = [Contacts.id, Contacts.user_id, Contacts.smm_id]
