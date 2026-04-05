from aiogram import Router
from aiogram.types import CallbackQuery

import asyncio
import os
import uuid

from Bot.config import config
import json

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
    BufferedInputFile,
    FSInputFile,
    CallbackQuery,
    InputMediaPhoto,
    InputMediaDocument,
    WebAppInfo
)
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject

from dotenv import dotenv_values
import pandas as pd

from Database.manager import db

from Bot.misc.states import SmmStatesGroup as st
from Bot.misc.methods import *

from PIL import Image, ImageDraw

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from aiogram.fsm.storage.redis import RedisStorage, Redis

from datetime import datetime, timedelta

from Bot.misc.scheduler import scheduler
from Bot.misc.bot import *

from yookassa import Configuration, Payment
import uuid
from yookassa.domain.response import PaymentResponse

from aiogram.exceptions import TelegramForbiddenError

# OpenRouter client is provided from Bot.misc.bot

from Bot.misc import constants

message_router = Router()

WEBAPP_DOMAIN_BY_PROF = {
    "smm": "smm.prof-tg.ru",
    "massage": "massage.prof-tg.ru",
    "photo": "photo.prof-tg.ru",
}


def get_webapp_base_url() -> str:
    prof_type = config.prof.prof
    domain = WEBAPP_DOMAIN_BY_PROF.get(prof_type, f"{prof_type}.prof-tg.ru")
    return f"https://{domain}"


def build_webapp_url(path: str) -> str:
    base = get_webapp_base_url()
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base}{path}"

