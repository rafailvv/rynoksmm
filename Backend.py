# region Imports
import os
import ssl
import mimetypes
import aioboto3
import random
import json

import uvicorn
from fastapi import FastAPI, Request, APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.requests import Request
from starlette.templating import Jinja2Templates
from Database.manager import db
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from Bot.misc.methods import cut_photo

from PIL import Image

from yookassa import Configuration, Payment
import uuid

from Bot.config import config

from Database.admin import *
from Database.session import BaseDatabase

from sqladmin.authentication import AuthenticationBackend
from sqladmin import Admin, ModelView

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from prometheus_client import Counter, Histogram, Gauge

# endregion

app = FastAPI(
    title="Warehouse API",
    description="API for managing warehouse processes",
    version="1.0.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Support Team",
        "url": "http://example.com/contact",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_tags=[
        {
            "name": "products",
            "description": "Operations with products"
        },
        {
            "name": "orders",
            "description": "Operations with orders"
        }
    ]
)


mainpage_router = APIRouter()

templates = Jinja2Templates(directory="API/profile/templates")
app.mount("/templates", StaticFiles(directory="API/profile/templates"), name="templates")

def load_prof_details():
    """Загружает детали профессий из JSON файла"""
    try:
        with open("prof_details.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

prof_details = load_prof_details()


# @app.get("/items/{id}", response_class=HTMLResponse)
# async def read_item(request: Request, id: str):
#     return templates.TemplateResponse("item.html", {"request": request, "id": id})

class User(BaseModel):
    user_id: int
    name: str
    phone: str
    age: int
    cost: int
    town: str
    description: str


@mainpage_router.get("/", tags=["products"])
async def main_page_index(request: Request):
    prof_type = config.prof.prof
    prof_data = prof_details.get(prof_type, {})
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "i_am": config.prof.i_am, 
        "i_looking": config.prof.i_looking, 
        "prof": prof_type,
        "title": prof_data.get("title", "Рынок"),
        "description": prof_data.get("description", "Описание"),
        "button_i_am": prof_data.get("button_i_am", "Я специалист"),
        "button_i_looking": prof_data.get("button_i_looking", "Я ищу специалиста")
    })


@mainpage_router.get("/profile")
async def main_page_router(request: Request):
    prof_type = config.prof.prof
    return templates.TemplateResponse("profile.html", {"request": request, "prof": prof_type})


@mainpage_router.get("/no_acc")
async def no_acc(request: Request):
    prof_type = config.prof.prof
    prof_data = prof_details.get(prof_type, {})
    
    return templates.TemplateResponse("no_acc.html", {
        "request": request,
        "button_i_am": prof_data.get("button_i_am", "Я специалист"),
        "prof": prof_type,
        "bot_url": prof_data.get("bot_url", "rynoksmm_bot")
    })


@mainpage_router.get("/profile/info/{user_id}")
async def main_page_info(request: Request, user_id: int):
    profile = await db.smm.get_profile_by_id(user_id)
    dict_of_ta = dict()
    dict_of_all_ta = dict()
    ta = await db.smm.get_category_by_smm(user_id)
    all_ta = await db.ta.get_all_ta()

    for v, k in ta:
        if k in dict_of_ta.keys():
            dict_of_ta[k].add(v)
        else:
            dict_of_ta[k] = {v}

    for v, k in all_ta:
        if k in dict_of_all_ta.keys():
            dict_of_all_ta[k].add(v)
        else:
            dict_of_all_ta[k] = {v}

    if profile is not None:

        age = profile[4]
        if age is None:
            age = ""
        else:
            age = int(age)
            if age % 10 == 1 and not (11 <= age % 100 <= 14):
                age = str(age) + " год"
            elif age % 10 < 5 and not (11 <= age % 100 <= 14):
                age = str(age) + " года"
            else:
                age = str(age) + " лет"
        return {"result": True,
                "user_id": user_id,
                "name": profile[1] if profile[1] is not None else "",
                "phone": profile[2] if profile[2] is not None else "",
                "age": age,
                "cost": profile[6] if profile[6] is not None else "",
                "town": profile[5] if profile[5] is not None else "",
                "all_ta": dict_of_all_ta,
                "ta": dict_of_ta,
                "description": profile[9] if profile[9] is not None else "",
                "date_sub": profile[10].strftime("%d.%m.%Y, %H:%M") if profile[10] is not None and profile[10] > datetime.utcnow() else "Подписка не активна"}
    else:
        return {"result": False}


@mainpage_router.post("/profile")
async def update(user: User):
    if user.user_id not in await db.users.lst_of_users():
        await db.users.add_user(user.user_id, None)
    if await db.smm.get_profile_by_id(user.user_id) is None:
        await db.smm.add_smm(user.user_id, datetime.utcnow())
    await db.smm.updt_user(
        user_id=user.user_id, age=user.age, phone=user.phone, fullname=user.name, cost=user.cost, town=user.town, description=user.description
    )

async def upload_image(image_bytes: bytes, bucket: str, filename: str):
    """Загружает изображение в S3"""
    session = aioboto3.Session()

    async with session.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id=config.minio.access_key,
        aws_secret_access_key=config.minio.secret_key,
        region_name="us-east-1",
    ) as s3:
        content_type = "image/jpeg"
        extra_args = {"ContentType": content_type}
        
        key = f"images/{filename}"
        await s3.put_object(Bucket=bucket, Key=key, Body=image_bytes, **extra_args)


def get_image_url(bucket: str, filename: str) -> str:
    """Возвращает публичный URL изображения из S3"""
    return f"https://s3.prof-tg.ru/{bucket}/images/{filename}"



