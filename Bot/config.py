from dataclasses import dataclass
from typing import List

from environs import Env


@dataclass
class TgBotConfig:
    token: str
    pay_token: str


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


@dataclass
class Config:
    tg_bot: TgBotConfig
    db: DbConfig
    redis: RedisConfig


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBotConfig(
            token=env.str("BOT_TOKEN"), pay_token=env.str("PAY_TOKEN")
        ),
        db=DbConfig(
            host=env.str("DB_HOST"),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
            port=env.str("DB_PORT"),
        ),
        redis=RedisConfig(host=env.str("REDIS_HOST")),
    )


config = load_config(".env")