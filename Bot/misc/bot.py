from Bot.config import config
from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties

BOT_TOKEN = config.tg_bot.token

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))