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

from Database.manager import db

from Bot.misc.states import SmmStatesGroup as st
from Bot.misc.methods import *
from Bot.handlers.message import *
from Bot.config import config
import json

from PIL import Image, ImageDraw

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

from aiogram.fsm.storage.redis import RedisStorage, Redis

from datetime import datetime, timedelta

from Bot.misc.scheduler import scheduler

from Bot.misc.bot import *

from aiogram.exceptions import TelegramForbiddenError

from openai import OpenAI


callback_router = Router()

def load_prof_details():
    """Загружает детали профессий из JSON файла"""
    try:
        with open("prof_details.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

prof_details = load_prof_details()


@callback_router.callback_query(lambda q: "menu" == q.data.split('|')[0])
async def menu(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")
    if data[1] == "smm":
        await state.clear()
        await state.update_data(ta=[])
        await smm_menu(callback.message, state)
    elif data[1] == "looking_smm":
        await state.clear()
        await state.update_data(ta=[])
        await search_by_field(callback.message, state, smm=False)
    elif data[1] == "ai":
        if "user_requests_limit" not in state_data:
            state_data["user_requests_limit"] = 10
        if "user_requests_count" not in state_data:
            state_data["user_requests_count"] = 0
        await state.update_data(state_data)
        await state.set_state(st.thread_state)
        
        # Получаем данные для текущей профессии
        prof_type = config.prof.prof
        prof_data = prof_details.get(prof_type, {})
        
        btns = [[KeyboardButton(text=prof_data.get("ai_exit", "Выйти из НейроБот ❌"))]]
        btns = ReplyKeyboardMarkup(keyboard=btns, resize_keyboard=True)
        ai_name = prof_data.get("ai_name", "НейроБот").replace(" 🤖", "")
        await message.answer(f"Добро пожаловать в {ai_name}, он поможет вам в написании контента и упаковке профиля.\nУ вас осталось {state_data['user_requests_limit'] - state_data['user_requests_count']} запросов", reply_markup=btns)

    await callback.answer()


@callback_router.callback_query(lambda q: "ta" == q.data.split('|')[0])
async def ta(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")
    t = []
    for i in range(len(message.reply_markup.inline_keyboard) - 1):
        t.append(message.reply_markup.inline_keyboard[i][0].text)
    if data[1] == "done":
        # await db.add_ta(message.chat.id, t)
        btn = [
            [InlineKeyboardButton(text=f"Опубликовать",
                                  callback_data=f"add_field|post")],
            [InlineKeyboardButton(text="Выбрать доп. сферу деятельности", callback_data="add_field|add_sp")],
        ]
        btn = InlineKeyboardMarkup(inline_keyboard=btn)
        await message.answer(text="Сфера деятельности успешно выбрана", reply_markup=btn)
        await message.delete()
    elif data[1] == "back":
        await search_by_field(message, state, smm=True, edit=True)
    else:
        if t[int(data[1])][0] == "✅":
            t[int(data[1])] = t[int(data[1])][2:]
            state_data['ta'].remove(t[int(data[1])])
        else:
            state_data['ta'].append(t[int(data[1])])
            t[int(data[1])] = "✅ " + t[int(data[1])]

        await state.update_data(ta=state_data['ta'])
        await ta_choose(message, t, fl=False)
    await callback.answer()


@callback_router.callback_query(lambda q: "talook" == q.data.split('|')[0])
async def talook(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")
    t = []
    for i in range(len(message.reply_markup.inline_keyboard) - 1):
        t.append(message.reply_markup.inline_keyboard[i][0].text)
    print(state_data['ta'])
    if data[1] == "done":
        dict_of_smm = await db.smm.get_smm_by_ta(state_data['ta'])
        await search_by_town(message, state, dict_of_smm)
    elif data[1] == "back":
        await search_by_field(message, state, smm=False, edit=True)
    else:
        if t[int(data[1])][0] == "✅":
            t[int(data[1])] = t[int(data[1])][2:]
            state_data['ta'].remove(t[int(data[1])])
        else:
            state_data['ta'].append(t[int(data[1])])
            t[int(data[1])] = "✅ " + t[int(data[1])]
        # t.append("Применить")
        await state.update_data(ta=state_data['ta'])
        await search_by_ta(message, t, fl=False)
    await callback.answer()


@callback_router.callback_query(lambda q: "choose_smm" == q.data.split('|')[0])
async def choose_smm(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")
    if data[1] == "buy":
        btn = [
            [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        if await db.smm.is_smm(message.chat.id) and await db.smm.get_date_sub(message.chat.id) < datetime.utcnow():
            btn.append([KeyboardButton(text="Оформить подписку 🎟")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer(f"""Этот контакт добавлен в избранное \n""", reply_markup=btn)
        profile = await db.smm.get_profile_by_id_str(int(data[2]))
        smm_id, name, phone, user_id, age, city, cost, photo, tg, description = profile
        await db.contacts.add_bought_contact(message.chat.id, user_id)
        photo_url = get_image_url(user_id)
        await message.answer_photo(
            photo=photo_url,
            caption=f"""🙌 Имя: {name}\n📞 Номер телефона: {phone}\n🎂 Возраст: {age}\n🏙 Город: {city}\n💬 Телеграм: @{tg}\n📝 Описание: {description}\n💸 Цена за месяц: от {cost} руб.""",
        )
        await bot.send_message(text="Вас добавили в избранное 👍", chat_id=int(data[2]))
        await message.delete()
    elif data[1] == "next":
        await list_of_smm(
            message, state_data["dos"], state_data["it"] + 1, state, True
        )
    elif data[1] == "prev":
        await list_of_smm(
            message, state_data["dos"], state_data["it"] - 1, state, True
        )
    elif data[1] == "remove":
        await db.contacts.remove_contact(message.chat.id, int(data[2]))
        await message.answer(text="Контакт удален из избранного")
        await list_of_smm(message, state_data["dos"], state_data["it"], state)
    await callback.answer()


@callback_router.callback_query(lambda q: "contacts_smm" == q.data.split('|')[0])
async def menu(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")
    if data[1] == "next":
        await contacts(
            message, state, state_data["dos"], state_data["it"] + 1, True
        )
    elif data[1] == "prev":
        await contacts(
            message, state, state_data["dos"], state_data["it"] - 1, True
        )
    elif data[1] == "remove":
        await db.contacts.remove_contact(message.chat.id, int(data[2]))
        await message.answer(text="Контакт удален из избранного")
        dict_of_contacts = await db.contacts.get_bought_contacts(message.chat.id)
        await contacts(message, state, dict_of_contacts)
    await callback.answer()


@callback_router.callback_query(lambda q: "add_field" == q.data.split('|')[0])
async def menu(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")

    if data[1] == "add_sp":
        await search_by_field(message=message, state=state, smm=True, edit=True)
    elif data[1] == "post":
        await state.update_data(ta=[])
        await db.ta.add_ta(message.chat.id, state_data['ta'])
        btn = [[InlineKeyboardButton(text="Пропустить", callback_data="add_field|promo_skip")]]
        btn = InlineKeyboardMarkup(inline_keyboard=btn)
        await message.edit_text(text='Введите промокод', reply_markup=btn)
        await state.set_state(st.promo)
    elif data[1] == "then":
        btn = [
            [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
            [KeyboardButton(text="Избранные контакты 🤝")],
            [KeyboardButton(text="Оформить подписку 🎟 ")],
        ]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer(text="Вы сможете продлить подписку нажав на соответствующую кнопку", reply_markup=btn)
    elif data[1] == "promo_skip":
        await promo(message=message, state=state, promo="-")
    await callback.answer()


@callback_router.callback_query(lambda q: "field" == q.data.split('|')[0])
async def menu(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")

    ta = await db.ta.get_ta_by_field(data[1])
    for i in range(len(ta)):
        ta[i] = ta[i][0]
        if 'ta' in state_data and ta[i] in state_data['ta']:
            ta[i] = "✅ " + ta[i]
    if data[2] == "True":
        await ta_choose(message, ta, True)
    else:
        await search_by_ta(message, ta)
    await callback.answer()


@callback_router.callback_query(lambda q: "photo" == q.data.split('|')[0])
async def menu(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")

    await message.delete_reply_markup()
    if data[1] == "change":
        await change_photo(message=message, state=state)
    elif data[1] == "accept":
        await send_description(message=message, state=state)
    await callback.answer()


@callback_router.callback_query(lambda q: "free_sub" == q.data.split('|')[0])
async def menu(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")

    if data[1] == "use":
        btn = [
            [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        await message.answer(text="Подписка успешно продлена на 7 дней!\nТеперь ваш профиль виден другим пользователям", reply_markup=btn)
        await db.smm.use_free_sub(int(data[2]))
        await db.smm.add_date_sub(message.chat.id, datetime.utcnow() + timedelta(days=7))
        await db.smm.add_payment(message.chat.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=7), 0)
        scheduler.add_job(sub_end, DateTrigger(datetime.now() + timedelta(days=7)), args=[message.chat.id])
    elif data[1] == "then":
        await promo(message=message, state=state, fl=False, promo="-")
    await callback.answer()


@callback_router.callback_query(lambda q: "town" == q.data.split('|')[0])
async def menu(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")

    await message.delete()
    if not bool(int(data[1])):
        await message.answer("Введите свой город 👇")
        await state.set_state(st.town)
    else:
        await town(message, state, bool(int(data[1])), data[2])
    await callback.answer()


@callback_router.callback_query(lambda q: "sub" == q.data.split('|')[0])
async def menu(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")

    await pay_for_publication(message.chat.id, int(data[1]), int(data[2]))
    await callback.answer()


@callback_router.callback_query(lambda q: "req" == q.data.split('|')[0])
async def support(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")
    
    if data[1] == "reply":
        if await db.users.is_answered(state_data["request"][state_data['i']][0], int(data[2])):
            await message.answer(text="Эта заявка уже отвечена")
            await requests(message, state)
        else:
            await message.answer(text="Введите текст, который хотите отправить пользователю:")
            await state.update_data(user_id=data[2])
            await state.set_state(st.support_reply)

    elif data[1] == "next":
        await iterate_requests(message, state, state_data["request"], int(data[2]) + 1, fl=True)
    elif data[1] == "prev":
        await iterate_requests(message, state, state_data["request"], int(data[2]) - 1, fl=True)
    await callback.answer()


