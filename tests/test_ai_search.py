import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class FakeState:
    def __init__(self, initial=None):
        self.data = dict(initial or {})
        self.state = None

    async def update_data(self, *args, **kwargs):
        if args:
            self.data.update(args[0])
        self.data.update(kwargs)

    async def get_data(self):
        return dict(self.data)

    async def set_state(self, value):
        self.state = value

    async def clear(self):
        self.data = {}


class FakeChat:
    def __init__(self, chat_id=42):
        self.id = chat_id


class FakeWaitMessage:
    def __init__(self):
        self.edit_text = AsyncMock()
        self.delete = AsyncMock()


class FakeMessage:
    def __init__(self, text=""):
        self.text = text
        self.chat = FakeChat()
        self.wait_message = FakeWaitMessage()
        self.answer = AsyncMock(return_value=self.wait_message)


@pytest.fixture
def message_module():
    return importlib.import_module("Bot.handlers.message")


def test_parse_ai_search_json_plain(message_module):
    parsed = message_module.parse_ai_search_json(
        '{"cities":["Москва"],"price_min":null,"price_max":"80 000 ₽","query_text":"нужен таргетолог"}'
    )

    assert parsed == {
        "cities": ["Москва"],
        "price_min": None,
        "price_max": 80000,
        "query_text": "нужен таргетолог",
    }


def test_parse_ai_search_json_markdown(message_module):
    parsed = message_module.parse_ai_search_json(
        '```json\n{"cities":"Казань","price_min":15000,"price_max":null,"query_text":"ведение соцсетей"}\n```'
    )

    assert parsed["cities"] == ["Казань"]
    assert parsed["price_min"] == 15000
    assert parsed["price_max"] is None


def test_parse_ai_search_json_broken(message_module):
    assert message_module.parse_ai_search_json("не json") is None


def test_rank_ai_search_results(message_module):
    candidates = [
        (1, ("A",), [1.0, 0.0]),
        (2, ("B",), [0.0, 1.0]),
        (3, ("C",), None),
        (4, ("D",), [0.8, 0.2]),
        (5, ("E",), [0.7, 0.3]),
        (6, ("F",), [0.6, 0.4]),
    ]

    ranked = message_module.rank_ai_search_results(candidates, [1.0, 0.0], limit=5)

    assert [item[0] for item in ranked] == [1, 4, 5, 6, 2]
    assert len(ranked) == 5


def test_build_missing_profile_message_lists_missing_fields(message_module):
    profile = (1, "Name", "", 10, None, "Москва", 50000, None, "user", " ", None)

    missing = message_module.get_missing_profile_fields(profile, tas=[], has_s3_photo=False)
    text = message_module.build_missing_profile_message(missing)

    assert missing == ["номер телефона", "возраст", "описание", "сферы деятельности", "фотография"]
    assert "Не заполнено:" in text
    assert "номер телефона" in text
    assert "фотография" in text


@pytest.mark.asyncio
async def test_ai_specialist_search_uses_ai_db_and_list(message_module, monkeypatch):
    message = FakeMessage("smm в Москве до 80000")
    state = FakeState({"old": "data"})
    candidates = [(1, ("Name", 30, "Москва", "photo", 70000, "desc", 1), [1.0, 0.0])]

    monkeypatch.setattr(
        message_module,
        "parse_ai_search_query",
        AsyncMock(
            return_value={
                "cities": ["Москва"],
                "price_min": None,
                "price_max": 80000,
                "query_text": "smm",
            }
        ),
    )
    monkeypatch.setattr(message_module, "make_embedding_safe", AsyncMock(return_value=[1.0, 0.0]))
    monkeypatch.setattr(
        message_module,
        "db",
        SimpleNamespace(smm=SimpleNamespace(get_smm_for_ai_search=AsyncMock(return_value=candidates))),
    )
    monkeypatch.setattr(message_module, "list_of_smm", AsyncMock())

    await message_module.ai_specialist_search(message, state)

    message_module.db.smm.get_smm_for_ai_search.assert_awaited_once_with(
        cities=["Москва"],
        price_max=80000,
    )
    message_module.list_of_smm.assert_awaited_once()
    assert state.data["ai_search_params"]["price_max"] == 80000
    message.wait_message.delete.assert_awaited_once()