def load_prof_details():
    """Загружает детали профессий из JSON файла"""
    try:
        with open("prof_details.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

prof_details = load_prof_details()


async def got_payment(message: Message, payment_response: PaymentResponse, payment_type, payment_id, state: FSMContext):
    state_data = await state.get_data()
    if payment_type == "subscription":
        btn = [
            [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer(text="Оплата прошла успешно!\nТеперь ваш профиль виден другим пользователям",
                             reply_markup=btn)

        scheduler.add_job(sub_end,
                          DateTrigger(datetime.now() + timedelta(days=int(payment_response.metadata.get('days')))),
                          args=[message.chat.id])
        await db.smm.add_date_sub(message.chat.id,
                                  datetime.utcnow() + timedelta(days=int(payment_response.metadata.get('days'))))
        await db.smm.add_payment(message.chat.id, datetime.utcnow(),
                                 datetime.utcnow() + timedelta(days=int(payment_response.metadata.get('days'))),
                                 int(payment_response.amount.value), payment_id)
    elif payment_type == "requests":
        btn = [
            [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        limit = state_data["user_requests_limit"] + int(payment_response.metadata["days"])
        await state.update_data(user_requests_limit=limit)
        await message.answer(text=f"Оплата прошла успешно!\nУ вас осталось {limit - state_data['user_requests_count']} запросов",
                             reply_markup=btn)
        await db.smm.add_payment(message.chat.id, datetime.utcnow(),
                                 datetime.utcnow() + timedelta(days=int(payment_response.metadata.get('days'))),
                                 int(payment_response.amount.value), payment_id)


@message_router.message(Command("stats"))
async def stats(message: Message, state: FSMContext):
    if message.chat.id in config.tg_bot.admins:
        cnt_users = len(await db.smm.get_active_payment())
        users_lw = len(await db.smm.get_payments_for_last_days(7, 0))
        cost_lw = await db.smm.get_total_cost_for_last_days(7, 0)
        users_pw = len(await db.smm.get_payments_for_last_days(14, 7))
        await message.answer(
            text=f"Кол-во пользователей с подпиской: {cnt_users}\nКол-во пользователей за неделю: {users_lw}\nКол-во денег за неделю: {cost_lw} ₽\nИзменение кол-ва пользователей за последнюю неделю {round(((users_lw - users_pw) / (users_pw if users_pw != 0 else 1)) * 100)}%")
    else:
        await message.answer(text="Вы не являетесь администратором")


@message_router.message(Command("delete"))
async def delete_smm(message: Message):
    await db.smm.delete_smm(message.chat.id)
    await message.answer(text="Ваш профиль был удален")


@message_router.message(Command("test"))
async def test(message: Message):
    import random
    
    rnd = random.randint(100000, 999999)
    profile_url = build_webapp_url(f"profile?rnd={rnd}")
    await message.answer(
        text=f"rnd: {rnd}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="test", web_app=WebAppInfo(url=profile_url))]]
        ),
    )


@message_router.message(F.text.in_({"/start", "Меню ☰"}))
async def start(message: Message):
    # all = await db.lst_of_users()
    # all_edit = []
    # for x in all:
    #     all_edit.append(x[0])
    # if message.chat.id in all_edit:
    #     await message.answer(text='pass')
    # else:

    await db.users.add_user(message.chat.id, message.chat.username)
    
    # Получаем данные для текущей профессии
    prof_type = config.prof.prof
    prof_data = prof_details.get(prof_type, {})
    
    button_phone = [
        [
            InlineKeyboardButton(text=prof_data.get("button_i_am", "Я специалист"), callback_data="menu|smm"),
            InlineKeyboardButton(text=prof_data.get("button_i_looking", "Я ищу специалиста"), callback_data="menu|looking_smm"),
        ]
    ]
    if prof_data.get("ai_name"):
        button_phone.append([InlineKeyboardButton(text=prof_data.get("ai_name"), callback_data="menu|ai")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=button_phone)
    btn = [
        [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
        [KeyboardButton(text="Избранные контакты 🤝")],
    ]
    if message.chat.id in config.tg_bot.admins:
        btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
    if await db.smm.is_smm(message.chat.id) and await db.smm.get_date_sub(message.chat.id) < datetime.utcnow():
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
    prof_type = config.prof.prof
    
    if data == f"i_{prof_type}":
        await state.clear()
        await state.update_data(ta=[])
        await smm_menu(message, state)
    elif data == f"i_looking_{prof_type}":
        await state.clear()
        await state.update_data(ta=[])
        await search_by_field(message, state)
    elif data.startswith("pay"):
        _, payment_id = data.split("_")
        Configuration.account_id = config.yookassa.shop_id
        Configuration.secret_key = config.yookassa.secret_key
        payment_response = Payment.find_one(payment_id)
        purchase_with_payment_id = await db.users.get_purchase_by_payment_id(payment_id)
        if payment_response.status != "succeeded":
            await message.answer("Во время оплаты произошла ошибка, обратитесь  тех. поддержку")
            return
        payment_type = payment_response.metadata["type"]
        if purchase_with_payment_id is None and message.chat.id == int(payment_response.metadata.get("client_id")):
            await got_payment(message, payment_response, payment_type, payment_id, state)
            return


@message_router.message(st.thread_state)
async def ai_smm(message: Message, state: FSMContext):
    state_data = await state.get_data()
    query = message.text
    
    # Получаем данные для текущей профессии
    prof_type = config.prof.prof
    prof_data = prof_details.get(prof_type, {})
    
    if query == prof_data.get("ai_exit", "Выйти из НейроБот ❌"):
        await state.clear()
        await state.update_data(state_data)
        btn = [
            [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        if await db.smm.is_smm(message.chat.id) and await db.smm.get_date_sub(message.chat.id) < datetime.utcnow():
            btn.append([KeyboardButton(text="Оформить подписку 🎟")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer(prof_data.get("ai_exit_message", "Вы вышли из НейроБот"), reply_markup=btn)
        return
    if state_data["user_requests_limit"] <= state_data["user_requests_count"]: # and message.chat.id not in config.tg_bot.admins
        btn = [
            [InlineKeyboardButton(text="50 Запросов", web_app=WebAppInfo(
                url=build_webapp_url("templates/payment.html?price=990&days=50&req=requests")))],
            [InlineKeyboardButton(text="100 Запросов", web_app=WebAppInfo(
                url=build_webapp_url("templates/payment.html?price=1490&days=100&req=requests")))],
            [InlineKeyboardButton(text="500 Запросов", web_app=WebAppInfo(
                url=build_webapp_url("templates/payment.html?price=5990&days=500&req=requests")))]
        ]
        btn = InlineKeyboardMarkup(inline_keyboard=btn)
        await message.answer(
            text="Выберите количество запросов 👇\n\n50 Запросов - 990 ₽\n100 Запросов - 1490 ₽ \n500 Запросов - 5990 ₽", reply_markup=btn)
        return

    message_wait = await message.answer("Подождите, запрос обрабатывается...")
    chat_response = await openrouter_client.chat.completions.create(
        model=config.openrouter.model,
        messages=[
            {
                "role": "user",
                "content": query,
            },
        ],
    )
    try:
        import re

        def escape_markdown_v2(text):
            return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

        messages = escape_markdown_v2(chat_response.choices[0].message.content or "")
        await state.update_data(user_requests_count=state_data["user_requests_count"] + 1)
        await message_wait.edit_text(messages, parse_mode="MarkdownV2")
        await message.answer(f"У вас осталось {state_data['user_requests_limit'] - (await state.get_data())['user_requests_count']} запросов")
    except Exception as e:
        await message_wait.answer("Произошла ошибка, попробуйте еще раз")


@message_router.message(F.text == "Избранные контакты 🤝")
async def get_dos(message: Message, state: FSMContext):
    dict_of_contacts = await db.contacts.get_bought_contacts(message.chat.id)
    print(dict_of_contacts)
    await contacts(message, state, dict_of_contacts, 0, False)


@message_router.message(F.text == "Оформить подписку 🎟")
async def extend_sub(message: Message, state: FSMContext):
    btn = [[InlineKeyboardButton(text="Пропустить", callback_data="add_field|promo_skip")]]
    btn = InlineKeyboardMarkup(inline_keyboard=btn)
    await message.answer(text='Введите промокод', reply_markup=btn)
    await state.set_state(st.promo)


@message_router.message(Command("i_smm"))
async def smm_menu(message: Message, state: FSMContext):
    # Получаем данные для текущей профессии
    prof_type = config.prof.prof
    prof_data = prof_details.get(prof_type, {})
    
    if await db.smm.is_smm(message.chat.id):
        await message.answer(
            prof_data.get("profile_exists_message", "У вас уже есть аккаунт. Вы можете просмотреть или изменить его, нажав на кнопку 'Профиль'."))
    else:
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=1)),
                          args=[message.chat.id, message.chat.first_name])
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=3)),
                          args=[message.chat.id, message.chat.first_name])
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=7)),
                          args=[message.chat.id, message.chat.first_name])
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=14)),
                          args=[message.chat.id, message.chat.first_name])
        scheduler.add_job(send_notification, DateTrigger(datetime.now() + timedelta(days=30)),
                          args=[message.chat.id, message.chat.first_name])
        await db.smm.add_smm(message.chat.id, datetime.utcnow())
        await message.answer(prof_data.get("fill_questionnaire", "Заполните анкету."))
        await message.answer("Введите ваше имя и фамилию 👇")

        await state.set_state(st.fullname)


