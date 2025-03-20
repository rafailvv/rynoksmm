from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqladmin import Admin, ModelView
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from Bot.config import config
from Database.models import *
import uvicorn

security = HTTPBasic()


def admin_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = config.db.user
    correct_password = config.db.password
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные данные авторизации",
            headers={"WWW-Authenticate": "Basic"},
        )


class Promocodes(ModelView, model=Promocodes):
    column_list = [Promocodes.id, Promocodes.promo, Promocodes.usage, Promocodes.users, Promocodes.duration]


class TargetAudience(ModelView, model=TargetAudience):
    column_list = [TargetAudience.id, TargetAudience.name, TargetAudience.category]
