from dataclasses import dataclass
from typing import List

from environs import Env


def _clean_env_value(value: str) -> str:
    return value.strip().strip("\"'")


@dataclass
class TgBotConfig:
    token: str
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
class OpenRouter:
    api_key: str
    model: str

@dataclass
class ProfConfig:
    i_am: str
    i_looking: str
    prof: str


@dataclass
class MinioConfig:
    access_key: str
    secret_key: str
    endpoint_url: str
    

@dataclass
class Config:
    tg_bot: TgBotConfig
    db: DbConfig
    redis: RedisConfig
    yookassa: Yookassa
    gpt: GPTConfig
    mistral: Mistral
    openrouter: OpenRouter
    prof: ProfConfig
    minio: MinioConfig


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
            elif prof in {"photo", "event"}:
                path = "event.env"
            else:
                path = ".env"  # fallback
    
    
    env = Env()
    env.read_env(path)
    minio = Env()
    minio.read_env("minio.env")
    openrouter_api = env.str("OPEN_ROUTER_API", default=None)
    if openrouter_api is None:
        openrouter_api = env.str("OPENROUTER_API_KEY")
    openrouter_model = env.str("OPEN_ROUTER_MODEL", default=None)
    if openrouter_model is None:
        openrouter_model = env.str("OPENROUTER_MODEL")

    return Config(
        tg_bot=TgBotConfig(
            token=env.str("BOT_TOKEN"),
            admins=list(map(int, env.str("ADMINS", default="").split(","))) if env.str("ADMINS", default="") else [],
            prof=env.str("BOT_PROF"),
        ),
        db=DbConfig(
            host=_clean_env_value(env.str("DB_HOST")),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
            port=env.str("DB_PORT"),
        ),
        redis=RedisConfig(
            host=_clean_env_value(env.str("REDIS_HOST")),
            use_redis=env.bool("USE_REDIS"),
            port=env.int("REDIS_PORT"),
        ),
        yookassa=Yookassa(
            shop_id=env.int("YOOKASSA_SHOP_ID"),
            secret_key=env.str("YOOKASSA_SECRET_KEY")
        ),
        gpt=GPTConfig(
            api_key=env.str("GPT_API_KEY", default=""),
            asst_key=env.str("GPT_ASST_KEY", default=""),
        ),
        mistral=Mistral(
            api_key=env.str("MISTRAL_API_KEY", default=""),
            model=env.str("MISTRAL_MODEL", default=""),
        ),
        openrouter=OpenRouter(api_key=openrouter_api, model=openrouter_model),
        prof=ProfConfig(i_am=env.str("I_AM"), i_looking=env.str("I_FIND"), prof=env.str("BOT_PROF")),
        minio=MinioConfig(
            access_key=minio.str("MINIO_ROOT_USER"),
            secret_key=minio.str("MINIO_ROOT_PASSWORD"),
            endpoint_url=_clean_env_value(minio.str("MINIO_ENDPOINT_URL", default="http://minio:9000")),
        )
    )



config = load_config()
