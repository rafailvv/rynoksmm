from aiogram import Router
from aiogram.types import CallbackQuery

import asyncio
import os
import uuid

import PIL.ImageOps
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    LabeledPrice,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    PreCheckoutQuery,
    InputFile,
    FSInputFile,
    CallbackQuery,
    InputMediaPhoto,
    InputMediaDocument
)
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject

from dotenv import dotenv_values
import pandas as pd

import Database.database as db

from Bot.misc.states import SmmStatesGroup as st
from Bot.misc.methods import *


from PIL import Image, ImageDraw

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from aiogram.fsm.storage.redis import RedisStorage, Redis

from datetime import datetime, timedelta

from Bot.misc.scheduler import scheduler
from Bot.misc.bot import bot

message_router = Router()


@message_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@message_router.message(lambda message: message.content_type in {ContentType.SUCCESSFUL_PAYMENT})
async def got_payment(message: Message, state: FSMContext):
    payload = message.successful_payment.invoice_payload.split("|")
    if payload[0] == "post":
        btn = [
            [KeyboardButton(text="Меню ☰")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer(text="Оплата прошла успешно!\nТеперь ваш профиль виден другим пользователям", reply_markup=btn)

        scheduler.add_job(sub_end, DateTrigger(datetime.now() + timedelta(days=30 * int(payload[1]))), args=[message])
        await db.add_date_sub(message.chat.id, datetime.utcnow() + timedelta(days=30 * int(payload[1])))


@message_router.message(Command("delete"))
async def delete_smm(message: Message):
    await db.delete_smm(message.chat.id)
    await message.answer(text="Ваш профиль был удален")


@message_router.message(F.text.in_({"/start", "Меню ☰"}))
async def start(message: Message):
    # all = await db.lst_of_users()
    # all_edit = []
    # for x in all:
    #     all_edit.append(x[0])
    # if message.chat.id in all_edit:
    #     await message.answer(text='pass')
    # else:

    await db.add_user(message.chat.id, message.chat.username)
    button_phone = [
        [
            InlineKeyboardButton(text="Я SMM", callback_data="menu|smm"),
            InlineKeyboardButton(text="Я ищу SMM", callback_data="menu|looking_smm"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=button_phone)
    btn = [
        [KeyboardButton(text="Меню ☰")],
        [KeyboardButton(text="Избранные контакты 🤝")],
    ]
    if await db.is_smm(message.chat.id) and await db.get_date_sub(message.chat.id) < datetime.utcnow():
        btn.append([KeyboardButton(text="Оформить подписку 🎟")])
    btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
    await message.answer_sticker(
        "CAACAgIAAxkBAAIFvmWXxX8WpuUBN9IAAZCCjUeOI7IIdwAC2A8AAkjyYEsV-8TaeHRrmDQE",
        reply_markup=btn,
    )
    await message.answer(
        f"Добро пожаловать, {message.from_user.first_name}, кто ты? 🤔",
        reply_markup=keyboard,
    )


@message_router.message(CommandStart())
async def deep_link_start(message: Message, state: FSMContext):
    data = message.text.split()[1]
    if data == "i_smm":
        await state.clear()
        await state.update_data(ta=[])
        await smm_menu(message, state)
    elif data == "i_looking_smm":
        await state.clear()
        await state.update_data(ta=[])
        await search_by_field(message, state)


@message_router.message(F.text == "Избранные контакты 🤝")
async def get_dos(message: Message, state: FSMContext):
    dict_of_contacts = await db.get_bought_contacts(message.chat.id)
    await contacts(message, state, list(dict_of_contacts.items()), 0, False)


@message_router.message(F.text == "Оформить подписку 🎟")
async def extend_sub(message: Message, state: FSMContext):
    btn = [[InlineKeyboardButton(text="Пропустить", callback_data="add_field|promo_skip")]]
    btn = InlineKeyboardMarkup(inline_keyboard=btn)
    await message.answer(text='Введите промокод', reply_markup=btn)
    await state.set_state(st.promo)


@message_router.message(Command("i_smm"))
async def smm_menu(message: Message, state: FSMContext):
    if await db.is_smm(message.chat.id):
        await message.answer(
            f"У вас уже есть аккаунт SMM. Вы можете просмотреть или изменить его, нажав на кнопку 'Профиль'.")
    else:
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=1)), args=[message])
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=3)), args=[message])
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=7)), args=[message])
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=14)), args=[message])
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=30)), args=[message])
        await db.add_smm(message.chat.id, datetime.utcnow())
        await message.answer(f"Заполните анкету.")
        await message.answer("Введите ваше имя и фамилию 👇")

        await state.set_state(st.fullname)