@message_router.message(st.fullname)
async def fullname(message: Message, state: FSMContext):
    name = list(message.text.split())
    if len(name) == 2:
        name = str(name[0]) + " " + str(name[1])
        await db.smm.add_fullname(message.chat.id, message.text)
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
        await db.smm.add_phone(message.chat.id, phone)
        markup = types.ReplyKeyboardRemove()
        await message.answer("Введите cвой возраст 👇", reply_markup=markup)
        await state.set_state(st.age)

    else:
        await message.answer("Для отправки нажмите на кнопку ниже")


@message_router.message(st.age)
async def age(message: Message, state: FSMContext):
    if message.text.isdigit() and 0 < int(message.text) < 120:
        await db.smm.add_age(message.chat.id, int(message.text))
        await message.answer("Введите свой город 👇")
        await state.set_state(st.town)

    else:
        await message.answer("❌ Неверный возраст, попробуйте еще раз")


@message_router.message(st.town)
async def town(message: Message, state: FSMContext, fl=False, town=""):
    # url = "https://ru.wikipedia.org/wiki/Список_городов_России"
    # df = pd.read_html(url)[0]
    # cities = df["Город"].to_list()
    
    cities = constants.cities
    if fl or message.text.capitalize() in cities:
        if town == "":
            await db.smm.add_town(message.chat.id, message.text.capitalize())
        else:
            await db.smm.add_town(message.chat.id, town)
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
        from io import BytesIO
        
        file_id = message.photo[-1].file_id if message.content_type == "photo" else message.animation.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Скачиваем файл в память
        file_buffer = BytesIO()
        await bot.download_file(file_path, destination=file_buffer)
        file_buffer.seek(0)
        image_bytes = file_buffer.read()
        
        # Обрезаем фото
        cropped_bytes = await cut_photo(image_bytes)
        #TODO Сохранение обрезанного фото в S3 только после того как пользователь нажал на кнопку "Применить"
        try:
            await upload_profile_image(cropped_bytes, message.chat.id)
        except Exception:
            await message.answer("Не удалось сохранить фото в хранилище. Попробуйте еще раз.")
            return
        await db.smm.add_photo(message.chat.id,
                               message.photo[
                                   -1].file_id if message.content_type == "photo" else message.animation.file_id)
        btns = [[InlineKeyboardButton(text="Изменить", callback_data="photo|change"),
                 InlineKeyboardButton(text="Применить", callback_data="photo|accept")]]
        btns = InlineKeyboardMarkup(inline_keyboard=btns)
        
        # Создаем BufferedInputFile из байтов и отправляем
        photo_file = BufferedInputFile(cropped_bytes, filename=f"{message.chat.id}.jpg")
        await message.answer_photo(photo=photo_file, caption="Ваша фотография", reply_markup=btns)
    else:
        await message.answer("❌ Неверный формат, отправьте фотографию")


