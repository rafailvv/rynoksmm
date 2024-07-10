from aiogram.fsm.state import StatesGroup, State


class SmmStatesGroup(StatesGroup):
    fullname = State()
    phone = State()
    age = State()
    town = State()
    cost = State()
    photo = State()
    promo = State()
    description = State()
