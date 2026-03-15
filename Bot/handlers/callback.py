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
_TA_REFRESH_TASKS = {}


def _extract_ta_options(markup: InlineKeyboardMarkup) -> list[str]:
    options = []
    for row in markup.inline_keyboard[:-1]:
        options.append(row[0].text.replace("✅ ", ""))
    return options


def _toggle_ta(state_ta: list[str], options: list[str], index: int) -> tuple[list[str], list[str]]:
    selected = list(state_ta or [])
    option = options[index]
    if option in selected:
        selected.remove(option)
    else:
        selected.append(option)
    labels = [f"✅ {opt}" if opt in selected else opt for opt in options]
    return selected, labels


def _schedule_ta_refresh(
    *,
    key: tuple[int, int, str],
    message: Message,
    labels: list[str],
    search_mode: bool,
):
    prev_task = _TA_REFRESH_TASKS.get(key)
    if prev_task and not prev_task.done():
        prev_task.cancel()

    async def _refresh():
        try:
            # Coalesce multiple fast clicks into a single Telegram edit.
            await asyncio.sleep(0.08)
            if search_mode:
                await search_by_ta(message, labels, fl=False)
            else:
                await ta_choose(message, labels, fl=False)
        finally:
            _TA_REFRESH_TASKS.pop(key, None)

    _TA_REFRESH_TASKS[key] = asyncio.create_task(_refresh())

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
    if data[1] == "done":
        await callback.answer()
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
        await callback.answer()
        await search_by_field(message, state, smm=True, edit=True)
    else:
        options = _extract_ta_options(message.reply_markup)
        option_idx = int(data[1])
        clicked_option = options[option_idx]
        was_selected = clicked_option in state_data.get("ta", [])
        selected, labels = _toggle_ta(state_data.get("ta", []), options, int(data[1]))
        await state.update_data(ta=selected)
        await callback.answer(
            text=(
                f"➕ Добавлено: {clicked_option}"
                if not was_selected
                else f"➖ Убрано: {clicked_option}"
            )
        )
        _schedule_ta_refresh(
            key=(message.chat.id, message.message_id, "ta"),
            message=message,
            labels=labels,
            search_mode=False,
        )


@callback_router.callback_query(lambda q: "talook" == q.data.split('|')[0])
async def talook(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")
    if data[1] == "done":
        await callback.answer()
        dict_of_smm = await db.smm.get_smm_by_ta(state_data['ta'])
        await search_by_town(message, state, dict_of_smm)
    elif data[1] == "back":
        await callback.answer()
        await search_by_field(message, state, smm=False, edit=True)
    else:
        options = _extract_ta_options(message.reply_markup)
        option_idx = int(data[1])
        clicked_option = options[option_idx]
        was_selected = clicked_option in state_data.get("ta", [])
        selected, labels = _toggle_ta(state_data.get("ta", []), options, int(data[1]))
        await state.update_data(ta=selected)
        await callback.answer(
            text=(
                f"➕ Добавлено: {clicked_option}"
                if not was_selected
                else f"➖ Убрано: {clicked_option}"
            )
        )
        _schedule_ta_refresh(
            key=(message.chat.id, message.message_id, "talook"),
            message=message,
            labels=labels,
            search_mode=True,
        )


@callback_router.callback_query(lambda q: "choose_smm" == q.data.split('|')[0])
async def choose_smm(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    message = callback.message
    data = callback.data.split("|")
    if data[1] == "buy":
        selected_user_id = int(data[2])
        btn = [
            [KeyboardButton(text="Меню ☰"), KeyboardButton(text="Тех. поддержка 🛠")],
            [KeyboardButton(text="Избранные контакты 🤝")],
        ]
        if message.chat.id in config.tg_bot.admins:
            btn.append([KeyboardButton(text="Просмотреть заявки 📩")])
        if await db.smm.is_smm(message.chat.id) and await db.smm.get_date_sub(message.chat.id) < datetime.utcnow():
            btn.append([KeyboardButton(text="Оформить подписку 🎟")])
        btn = ReplyKeyboardMarkup(keyboard=btn, resize_keyboard=True)
        current_idx = state_data.get("it", 0)
        current_list = state_data.get("dos", [])
        await db.contacts.add_bought_contact(message.chat.id, selected_user_id)
        await message.delete()
        await message.answer("Этот контакт добавлен в избранное", reply_markup=btn)
        await bot.send_message(text="Вас добавили в избранное 👍", chat_id=selected_user_id)
        if current_list:
            safe_idx = min(current_idx, len(current_list) - 1)
            await list_of_smm(message, current_list, safe_idx, state, fl=False, show_found=False)
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
        current_idx = state_data.get("it", 0)
        current_list = state_data.get("dos", [])
        await message.delete()
        await message.answer(text="Контакт удален из избранного")
        if current_list:
            safe_idx = min(current_idx, len(current_list) - 1)
            await list_of_smm(message, current_list, safe_idx, state, fl=False, show_found=False)
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
        dict_of_contacts = await db.contacts.get_bought_contacts(message.chat.id)
        if len(dict_of_contacts) == 0:
            await message.delete()
            await message.answer(text="🤷‍♂️ Вы пока ещё не выбрали ни одного контакта")
        else:
            await message.answer(text="Контакт удален из избранного")
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
    # Acknowledge instantly to remove Telegram spinner before DB/read + markup update.
    await callback.answer()
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
