from dataclasses import dataclass
from typing import List

from environs import Env


@dataclass
class TgBotConfig:
    token: str
    pay_token: str
    admins: List[int]
    prof: str


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str
    port: str


@dataclass
class RedisConfig:
    host: str
    use_redis: bool
    port: int


@dataclass
class Yookassa:
    shop_id: int
    secret_key: str

@dataclass
class GPTConfig:
    api_key: str
    asst_key: str

@dataclass
class Mistral:
    api_key: str
    model: str

@dataclass
class ProfConfig:
    i_am: str
    i_looking: str
    prof: str

@dataclass
class Config:
    tg_bot: TgBotConfig
    db: DbConfig
    redis: RedisConfig
    yookassa: Yookassa
    gpt: GPTConfig
    mistral: Mistral
    prof: ProfConfig


def load_config(path: str = None):
    import os
    
    # Автоматическое определение .env файла
    if path is None:
        # Проверяем переменные окружения Docker
        if "BOT_PROF" in os.environ:
            prof = os.environ["BOT_PROF"]
            if prof == "smm":
                path = "smm.env"
            elif prof == "massage":
                path = "massage.env"
            else:
                path = ".env"  # fallback
    
    
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBotConfig(
            token=env.str("BOT_TOKEN"), pay_token=env.str("PAY_TOKEN"),
            admins=list(map(int, env.str("ADMINS").split(","))), prof=env.str("BOT_PROF")),
        db=DbConfig(
            host=env.str("DB_HOST"),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
            port=env.str("DB_PORT"),
        ),
        redis=RedisConfig(host=env.str("REDIS_HOST"), use_redis=env.bool("USE_REDIS"), port=env.int("REDIS_PORT")),
        yookassa=Yookassa(
            shop_id=env.int("YOOKASSA_SHOP_ID"),
            secret_key=env.str("YOOKASSA_SECRET_KEY")
        ),
        gpt=GPTConfig(api_key=env.str("GPT_API_KEY"), asst_key=env.str("GPT_ASST_KEY")),
        mistral=Mistral(api_key=env.str("MISTRAL_API_KEY"), model=env.str("MISTRAL_MODEL")),
        prof=ProfConfig(i_am=env.str("I_AM"), i_looking=env.str("I_FIND"), prof=env.str("BOT_PROF"))
    )


# Загружаем конфигурацию один раз при импорте модуля
config = load_config()
