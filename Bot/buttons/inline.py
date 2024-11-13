from aiogram import Router
from aiogram.types import CallbackQuery

import asyncio
import os
import uuid

from Bot.config import config

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
from Bot.misc.bot import bot

from yookassa import Configuration, Payment
import uuid
from yookassa.domain.response import PaymentResponse

from aiogram.exceptions import TelegramForbiddenError


async def subscribe_notification_button(id):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Подписаться на уведомления 🔔", callback_data=f"notifications|{id}")]])