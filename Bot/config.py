from dataclasses import dataclass
from typing import List

from environs import Env


@dataclass
class TgBotConfig:
    token: str
    pay_token: str
    admins: List[int]


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


@dataclass
class Yookassa:
    shop_id: int
    secret_key: str


@dataclass
class Config:
    tg_bot: TgBotConfig
    db: DbConfig
    redis: RedisConfig
    yookassa: Yookassa


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBotConfig(
            token=env.str("BOT_TOKEN"), pay_token=env.str("PAY_TOKEN"),
            admins=list(map(int, env.str("ADMINS").split(",")))),
        db=DbConfig(
            host=env.str("DB_HOST"),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
            port=env.str("DB_PORT"),
        ),
        redis=RedisConfig(host=env.str("REDIS_HOST"), use_redis=env.bool("USE_REDIS")),
        yookassa=Yookassa(
            shop_id=env.int("YOOKASSA_SHOP_ID"),
            secret_key=env.str("YOOKASSA_SECRET_KEY")
        )
    )


config = load_config(".env")