@mainpage_router.post("/upload/{user_id}")
async def upload_file(user_id: str, file: UploadFile = File(...)):
    try:
        if not user_id:
            raise ValueError("User ID is not provided.")

        # Читаем файл в память
        file_content = await file.read()
        
        # Обрабатываем изображение
        from io import BytesIO
        im = Image.open(BytesIO(file_content))
        rgb_im = im.convert('RGB')
        
        # Сохраняем во временный буфер
        temp_buffer = BytesIO()
        rgb_im.save(temp_buffer, format='JPEG', quality=95)
        image_bytes = temp_buffer.getvalue()
        
        # Обрезаем фото до квадрата
        image_bytes = await cut_photo(image_bytes)
        
        # Загружаем в S3
        filename = f"{user_id}.jpg"
        await upload_image(image_bytes, config.prof.prof, filename)
        
        # Возвращаем URL изображения
        image_url = get_image_url(config.prof.prof, filename)
        
        return {"filename": filename, "url": image_url}

    except Exception as e:
        return {"error": str(e)}


class Categories(BaseModel):
    user_id: int
    categories: List[str]


@mainpage_router.post("/save_categories/")
async def save_categories(categories: Categories):
    try:
        await db.smm.edit_categories(categories)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PaymentRequest(BaseModel):
    client_id: int
    price: int
    days: int
    email: str
    req: str


@mainpage_router.get("/users/created")
async def get_users_created(datefrom: datetime=Query(...), dateto: datetime=Query(...)):
    if datefrom.tzinfo is not None:
        datefrom = datefrom.astimezone(timezone.utc).replace(tzinfo=None)
    if dateto.tzinfo is not None:
        dateto = dateto.astimezone(timezone.utc).replace(tzinfo=None)

    if datefrom > dateto:
        raise HTTPException(status_code=400, detail="datefrom must be less than or equal to dateto")

    users = list(await db.users.get_users_created(datefrom, dateto))
    users_by_day = {}
    for user in users:
        day = user.created_at.strftime("%Y-%m-%d")
        users_by_day[day] = users_by_day.get(day, 0) + 1

    res = []
    current_day = datefrom.date()
    end_day = dateto.date()
    while current_day <= end_day:
        day = current_day.strftime("%Y-%m-%d")
        res.append({"date": day, "cnt": users_by_day.get(day, 0)})
        current_day += timedelta(days=1)
    daily_data = res
    return [{"time": datetime.strptime(item["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000, "value": item["cnt"]} for item in daily_data]


# @mainpage_router.get("/users/created/timeseries")
# async def get_users_created_timeseries(datefrom: datetime=Query(...), dateto: datetime=Query(...)):
#     daily_data = await get_users_created(datefrom=datefrom, dateto=dateto)
#     return [{"time": f"{item['date']}T00:00:00Z", "value": item["cnt"]} for item in daily_data]

@mainpage_router.post("/payment/token")
async def get_confirmation_token(payment_request: PaymentRequest):
    # Настройка конфигурации YooKassa
    Configuration.account_id = config.yookassa.shop_id
    Configuration.secret_key = config.yookassa.secret_key

    # Получение данных из запроса
    client_id = payment_request.client_id
    price = payment_request.price
    days = payment_request.days
    email = payment_request.email
    req = payment_request.req
    
    # Получаем данные для текущей профессии
    prof_type = config.prof.prof
    prof_data = prof_details.get(prof_type, {})

    # Преобразование цены
    price = str(max(0, int(price * 100)) / 100)
    try:
        # Создание платежа
        idempotence_key = str(uuid.uuid4())
        payment = Payment.create({
            "amount": {
                "value": price,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "embedded"
            },
            "receipt": {
                "items": [
                    {
                        "amount": {
                            "value": price,
                            "currency": "RUB"
                        },
                        "quantity": 1,
                        "description": f'Подписка {days}' if req == 'subscription' else f'{days} {prof_data.get("ai_requests_description", "Запросов к НейроБот")}',
                        "vat_code": 1,
                        "payment_subject": "service",
                        "payment_mode": "full_prepayment"
                    }
                ],
                "customer": {
                    "email": email
                }
            },
            "capture": True,
            "test": True,
            "description": f'Подписка {days}' if req == 'subscription' else f'{days} {prof_data.get("ai_requests_description", "Запросов к НейроБот")}',
            "metadata": {"client_id": client_id, "type": req, "days": days}
        }, idempotence_key)

    # Получение и возврат токена подтверждения
        confirmation_token = payment.confirmation.confirmation_token
        return {"result": True, "id": payment.id, "confirmation_token": confirmation_token}
    except:
        return {"result": False}

# Middleware для отключения кеша
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.include_router(mainpage_router)
secret_key = [chr(random.randint(1, 128)) for i in range(random.randint(75, 100))]
authentication_backend = BasicAuth(secret_key)
engine = BaseDatabase(config).session_manager.engine
# admin = Admin(app, engine, dependencies=[Depends(admin_auth)])
admin = Admin(app, engine, authentication_backend=authentication_backend, templates_dir="API/profile/templates")

admin.add_view(Promocodes)
admin.add_view(TargetAudience)
admin.add_view(Support)
admin.add_view(Users)
admin.add_view(Payments)
admin.add_view(Smm)
admin.add_view(SubscribeNotifications)
admin.add_view(TargetAudienceSmm)
admin.add_view(Cases)
admin.add_view(Contacts)

# if __name__ == "__main__":
#     try:
#         uvicorn.run(app, host="0.0.0.0", port=80)
#     except:
#         uvicorn.run(app, host="127.0.0.1", port=80)
