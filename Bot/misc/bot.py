from Bot.config import config
from aiogram import Bot


BOT_TOKEN = config.tg_bot.token

bot = Bot(BOT_TOKEN, parse_mode="HTML")