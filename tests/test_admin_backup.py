from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_basic_auth_login_success_by_credentials():
    from Database.admin import BasicAuth
    from Bot.config import config

    class Req:
        def __init__(self):
            self.session = {}
            self.client = SimpleNamespace(host="10.0.0.1")

        async def form(self):
            return {"username": config.db.user, "password": config.db.password}

    req = Req()
    auth = BasicAuth(secret_key="s")
    assert await auth.login(req) is True
    assert req.session["authenticated"] is True


@pytest.mark.asyncio
async def test_basic_auth_login_localhost_bypass():
    from Database.admin import BasicAuth

    class Req:
        def __init__(self):
            self.session = {}
            self.client = SimpleNamespace(host="127.0.0.1")

        async def form(self):
            return {"username": "x", "password": "y"}

    req = Req()
    auth = BasicAuth(secret_key="s")
    assert await auth.login(req) is True


@pytest.mark.asyncio
async def test_basic_auth_login_fail_sets_error():
    from Database.admin import BasicAuth

    class Req:
        def __init__(self):
            self.session = {}
            self.client = SimpleNamespace(host="10.0.0.2")

        async def form(self):
            return {"username": "x", "password": "y"}

    req = Req()
    auth = BasicAuth(secret_key="s")
    assert await auth.login(req) is False
    assert req.session.get("auth_error") is True


@pytest.mark.asyncio
async def test_basic_auth_logout_and_authenticate():
    from Database.admin import BasicAuth

    req = SimpleNamespace(session={"authenticated": True})
    auth = BasicAuth(secret_key="s")
    assert await auth.authenticate(req) is True
    assert await auth.logout(req) is True
    assert req.session == {}


@pytest.mark.asyncio
async def test_send_backup_retries_then_success(monkeypatch):
    import Backup.backup as backup

    send_mock = AsyncMock(side_effect=[Exception("n1"), Exception("n2"), None])

    monkeypatch.setattr(backup, "bot", SimpleNamespace(send_document=send_mock))
    monkeypatch.setattr(backup.os, "remove", lambda *_: None)

    await backup.send_backup(1, "x.sql")

    assert send_mock.await_count == 3


@pytest.mark.asyncio
async def test_backup_database_builds_command(monkeypatch):
    import Backup.backup as backup

    class FakeDateTime:
        @classmethod
        def now(cls):
            return datetime(2026, 1, 2, 3, 4, 5)

    calls = []

    def fake_run(command, shell=True):
        calls.append((command, shell))

    monkeypatch.setattr(backup, "datetime", FakeDateTime)
    monkeypatch.setattr(backup.subprocess, "run", fake_run)

    path = await backup.backup_database()

    assert path.endswith("backup_2026_01_02__03_04_05.sql")
    assert calls and "pg_dump" in calls[0][0]


@pytest.mark.asyncio
async def test_scheduler_calls_backup_send_and_add_job(monkeypatch):
    import Backup.backup as backup

    monkeypatch.setattr(backup, "backup_database", AsyncMock(return_value="f.sql"))
    monkeypatch.setattr(backup, "send_backup", AsyncMock())
    add_job = AsyncMock()
    monkeypatch.setattr(backup, "scheduler", SimpleNamespace(add_job=add_job))

    await backup.scheduler_()

    backup.backup_database.assert_awaited_once()
    backup.send_backup.assert_awaited_once()
    add_job.assert_called_once()
