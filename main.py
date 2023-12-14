import asyncio
import os
import uuid

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, LabeledPrice, \
    InlineKeyboardButton, InlineKeyboardMarkup, PreCheckoutQuery, InputFile, FSInputFile, CallbackQuery
from aiogram.filters import Command

from dotenv import dotenv_values
import pandas as pd

import database as db

config = dotenv_values(".env")

token = config['TOKEN']

bot = Bot(token)
dp = Dispatcher()

price = 300


async def payment(user_id):
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Приобрести билет", pay=True)]
        ]
    )
    await bot.send_invoice(
        chat_id=user_id,
        title="Контакт",
        description="Приобрести",
        provider_token=config["PAY_TOKEN"],
        currency="RUB",
        # photo_url="https://i.ibb.co/448wWGc/avatar.png",
        # photo_width=640,
        # photo_height=640,
        # is_flexible=False,
        prices=[LabeledPrice(label="Цена", amount=price * 100)],
        start_parameter="time-machine-example",
        payload=f"ticket",
        need_name=True,
        need_email=True,
        send_email_to_provider=True,
        # provider_data={
        #     "receipt": {
        #         "items": [
        #             {
        #                 "description": "билет на ",
        #                 "quantity": "1.00",
        #                 "amount": {
        #                     "value": str(price),
        #                     "currency": "RUB",
        #                 },
        #                 "vat_code": 2,
        #             }
        #         ]
        #     }
        # },
        reply_markup=buttons,
    )


@dp.message(Command('start'))
async def start(message: Message):
    button_phone = [[InlineKeyboardButton(text="Я SMM", callback_data='menu|smm'),
                     InlineKeyboardButton(text="Я ищу SMM", callback_data='menu|looking')]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=button_phone)
    await db.add_user(message.chat.id, message.chat.username)
    await message.answer(f"Добро пожаловать, {message.from_user.first_name}, кто ты?", reply_markup=keyboard)


@dp.callback_query()
async def menu_handler(callback: CallbackQuery):
    data = callback.data.split("|")
    if 'menu' == data[0]:
        if data[1] == "smm":
            await smm_menu(callback.message)
        elif data[1] == "looking":
            await looking_smm_menu(callback.message)
    elif 'ta' == data[0]:
        smm = await db.get_smm_by_ta(int(data[1]))
        i = 0
        while i < 5 and i < len(smm):
            await callback.message.answer(text=f"{smm[i][0], smm[i][1], smm[i][2], smm[i][3]}")
            i += 1

@dp.message(Command('i_smm'))
async def smm_menu(message: Message):
    await message.answer(f"Заполни анкету")


@dp.message(Command('i_looking_smm'))
async def looking_smm_menu(message: Message):
    target_audience = await db.get_all_target_audience()
    buttons = []
    for ta in target_audience:
        buttons.append([InlineKeyboardButton(text=ta[1], callback_data=f'ta|{ta[0]}')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(f"Выбери свою ЦА 👇", reply_markup=keyboard)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
