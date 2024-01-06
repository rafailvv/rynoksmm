import asyncio
import os
import uuid

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, LabeledPrice, \
    InlineKeyboardButton, InlineKeyboardMarkup, PreCheckoutQuery, InputFile, FSInputFile, CallbackQuery, InputMediaPhoto
from aiogram.filters import Command

from dotenv import dotenv_values
import pandas as pd

import database as db
from states import SmmStatesGroup as st

config = dotenv_values(".env")

token = config['TOKEN']

bot = Bot(token)
dp = Dispatcher()

async def payment(user_id, price, smm_id):
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Купить контакт", pay=True)]
        ]
    )
    await bot.send_invoice(
        chat_id=user_id,
        title="Купить контакт",
        description="Приобрести контакт данного пользователя",
        provider_token=config["PAY_TOKEN"],
        currency="RUB",
        # photo_url="https://i.ibb.co/448wWGc/avatar.png",
        # photo_width=640,
        # photo_height=640,
        # is_flexible=False,
        prices=[LabeledPrice(label="Цена", amount=price * 100)],
        start_parameter="time-machine-example",
        payload=f"contact|{smm_id}",

        # need_email=True,
        # send_email_to_provider=True,
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


@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@dp.message(
    lambda message: message.content_type
                    in {ContentType.SUCCESSFUL_PAYMENT}
)
async def got_payment(message: Message):
    payload = message.successful_payment.invoice_payload.split("|")
    if payload[0] == "contact":
        await message.answer(f"""Оплата прошла успешно\n""")
        profile = await db.get_profile_by_id(payload[1])
        id, name, phone, user_id, age, town, cost, photo, tg = profile[0].split(',')

        await message.answer_photo(photo,
                                   caption=f"""Имя: {name[1:-1]}\nНомер телефона: {phone}\nВозраст: {age}\nГород: {town}\nТелеграм: @{tg[:-1]}""")


@dp.message(F.text.in_({"/start", "Меню ☰"}))
async def start(message: Message):
    button_phone = [[InlineKeyboardButton(text="Я SMM", callback_data='menu|smm'),
                     InlineKeyboardButton(text="Я ищу SMM", callback_data='menu|looking')]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=button_phone)
    await db.add_user(message.chat.id, message.chat.username)
    btn = [[KeyboardButton(text="Меню ☰")]]
    btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
    await message.answer_sticker("CAACAgIAAxkBAAIFvmWXxX8WpuUBN9IAAZCCjUeOI7IIdwAC2A8AAkjyYEsV-8TaeHRrmDQE", reply_markup=btn)
    await message.answer(f"Добро пожаловать, {message.from_user.first_name}, кто ты?", reply_markup=keyboard)


async def ta_choose(message: Message, t=None, fl=True):
    if t is None:
        t = []
        target_audience = await db.get_all_target_audience()
        for i in range(len(target_audience)):
            t.append(target_audience[i][1])
        t.append("Принять")

    btns = []
    for i in range(len(t) - 1):
        btns.append([InlineKeyboardButton(text=f"{t[i]}", callback_data=f"ta|{i}")])
    btns.append([InlineKeyboardButton(text="Принять", callback_data="ta|done")])
    btns = InlineKeyboardMarkup(inline_keyboard=btns)
    if fl:
        await message.answer(text="Выбери свою ЦА 👇", reply_markup=btns)
    else:
        await message.edit_reply_markup(reply_markup=btns)


@dp.message(Command('i_looking_smm'))
async def search_by_ta(message: Message, t=None, fl=True):
    if t is None:
        t = []
        target_audience = await db.get_all_target_audience()
        for i in range(len(target_audience)):
            t.append(target_audience[i][1])
        t.append("Применить")

    btns = []
    for i in range(len(t) - 1):
        btns.append([InlineKeyboardButton(text=f"{t[i]}", callback_data=f"talook|{i}")])
    btns.append([InlineKeyboardButton(text="Применить", callback_data="talook|done")])
    btns = InlineKeyboardMarkup(inline_keyboard=btns)
    if fl:
        await message.answer(text="Выбери свою ЦА 👇", reply_markup=btns)
    else:
        await message.edit_reply_markup(reply_markup=btns)


async def search_by_town(message: Message, state: FSMContext, dict_of_smm):
    await message.answer(text='Введите город, если неважно введите "-" (без кавычек)')
    await state.update_data(town=True)
    await state.update_data(town_d=dict_of_smm)


async def search_by_cost(message: Message, state: FSMContext, dict_of_smm):
    await message.answer(text='Введите начальную цену услуг')
    await state.update_data(cost=True)
    await state.update_data(cost_d=dict_of_smm)


@dp.callback_query()
async def menu_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")

    if 'menu' == data[0]:
        if data[1] == "smm":
            await smm_menu(callback.message, state)
        elif data[1] == "looking":
            await search_by_ta(callback.message)
    elif 'ta' == data[0]:
        t = []
        for i in range(len(message.reply_markup.inline_keyboard) - 1):
            t.append(message.reply_markup.inline_keyboard[i][0].text)

        if data[1] == "done":
            await db.add_ta(message.chat.id, t)
            await message.edit_text(text="Данные успешно, сохранены")
        else:
            if t[int(data[1])][0] == "✅":

                t[int(data[1])] = t[int(data[1])][2:]

            else:

                t[int(data[1])] = "✅ " + t[int(data[1])]

            t.append("Принять")
            await ta_choose(message, t, fl=False)
    elif "talook" == data[0]:
        t = []
        for i in range(len(message.reply_markup.inline_keyboard) - 1):
            t.append(message.reply_markup.inline_keyboard[i][0].text)

        if data[1] == "done":
            dict_of_smm = await db.get_smm_by_ta(t)
            await search_by_town(message, state, dict_of_smm)
        else:
            if t[int(data[1])][0] == "✅":

                t[int(data[1])] = t[int(data[1])][2:]

            else:

                t[int(data[1])] = "✅ " + t[int(data[1])]

            t.append("Применить")
            await search_by_ta(message, t, fl=False)
    elif "choose_smm" == data[0]:
        if data[1] == "buy":
            await payment(message.chat.id, 300, int(data[2]))
            await message.delete()
        elif data[1] == "next":
            await list_of_smm(message, state_data["dos"], state_data["it"] + 1, state, True)
        elif data[1] == "prev":
            await list_of_smm(message, state_data["dos"], state_data["it"] - 1, state, True)


@dp.message(Command('i_smm'))
async def smm_menu(message: Message, state: FSMContext):
    await db.add_smm(message.chat.id)
    await message.answer(f"Заполни анкету")
    await message.answer("Введите Имя и Фамилию")
    await state.set_state(st.fullname)


# @dp.message(Command('i_looking_smm'))
# async def looking_smm_menu(message: Message):
#     target_audience = await db.get_all_target_audience()
#     buttons = []
#     for ta in target_audience:
#         buttons.append([InlineKeyboardButton(text=ta[1], callback_data=f'ta|{ta[0]}')])
#     keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
#     await message.answer(f"Выбери свою ЦА 👇", reply_markup=keyboard)


@dp.message(Command('profile'))
async def profile(message: Message):
    profile = await db.get_profile_by_id(message.chat.id)
    id, name, phone, user_id, age, town, cost, photo, tg = profile[0].split(',')

    await message.answer_photo(photo[:-1],
                               caption=f"""Ваше имя: {name[1:-1]}\nВаш номер телефона: {phone}\nВаш возраст: {age}\nВаш город: {town}""")


@dp.message(st.fullname)
async def fullname(message: Message, state: FSMContext):
    name = list(message.text.split())
    name = str(name[0]) + ' ' + str(name[1])
    await db.add_fullname(message.chat.id, message.text)
    btn = [[KeyboardButton(text="Ввести номер телефона", request_contact=True)]]
    btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
    await message.answer("Введите номер телефона", reply_markup=btn)
    await state.set_state(st.phone)


@dp.message(st.phone)
async def phone(message: Message, state: FSMContext):
    if message.content_type == "contact":
        await db.add_phone(message.chat.id, message.contact.phone_number)
        markup = types.ReplyKeyboardRemove()
        await message.answer("Введите cвой возраст", reply_markup=markup)
        await state.set_state(st.age)

    else:
        await message.answer("Для отправки нажмите на кнопку ниже")


@dp.message(st.age)
async def age(message: Message, state: FSMContext):
    if message.text.isdigit() and 0 < int(message.text) < 120:
        await db.add_age(message.chat.id, int(message.text))
        await message.answer("Введите свой город")
        await state.set_state(st.town)

    else:
        await message.answer("Неверный возраст, попробуйте еще раз")


@dp.message(st.town)
async def town(message: Message, state: FSMContext):
    url = 'https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D0%BE%D0%B2_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8'
    df = pd.read_html(url)[0]
    cities = df['Город'].to_list()
    if message.text.capitalize() in cities:
        await db.add_town(message.chat.id, message.text.capitalize())
        await message.answer("Пришлите фотографию вашего профиля")
        await state.set_state(st.photo)
    else:
        await message.answer("Неверный город, попробуйте еще")


@dp.message(st.photo)
async def photo(message: Message, state: FSMContext):
    if message.content_type == "photo":
        await db.add_photo(message.chat.id, message.photo[-1].file_id)
        await message.answer("Начальная цена ваших услуг в рублях")
        await state.set_state(st.cost)
    else:
        await message.answer("Отправьте фотографию")


@dp.message(st.cost)
async def cost(message: Message, state: FSMContext):
    if message.text.isdigit() and 50 <= int(message.text) <= 2000000000:
        await db.add_cost(message.chat.id, int(message.text))
        await state.clear()
        await ta_choose(message)
    else:
        await message.answer(
            "Введите только число" if not message.text.isdigit() else "Слишком низкая цена" if 50 > int(
                message.text) else "Слишком высокая цена")


@dp.message()
async def messages(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if "town" in state_data and state_data["town"]:
        dict_of_smm = state_data["town_d"]
        await state.clear()
        if message.text == "-":
            pass
        else:
            i = 0
            for k, v in dict_of_smm:
                if v[2].lower() != message.text.lower():
                    del dict_of_smm[i]
                i += 1
        await search_by_cost(message, state, dict_of_smm)
    elif "cost" in state_data and state_data["cost"]:
        dict_of_smm = state_data["cost_d"]
        await state.clear()
        if message.text.isdigit():
            i = 0
            for k, v in dict_of_smm:
                if v[4] < int(message.text):
                    del dict_of_smm[i]
                i += 1
        else:
            await message.answer(text="Введите число")
        await list_of_smm(message, dict_of_smm, 0, state)


async def list_of_smm(message: Message, dict_of_smm, i, state: FSMContext, fl=False):
    smm = dict_of_smm[i]
    user_id = smm[0]
    user_info = smm[1]
    buy = InlineKeyboardButton(text="Купить контакт", callback_data=f"choose_smm|buy|{user_id}")
    prev = InlineKeyboardButton(text="Предыдущий", callback_data=f"choose_smm|prev")
    next = InlineKeyboardButton(text="Следующий", callback_data=f"choose_smm|next")
    await state.update_data(dos=dict_of_smm)
    await state.update_data(it=i)
    if i == 0:
        btns = [[buy], [next]]
    elif i == len(dict_of_smm) - 1:
        btns = [[buy], [prev]]
    else:
        btns = [[buy], [prev, next]]
    btns = InlineKeyboardMarkup(inline_keyboard=btns)
    if not fl:
        await message.answer_photo(user_info[3], caption=f"Возраст: {user_info[1]}\nГород: {user_info[2]}\nЦена: {user_info[4]}", reply_markup=btns)
    else:
        await message.edit_media(media=InputMediaPhoto(media=user_info[3], caption=f"Возраст: {user_info[1]}\nГород: {user_info[2]}\nЦена: {user_info[4]}"), reply_markup=btns)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
