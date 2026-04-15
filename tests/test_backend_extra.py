import hashlib
import hmac
import json
import time
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from Backend import app
from Bot.config import config


def make_auth_headers(user_id: int) -> dict[str, str]:
    from urllib.parse import urlencode

    payload = {
        "auth_date": str(int(time.time())),
        "user": json.dumps({"id": user_id}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", config.tg_bot.token.encode(), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return {"X-Telegram-Init-Data": urlencode(payload)}


@pytest.mark.asyncio
async def test_load_prof_details_file_not_found(monkeypatch):
    import Backend

    def fail_open(*args, **kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("builtins.open", fail_open)
    assert Backend.load_prof_details() == {}


def test_backend_get_image_url():
    import Backend

    assert Backend.get_image_url("bucket", "1.jpg") == "https://s3.prof-tg.ru/bucket/images/1.jpg"


@pytest.mark.asyncio
async def test_users_created_bad_range_returns_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            "/users/created",
            params={"datefrom": "2026-01-03T00:00:00Z", "dateto": "2026-01-01T00:00:00Z"},
        )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_users_created_groups_by_day(monkeypatch):
    import Backend

    users = [
        SimpleNamespace(created_at=datetime(2026, 1, 1, 10, 0, 0)),
        SimpleNamespace(created_at=datetime(2026, 1, 1, 12, 0, 0)),
        SimpleNamespace(created_at=datetime(2026, 1, 2, 9, 0, 0)),
    ]
    monkeypatch.setattr(Backend.db.users, "get_users_created", AsyncMock(return_value=users))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            "/users/created",
            params={"datefrom": "2026-01-01T00:00:00Z", "dateto": "2026-01-02T00:00:00Z"},
        )

    assert res.status_code == 200
    payload = res.json()
    assert len(payload) == 2
    assert payload[0]["value"] == 2
    assert payload[1]["value"] == 1


@pytest.mark.asyncio
async def test_payment_token_exception_returns_false(monkeypatch):
    import Backend

    class FailPayment:
        @staticmethod
        def create(*args, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(Backend, "Payment", FailPayment)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/payment/token",
            json={"plan": "subscription_30", "email": "a@a.a"},
            headers=make_auth_headers(1),
        )

    assert res.status_code == 200
    assert res.json() == {"result": False}


@pytest.mark.asyncio
async def test_save_categories_error_returns_500(monkeypatch):
    import Backend

    monkeypatch.setattr(Backend.db.smm, "edit_categories", AsyncMock(side_effect=Exception("db error")))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/save_categories/",
            json={"user_id": 1, "categories": ["A"]},
            headers=make_auth_headers(1),
        )

    assert res.status_code == 500
    assert res.json()["detail"] == "db error"