@message_router.message(st.fullname)
async def fullname(message: Message, state: FSMContext):
    name = list(message.text.split())
    if len(name) == 2:
        name = str(name[0]) + " " + str(name[1])
        await db.add_fullname(message.chat.id, message.text)
        btn = [[KeyboardButton(text="Ввести номер телефона 📱", request_contact=True)]]
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer("Введите номер телефона 👇", reply_markup=btn)
        await state.set_state(st.phone)
    else:
        await message.answer("Введите Имя и Фамилию 👇")


@message_router.message(st.phone)
async def phone(message: Message, state: FSMContext):
    if message.content_type == "contact":
        phone = message.contact.phone_number
        if not message.contact.phone_number.startswith("+"):
            phone = "+" + phone
        await db.add_phone(message.chat.id, phone)
        markup = types.ReplyKeyboardRemove()
        await message.answer("Введите cвой возраст 👇", reply_markup=markup)
        await state.set_state(st.age)

    else:
        await message.answer("Для отправки нажмите на кнопку ниже")


@message_router.message(st.age)
async def age(message: Message, state: FSMContext):
    if message.text.isdigit() and 0 < int(message.text) < 120:
        await db.add_age(message.chat.id, int(message.text))
        await message.answer("Введите свой город 👇")
        await state.set_state(st.town)

    else:
        await message.answer("❌ Неверный возраст, попробуйте еще раз")


@message_router.message(st.town)
async def town(message: Message, state: FSMContext, fl=False, town=""):
    url = "https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D0%BE%D0%B2_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8"
    df = pd.read_html(url)[0]
    cities = df["Город"].to_list()
    if fl or message.text.capitalize() in cities:
        if town == "":
            await db.add_town(message.chat.id, message.text.capitalize())
        else:
            await db.add_town(message.chat.id, town)
        await message.answer("Пришлите фотографию вашего профиля 📸")
        await state.set_state(st.photo)
    else:
        btns = [[InlineKeyboardButton(text="Да", callback_data=f"town|1|{message.text.capitalize()}"),
                 InlineKeyboardButton(text="Нет", callback_data="town|0")]]
        btns = InlineKeyboardMarkup(inline_keyboard=btns)
        await message.answer("Ваш город не найден в базе данных, вы уверены что хотите продолжить?", reply_markup=btns)


@message_router.message(st.photo)
async def photo(message: Message, state: FSMContext):
    if message.content_type in ["photo"]:
        file_id = message.photo[-1].file_id if message.content_type == "photo" else message.animation.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        await bot.download_file(file_path, f"API/profile/templates/images/{message.chat.id}.{file_path.split('.')[-1]}")
        await db.add_photo(message.chat.id,
                           message.photo[-1].file_id if message.content_type == "photo" else message.animation.file_id)
        await cut_photo(message.chat.id, file_path)
        btns = [[InlineKeyboardButton(text="Изменить", callback_data="photo|change"),
                 InlineKeyboardButton(text="Применить", callback_data="photo|accept")]]
        btns = InlineKeyboardMarkup(inline_keyboard=btns)
        document = FSInputFile(f"API/profile/templates/images/{message.chat.id}.{file_path.split('.')[-1]}")
        await message.answer_photo(photo=document, caption="Ваша фотография", reply_markup=btns)
    else:
        await message.answer("❌ Неверный формат, отправьте фотографию")


