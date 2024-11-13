from Bot.config import config
from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from openai import OpenAI

BOT_TOKEN = config.tg_bot.token

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

client = ""
assistant = ""

# client = OpenAI(api_key=f"{config.gpt.api_key}")
#
# assistant = client.beta.assistants.create(
#     name="SMM Helper",
#     instructions="Ты СММ помощник. Твоя задача помогать людям с их постами для соц. сетей. Всегда отвечай людям на русском языке. Всегда проверяй себя на орфографию и другие ошибки в предложениях",
#     tools=[{"type": "code_interpreter"}],
#     model="gpt-4o",
# )