import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from Backend import app, get_db
from Backend.models import Base  # где у вас Base = declarative_base()
import asyncio
from Bot.config import config

# Создание тестовой in-memory БД
DATABASE_URL = f"postgresql+asyncpg://{config.db.user}:{config.db.password}@{config.db.host}/{config.db.database}"

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# Фикстура БД-сессии
@pytest.fixture()
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
@pytest.fixture()
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
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
    response = await async_client.post("/profile", json=json)
    assert response.status_code == 200

    # GET: получение профиля
    response = await async_client.get(f"/profile/info/{json['user_id']}")
    assert response.status_code == 200
    assert response.json() == json