@message_router.message(st.description)
async def send_cost(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("Слишком длинное описание, попробуйте сократить (до 500 символов)")
        return

    await db.add_description(message.chat.id, message.text)
    await message.answer("Начальная цена ваших услуг в рублях за месяц 👇")
    await state.set_state(st.cost)


@message_router.message(st.cost)
async def cost(message: Message, state: FSMContext):
    if message.text.isdigit() and 15000 <= int(message.text) <= 10000000:
        await db.add_cost(message.chat.id, int(message.text))
        await state.clear()
        await state.update_data(ta=list())
        await state.update_data(cnt_of_sd=0)
        await search_by_field(message, state, smm=True)
    else:
        await message.answer(
            "Введите только число"
            if not message.text.isdigit()
            else "Минимальная цена 15000₽"
            if 15000 > int(message.text)
            else "Слишком высокая цена"
        )


@message_router.message(st.promo)
async def promo(message: Message, state: FSMContext, fl=True, promo=None):
    user_id = message.chat.id
    if promo is None:
        promo = message.text

    tas = await db.get_ta_by_user_id(user_id)
    smm_id, full_name, phone, user_id, age, town, cost, photo, username, description, date_sub = await db.get_profile_by_id(user_id)
    if None in [full_name, phone, age, town, cost, description, date_sub] or len(tas) == 0 or f"{user_id}.jpg" not in os.listdir("API/profile/templates/images"):
        btn = [[KeyboardButton(text="Меню ☰")], [KeyboardButton(text="Избранные контакты 🤝")],
               [KeyboardButton(text="Оформить подписку 🎟")]]
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer("Пожалуйста, заполните все поля профиля, нажав на кнопку 'Профиль', и повторите попытку", reply_markup=btn)
        return
    if promo == "-":
        if fl and not await db.is_used_free_sub(message.chat.id):
            btns = [[InlineKeyboardButton(text="Активировать", callback_data=f"free_sub|use|{message.chat.id}")],
                    [InlineKeyboardButton(text="Использовать потом", callback_data=f"free_sub|then")]]
            btns = InlineKeyboardMarkup(inline_keyboard=btns)
            await message.answer(text="Вам доступен пробный период 7 дней", reply_markup=btns)
        else:
            cost = 1000
            discount3 = 0.1
            discount6 = 0.25
            discount12 = 0.4
            btn = [
                [InlineKeyboardButton(text="1 месяц", callback_data=f"sub|1|{cost}|{user_id}")],
                [InlineKeyboardButton(text="3 месяца", callback_data=f"sub|3|{int(3 * cost * (1 - discount3))}|{user_id}")],
                [InlineKeyboardButton(text="6 месяцев", callback_data=f"sub|6|{int(6 * cost * (1 - discount6))}|{user_id}")],
                [InlineKeyboardButton(text="12 месяцев", callback_data=f"sub|12|{int(12 * cost * (1 - discount12))}|{user_id}")]
            ]
            btn = InlineKeyboardMarkup(inline_keyboard=btn)
            await message.answer(
                text=f"Выберите длительность подписки 👇\n\n1 месяц - {cost} ₽\n3 месяца - {int(3 * cost * (1 - discount3))} ₽ (Скидка {int(discount3 * 100)}%)\n6 месяцев - {int(6 * cost * (1 - discount6))} ₽ (Скидка {int(discount6 * 100)}%)\n12 месяцев - {int(12 * cost * (1 - discount12))} ₽ (Скидка {int(discount12 * 100)}%)",
                reply_markup=btn
            )
    elif promo.lower() == "неделя":
        btn = [
            [KeyboardButton(text="Меню ☰")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer(text="Вы активировали промокод на бесплатную подписку на неделю!", reply_markup=btn)
        await db.add_date_sub(message.chat.id, datetime.utcnow() + timedelta(days=7))
        scheduler.add_job(sub_end, DateTrigger(datetime.now() + timedelta(days=7)), args=[message])
    elif promo.lower() == "месяц":
        btn = [
            [KeyboardButton(text="Меню ☰")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer(text="Вы активировали промокод на бесплатную подписку на месяц!", reply_markup=btn)
        await db.add_date_sub(message.chat.id, datetime.utcnow() + timedelta(days=30))
        scheduler.add_job(sub_end, DateTrigger(datetime.now() + timedelta(days=30)), args=[message])

    state_data = await state.get_data()
    await state.clear()
    await state.update_data(state_data)


@message_router.message(Command("i_looking_smm"))
async def search_by_field(message: Message, state: FSMContext, smm=False, edit=False, clear=True):
    f = []
    field = await db.get_all_field()
    for i in range(len(field)):
        f.append(field[i][0])
    btns = []
    for i in range(len(f)):
        btns.append([InlineKeyboardButton(text=f"{f[i]}", callback_data=f"field|{f[i]}|{smm}")])
    btns = InlineKeyboardMarkup(inline_keyboard=btns)
    if edit:
        await message.edit_text(text="Выберите вашу сферу деятельности👇", reply_markup=btns)
    else:
        await message.answer(text="Выберите вашу сферу деятельности👇", reply_markup=btns)


@message_router.message()
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
            await list_of_smm(message, dict_of_smm, 0, state)
        else:
            await message.answer(text="Введите число")
