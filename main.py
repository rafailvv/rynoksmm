import asyncio
import logging
import json

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram import Bot, Dispatcher

from Bot.config import config
from Bot.handlers import *

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
from PIL import Image, ImageDraw

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from Bot.misc.scheduler import scheduler

from aiogram.fsm.storage.redis import RedisStorage, Redis

from datetime import datetime, timedelta

from Bot.misc.bot import bot

from Backup.backup import scheduler_

from Database.session import BaseDatabase

import aioboto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if config.redis.use_redis:
    redis = Redis(host=config.redis.host, port=config.redis.port)
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)
else:
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

dp.include_routers(message_router, callback_router)


async def main():
    logging.info("Starting bot")
    try:
        await minio_create_bucket(f"{config.prof.prof}")
        await BaseDatabase(config).init_db()
        await db.ta.load_all_ta()
        await bot.delete_webhook(drop_pending_updates=True)
        scheduler.start()
        scheduler.add_job(scheduler_, trigger=DateTrigger(datetime.now() + timedelta(seconds=5)))
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Error occurred: {e}")


async def minio_create_bucket(bucket: str):
    session = aioboto3.Session()

    async with session.client(
        "s3",
        endpoint_url="http://minio:9000",
        aws_access_key_id=config.minio.access_key,
        aws_secret_access_key=config.minio.secret_key,
        region_name="us-east-1",
    ) as s3:
        bucket_policy = json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowPublicRead",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{bucket}/*"],
                    }
                ],
            }
        )

        try:
            await s3.head_bucket(Bucket=bucket)
            print("Bucket already exists:", bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                await s3.create_bucket(Bucket=bucket)
                print("Bucket created:", bucket)
            else:
                raise e

        await s3.put_bucket_policy(Bucket=bucket, Policy=bucket_policy)
        await s3.put_object(Bucket=bucket, Key="images/", Body=b"")
        await s3.put_object(Bucket=bucket, Key="images/system/", Body=b"")


if __name__ == "__main__":
    asyncio.run(main())

