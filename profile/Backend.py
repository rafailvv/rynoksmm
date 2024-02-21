# region Imports
import uvicorn
from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.requests import Request
from starlette.templating import Jinja2Templates
import database as db

# endregion

app = FastAPI()

mainpage_router = APIRouter()

templates = Jinja2Templates(directory="templates")
app.mount("/templates", StaticFiles(directory="templates"), name="templates")


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


@mainpage_router.get("/profile/{user_id}")
async def main_page(request: Request, user_id: int):
    profile = await db.get_profile_by_id(user_id)
    if profile is not None:
        profile = profile[0].split(",")

        age = int(profile[4])
        if age % 10 == 1:
            age = str(age) + " год"
        elif age % 10 < 5:
            age = str(age) + " года"
        else:
            age = str(age) + " лет"
        return templates.TemplateResponse("index.html", {"request": request, "user_id": user_id, "name": profile[1][1:-1],
                                                         "phone": profile[2], "age": age, "cost": profile[6],
                                                         "town": profile[5]})
    else:
        return templates.TemplateResponse("no_acc.html", {"request": request})


@mainpage_router.post("/profile")
async def update(user: User):
    await db.updt_user(
        user_id=user.user_id, age=user.age, phone=user.phone, fullname=user.name, cost=user.cost, town=user.town
    )


app.include_router(mainpage_router)
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
