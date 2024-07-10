# region Imports
import os
import ssl

import uvicorn
from fastapi import FastAPI, Request, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.requests import Request
from starlette.templating import Jinja2Templates
import database as db
from typing import List
from datetime import datetime
# endregion

app = FastAPI()

mainpage_router = APIRouter()

templates = Jinja2Templates(directory="profile/templates")
app.mount("/templates", StaticFiles(directory="profile/templates"), name="templates")


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

# @mainpage_router.get("/profile/{user_id}")
# async def main_page(request: Request, user_id: int):
#     profile = await db.get_profile_by_id(user_id)
#     if profile is not None:
#         profile = profile[0].split(",")
#
#         age = int(profile[4])
#         if age % 10 == 1:
#             age = str(age) + " год"
#         elif age % 10 < 5:
#             age = str(age) + " года"
#         else:
#             age = str(age) + " лет"
#         return templates.TemplateResponse("profile.html", {"request": request, "user_id": user_id, "name": profile[1][1:-1],
#                                                          "phone": profile[2], "age": age, "cost": profile[6],
#                                                          "town": profile[5]})
#     else:
#         return templates.TemplateResponse("no_acc.html", {"request": request})

@mainpage_router.get("/")
async def main_page_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@mainpage_router.get("/profile")
async def main_page_router(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@mainpage_router.get("/no_acc")
async def no_acc(request: Request):
    return templates.TemplateResponse("no_acc.html", {"request": request})


@mainpage_router.get("/profile/info/{user_id}")
async def main_page_info(request: Request, user_id: int):
    profile = await db.get_profile_by_id(user_id)
    dict_of_ta = dict()
    dict_of_all_ta = dict()
    ta = await db.get_category_by_smm(user_id)
    all_ta = await db.get_all_ta()

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
                "date_sub": "Ваша подписка заканчивается " + profile[10].strftime("%d.%m.%Y, %H:%M") if profile[10]  is not None and profile[10] > datetime.utcnow() else "Подписка не активна"}
    else:
        return {"result": False}


@mainpage_router.post("/profile")
async def update(user: User):
    await db.updt_user(
        user_id=user.user_id, age=user.age, phone=user.phone, fullname=user.name, cost=user.cost, town=user.town, description=user.description
    )


@mainpage_router.post("/upload")
async def upload_file(user_id: str, file: UploadFile = File(...)):
    try:
        if not user_id:
            raise ValueError("User ID is not provided.")

        extension = file.filename.split('.')[-1]
        new_file_name = f"{user_id}.{extension}"
        file_path = os.path.join("profile/templates/images", new_file_name)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        return {"filename": new_file_name}

    except Exception as e:
        return {"error": str(e)}


class Categories(BaseModel):
    user_id: int
    categories: List[str]


@mainpage_router.post("/save_categories/")
async def save_categories(categories: Categories):
    try:
        await db.edit_categories(categories)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(mainpage_router)
if __name__ == "__main__":
    # uvicorn.run(app, host="0.0.0.0", port=443, ssl_keyfile="/etc/letsencrypt/live/rynoksmm.ru/privkey.pem", ssl_certfile="/etc/letsencrypt/live/rynoksmm.ru/fullchain.pem")
    uvicorn.run(app, host="127.0.0.1", port=80)