@message_router.message(st.description)
async def send_cost(message: Message, state: FSMContext):
    if len(message.text) > 500:
        await message.answer("Слишком длинное описание, попробуйте сократить (до 500 символов)")
        return

    await db.smm.add_description(message.chat.id, message.text)
    await message.answer("Начальная цена ваших услуг в рублях за месяц 👇")
    await state.set_state(st.cost)


@message_router.message(st.cost)
async def cost(message: Message, state: FSMContext):
    if message.text.isdigit() and 15000 <= int(message.text) <= 10000000:
        await db.smm.add_cost(message.chat.id, int(message.text))
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


@message_router.message(F.text == "Тех. поддержка 🛠")
async def support(message: Message, state: FSMContext):
    await message.answer("Здравствуйте! Это служба технической поддержки.\nКак мы можем вам помочь?")
    await state.set_state(st.support)


@message_router.message(st.support)
async def ans_sup(message: Message, state: FSMContext):
    await message.answer(text="Ваше собщение было доставлено администратору. Ожидайте ответа")
    await db.users.add_support_request(message.text, message.chat.id, message.from_user.url)
    state_data = await state.get_data()
    await state.clear()
    await state.update_data(state_data)
    message_text = f"Вам пришло уведомление!\n\nПользователь <a href='{message.from_user.url}'>{message.chat.first_name}</a> обратился в тех. поддержку"
    for admin in config.tg_bot.admins:
        await bot.send_message(chat_id=admin,
                               text=message_text)


@message_router.message(F.text == "Просмотреть заявки 📩")
async def requests(message: Message, state: FSMContext):
    if message.chat.id in config.tg_bot.admins:
        requests = await db.users.get_support_requests()
        await iterate_requests(message, state, requests)
    else:
        await message.answer("Вы не являетесь администратором")


@message_router.message(st.support_reply)
async def support_reply(message: Message, state: FSMContext):
    state_data = await state.get_data()
    try:
        await bot.send_message(chat_id=state_data["user_id"],
                               text=f"Вам пришло уведомление от Администратора!\n\n{message.text}")
        await message.answer(text="Сообщение доставлено!")
    except TelegramForbiddenError as e:
        await message.answer(text="Ваш бот заблокирован пользователем")
    await db.users.answer_request(state_data["requests"][state_data["i"]][0], state_data["requests"][state_data["i"]][1])
    await message.delete()
    last_request_message_id = state_data.get("last_request_message_id")
    if last_request_message_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_request_message_id)
        except Exception:
            pass
    await requests(message, state)


