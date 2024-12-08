from Bot.config import config
from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from openai import OpenAI

BOT_TOKEN = config.tg_bot.token

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

client = OpenAI(api_key=f"{config.gpt.api_key}")

assistant = client.beta.assistants.retrieve(config.gpt.asst_key)