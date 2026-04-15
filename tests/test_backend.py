import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from Backend import app
from Database.session import Base, get_db  # где у вас Base = declarative_base()
from Bot.config import config

# Создание тестовой in-memory БД
DATABASE_URL = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.database}"

engine = create_async_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def make_auth_headers(user_id: int) -> dict[str, str]:
    payload = {
        "auth_date": str(int(time.time())),
        "user": json.dumps({"id": user_id}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", config.tg_bot.token.encode(), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return {"X-Telegram-Init-Data": urlencode(payload)}


# Фикстура БД-сессии
@pytest_asyncio.fixture()
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    await engine.dispose()


# Подмена зависимости get_db
@pytest.fixture(autouse=True)
def override_get_db(db_session):
    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override


# Асинхронный клиент FastAPI
@pytest_asyncio.fixture()
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# Сам тест
@pytest.mark.asyncio
async def test_profile(async_client):
    json = {
        'user_id': 10,
        'age': 10,
        'phone': "89191111111",
        'name': 'Vasya',
        'cost': 10,
        'town': 'A',
        'description': 'test'
    }

    # POST: создание/обновление профиля
    headers = make_auth_headers(json["user_id"])

    response = await async_client.post("/profile", json=json, headers=headers)
    assert response.status_code == 200

    # GET: получение профиля
    response = await async_client.get(f"/profile/info/{json['user_id']}", headers=headers)
    assert response.status_code == 200
    responsejs = response.json()
    assert responsejs['result']
    assert responsejs['user_id'] == json['user_id']
    assert responsejs['name'] == json['name']


@pytest.mark.asyncio
async def test_pay_token(async_client):
    import Backend

    class FakePayment:
        id = "payment-id"
        confirmation = type("Confirmation", (), {"confirmation_token": "token-123"})()

        @staticmethod
        def create(*args, **kwargs):
            return FakePayment()

    headers = make_auth_headers(10)
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(Backend, "Payment", FakePayment)
    json = {
        'plan': 'subscription_30',
        'email': 'test@gmail.com',
    }
    response = await async_client.post('/payment/token', json=json, headers=headers)
    assert response.status_code == 200
    response = response.json()
    assert response['result']
    assert response['id'] is not None
    assert response['confirmation_token'] is not None
    monkeypatch.undo()