@message_router.message(st.promo)
async def promo(message: Message, state: FSMContext, fl=True, promo=None):
    user_id = message.chat.id

    if promo is None:
        promo = (message.text or "").strip()
    else:
        promo = str(promo).strip()
    promo = promo.lower()
    tas = await db.ta.get_ta_by_user_id(user_id)
    profile = await db.smm.get_profile_by_id(user_id)
    if profile is None:
        btn = [[KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
               [KeyboardButton(text="Избранные контакты 🤝")],
               [KeyboardButton(text="Оформить подписку 🎟")]]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer("Пожалуйста, заполните профиль, нажав на кнопку 'Профиль', и повторите попытку",
                             reply_markup=btn)
        return

    smm_id, full_name, phone, user_id, age, town, cost, photo, username, description, date_sub = profile
    has_s3_photo = await is_s3_image_exists(user_id)
    if None in [full_name, phone, age, town, cost, description] or len(tas) == 0 or not has_s3_photo:
        btn = [[KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
               [KeyboardButton(text="Избранные контакты 🤝")],
               [KeyboardButton(text="Оформить подписку 🎟")]]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer("Пожалуйста, заполните все поля профиля, нажав на кнопку 'Профиль', и повторите попытку",
                             reply_markup=btn)
        return
    if promo == "-":
        # if fl and not await db.smm.is_used_free_sub(message.chat.id):
        #     btns = [[InlineKeyboardButton(text="Активировать", callback_data=f"free_sub|use|{message.chat.id}")],
        #             [InlineKeyboardButton(text="Использовать потом", callback_data=f"free_sub|then")]]
        #     btns = InlineKeyboardMarkup(inline_keyboard=btns)
        #     await message.answer(text="Вам доступен пробный период 7 дней", reply_markup=btns)
        # else:
        cost = 1000
        discount3 = 0.1
        discount6 = 0.25
        discount12 = 0.4
        # btn = [
        #     [InlineKeyboardButton(text="1 месяц", callback_data=f"sub|1|{cost}|{user_id}")],
        #     [InlineKeyboardButton(text="3 месяца",
        #                           callback_data=f"sub|3|{int(3 * cost * (1 - discount3))}|{user_id}")],
        #     [InlineKeyboardButton(text="6 месяцев",
        #                           callback_data=f"sub|6|{int(6 * cost * (1 - discount6))}|{user_id}")],
        #     [InlineKeyboardButton(text="12 месяцев",
        #                           callback_data=f"sub|12|{int(12 * cost * (1 - discount12))}|{user_id}")]
        # ]
        btn = [
            [InlineKeyboardButton(text="1 месяц", web_app=WebAppInfo(
                url=build_webapp_url(f"templates/payment.html?price={cost}&days={30}&req=subscription")))],
            [InlineKeyboardButton(text="3 месяца", web_app=WebAppInfo(
                url=build_webapp_url(f"templates/payment.html?price={int(3 * cost * (1 - discount3))}&days={90}&req=subscription")))],
            [InlineKeyboardButton(text="6 месяцев", web_app=WebAppInfo(
                url=build_webapp_url(f"templates/payment.html?price={int(6 * cost * (1 - discount6))}&days={180}&req=subscription")))],
            [InlineKeyboardButton(text="12 месяцев", web_app=WebAppInfo(
                url=build_webapp_url(f"templates/payment.html?price={int(12 * cost * (1 - discount12))}&days={360}&req=subscription")))],
        ]
        btn = InlineKeyboardMarkup(inline_keyboard=btn)
        await message.answer(
            text=f"Выберите длительность подписки 👇\n\n1 месяц - {cost} ₽\n3 месяца - {int(3 * cost * (1 - discount3))} ₽ (Скидка {int(discount3 * 100)}%)\n6 месяцев - {int(6 * cost * (1 - discount6))} ₽ (Скидка {int(discount6 * 100)}%)\n12 месяцев - {int(12 * cost * (1 - discount12))} ₽ (Скидка {int(discount12 * 100)}%)",
            reply_markup=btn
        )
    else:
        promos = await db.smm.get_all_promos()
        promo_data = promos.get(promo)
        if promo_data is not None:
            promo_usage = promo_data[0]
            promo_users_raw = promo_data[1] or "-"
            promo_duration = promo_data[2]
            promo_text = promo_data[3]
            promo_users = [p.strip() for p in promo_users_raw.split(",") if p.strip()] or ["-"]

            users_promos_res = await db.smm.get_users_promos(user_id)
            users_promos = users_promos_res[0][0] if users_promos_res else None
            if users_promos is not None:
                users_promos = [p.strip() for p in users_promos.split(",") if p.strip()]
            else:
                users_promos = []

            if (promo_usage > 0 or promo_usage < -100000) and promo not in users_promos and (
                    str(user_id) in promo_users or promo_users[0] == '-'):
                btn = [
                    [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
                    [KeyboardButton(text="Избранные контакты 🤝")],
                ]
                if message.chat.id in config.tg_bot.admins:
                    btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
                btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
                await message.answer(text=f"{promo_text}", reply_markup=btn)
                await db.smm.add_date_sub(message.chat.id, datetime.utcnow() + timedelta(days=promo_duration))
                await db.smm.add_payment(message.chat.id, datetime.utcnow(),
                                         datetime.utcnow() + timedelta(days=promo_duration), 0)
                scheduler.add_job(sub_end, DateTrigger(datetime.now() + timedelta(days=promo_duration)),
                                  args=[message.chat.id])
                await db.smm.use_promo(promo, user_id)
            elif promo_usage <= 0:
                await message.answer(
                    text="Спасибо за интерес, но этот промокод больше не действует.\nСледите за нашими новыми акциями!")

                await extend_sub(message, state)
                return
            elif str(user_id) not in promo_users and promo_users[0] != '-':
                await message.answer(text="Этот промокод не принадлежит вам.\nСледите за нашими новыми акциями!")
                await extend_sub(message, state)
                return
            else:
                await message.answer(text="Вы уже использовали этот промокод.\nСледите за нашими новыми акциями!")
                await extend_sub(message, state)
                return
        else:
            await message.answer(text="К сожалению, такого промокода не существует.\nСледите за нашими новыми акциями!")
            await extend_sub(message, state)
            return

    state_data = await state.get_data()
    await state.clear()
    await state.update_data(state_data)


@message_router.message(Command("i_looking_smm"))
async def search_by_field(message: Message, state: FSMContext, smm=False, edit=False, clear=True):
    state_data = await state.get_data()
    f = []
    field = await db.ta.get_all_field()

    for i in range(len(field)):
        cnt = 0
        ta = await db.ta.get_ta_by_field(field[i][0])
        for j in range(len(ta)):
            ta[j] = ta[j][0]
            if 'ta' in state_data and ta[j] in state_data['ta']:
                cnt += 1
        f.append(f"[{cnt}/{len(ta)}] {field[i][0]}")
    btns = []
    for i in range(len(f)):
        btns.append([InlineKeyboardButton(text=f"{f[i]}", callback_data=f"field|{(f[i].split('] '))[1]}|{smm}")])
    btns = InlineKeyboardMarkup(inline_keyboard=btns)
    if edit:
        await message.edit_text(text="Выберите вашу сферу деятельности👇", reply_markup=btns)
    else:
        await message.answer(text="Выберите вашу сферу деятельности👇", reply_markup=btns)


@message_router.message(Command("test"))
async def test(message: Message):
    await message.answer(text="1")
    scheduler.add_job(func=test2, trigger=DateTrigger(datetime.now() + timedelta(seconds=30)), args=[message.chat.id])


async def test2(user_id):
    await bot.send_message(chat_id=user_id, text="2")


@message_router.message()
async def messages(message: Message, state: FSMContext):
    state_data = await state.get_data()
    if "town" in state_data and state_data["town"]:
        dict_of_smm = state_data["town_d"]
        await state.clear()
        await state.update_data(state_data)
        await state.update_data(town_search=message.text.lower())
        await state.update_data(town=False)
        if message.text != "-":
            i = 0
            for k, v in dict_of_smm:
                if v[2].lower() != message.text.lower():
                    del dict_of_smm[i]
                i += 1
        await search_by_cost(message, state, dict_of_smm)
    elif "cost" in state_data and state_data["cost"]:
        dict_of_smm = state_data["cost_d"]
        if message.text.isdigit():
            i = 0
            for k, v in dict_of_smm:
                if v[4] < int(message.text):
                    del dict_of_smm[i]
                i += 1
            await state.clear()
            await state.update_data(state_data)
            await state.update_data(cost_search=int(message.text))
            await state.update_data(cost=False)
            await list_of_smm(message, dict_of_smm, 0, state)
        else:
            await message.answer(text="Введите число")
