from Bot.config import config
from aiogram import Bot
from aiogram.client.bot import DefaultBotProperties
from openai import AsyncOpenAI
from mistralai import Mistral

BOT_TOKEN = config.tg_bot.token

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

client = Mistral(api_key=f"{config.mistral.api_key}") if config.mistral.api_key else None
openrouter_client = AsyncOpenAI(
    api_key=config.openrouter.api_key,
    base_url="https://openrouter.ai/api/v1",
)

# client = OpenAI(api_key=f"{config.gpt.api_key}")
#
# assistant = client.beta.assistants.retrieve(config.gpt.asst_key)
