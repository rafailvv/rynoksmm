import os
import asyncio
import time

from aiogram import Bot, Dispatcher
from datetime import datetime, timedelta
import subprocess

from dotenv import dotenv_values
from Bot.config import config

from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from Bot.misc.scheduler import scheduler

from aiogram.types import FSInputFile

from Bot.misc.bot import bot

DB_NAME = config.db.database
DB_USER = config.db.user
DB_PASS = config.db.password
DB_HOST = config.db.host
DB_PORT = config.db.port
USER_ID = 5283298935


async def send_backup(user_id, backup_path):
    attempt = 0
    while attempt < 100:
        try:
            await bot.send_document(user_id, document=FSInputFile(backup_path), caption=datetime.now().strftime('%H:%M:%S %d.%m.%Y'))

            os.remove(backup_path)
            break
        except Exception as e:
            attempt += 1
            print(f"Network error: {e}")
            print(f"Retry attempt {attempt}")



async def backup_database():
    backup_name = f"backup_{datetime.now().strftime('%Y_%m_%d__%H_%M_%S')}.sql"
    backup_path = f"Backup/backups/{backup_name}"
    os.environ['PGPASSWORD'] = DB_PASS
    command = f"pg_dump -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} -w -F c -b -v -f {backup_path}"
    subprocess.run(command, shell=True)

    return backup_path


async def scheduler_():
    backup_path = await backup_database()
    await send_backup(USER_ID, backup_path)
    scheduler.add_job(scheduler_, trigger=DateTrigger(datetime.now() + timedelta(seconds=900)))
