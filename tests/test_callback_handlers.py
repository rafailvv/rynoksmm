import importlib
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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


class FakeMessage:
    def __init__(self, chat_id=42, message_id=1, reply_markup=None):
        self.chat = FakeChat(chat_id)
        self.message_id = message_id
        self.reply_markup = reply_markup
        self.answer = AsyncMock()
        self.answer_photo = AsyncMock()
        self.edit_media = AsyncMock()
        self.edit_text = AsyncMock()
        self.edit_reply_markup = AsyncMock()
        self.delete = AsyncMock()
        self.delete_reply_markup = AsyncMock()


class FakeCallback:
    def __init__(self, data, message):
        self.data = data
        self.message = message
        self.answer = AsyncMock()


@pytest.fixture
def callback_module():
    return importlib.import_module("Bot.handlers.callback")


def _make_ta_markup(options):
    rows = [[InlineKeyboardButton(text=opt, callback_data="x")]
            for opt in options]
    rows.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="ta|back"),
        InlineKeyboardButton(text="Принять", callback_data="ta|done"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def test_extract_ta_options(callback_module):
    markup = _make_ta_markup(["✅ A", "B"])
    assert callback_module._extract_ta_options(markup) == ["A", "B"]


def test_toggle_ta_add_and_remove(callback_module):
    selected, labels = callback_module._toggle_ta([], ["A", "B"], 1)
    assert selected == ["B"]
    assert labels == ["A", "✅ B"]

    selected, labels = callback_module._toggle_ta(selected, ["A", "B"], 1)
    assert selected == []
    assert labels == ["A", "B"]


@pytest.mark.asyncio
async def test_schedule_ta_refresh_calls_ta_choose(callback_module, monkeypatch):
    message = FakeMessage(chat_id=7, message_id=99)
    monkeypatch.setattr(callback_module, "ta_choose", AsyncMock())

    callback_module._schedule_ta_refresh(
        key=(message.chat.id, message.message_id, "ta"),
        message=message,
        labels=["A"],
        search_mode=False,
    )
    await asyncio.sleep(0.12)

    callback_module.ta_choose.assert_awaited_once()
    assert (message.chat.id, message.message_id, "ta") not in callback_module._TA_REFRESH_TASKS


@pytest.mark.asyncio
async def test_ta_callback_toggles_and_schedules(callback_module, monkeypatch):
    markup = _make_ta_markup(["Design", "SMM"])
    message = FakeMessage(reply_markup=markup)
    callback = FakeCallback("ta|0", message)
    state = FakeState({"ta": []})
    called = {"count": 0}
    def _fake_schedule(*args, **kwargs):
        called["count"] += 1
    monkeypatch.setattr(callback_module, "_schedule_ta_refresh", _fake_schedule)

    await callback_module.ta(callback, state)

    assert state.data["ta"] == ["Design"]
    callback.answer.assert_awaited_once()
    assert "Добавлено" in callback.answer.await_args.kwargs["text"]
    assert called["count"] == 1


@pytest.mark.asyncio
async def test_talook_done_calls_search_by_town(callback_module, monkeypatch):
    message = FakeMessage()
    callback = FakeCallback("talook|done", message)
    state = FakeState({"ta": ["IT"]})

    fake_db = SimpleNamespace(smm=SimpleNamespace(get_smm_by_ta=AsyncMock(return_value={1: ("x",)})))
    monkeypatch.setattr(callback_module, "db", fake_db)
    monkeypatch.setattr(callback_module, "search_by_town", AsyncMock())

    await callback_module.talook(callback, state)

    callback_module.search_by_town.assert_awaited_once()


@pytest.mark.asyncio
async def test_choose_smm_buy_adds_contact_and_updates_list(callback_module, monkeypatch):
    message = FakeMessage(chat_id=101)
    callback = FakeCallback("choose_smm|buy|202", message)
    state = FakeState({"it": 0, "dos": [(1, ("N", 20, "M", None, 1000, "d", 1))]})

    fake_db = SimpleNamespace(
        contacts=SimpleNamespace(add_bought_contact=AsyncMock()),
        smm=SimpleNamespace(is_smm=AsyncMock(return_value=False)),
    )
    monkeypatch.setattr(callback_module, "db", fake_db)
    monkeypatch.setattr(callback_module, "bot", SimpleNamespace(send_message=AsyncMock()))
    monkeypatch.setattr(callback_module, "list_of_smm", AsyncMock())

    await callback_module.choose_smm(callback, state)

    fake_db.contacts.add_bought_contact.assert_awaited_once_with(101, 202)
    callback_module.bot.send_message.assert_awaited_once()
    callback_module.list_of_smm.assert_awaited_once()
    message.delete.assert_awaited_once()
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_menu_sub_calls_pay_for_publication(callback_module, monkeypatch):
    message = FakeMessage(chat_id=77)
    callback = FakeCallback("sub|10|300", message)
    state = FakeState()
    monkeypatch.setattr(callback_module, "pay_for_publication", AsyncMock())

    await callback_module.menu(callback, state)

    callback_module.pay_for_publication.assert_awaited_once_with(77, 10, 300)
    callback.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_support_reply_already_answered(callback_module, monkeypatch):
    message = FakeMessage()
    callback = FakeCallback("req|reply|5", message)
    state = FakeState({"requests": [(123, 5, "tg")], "i": 0})

    fake_db = SimpleNamespace(users=SimpleNamespace(is_answered=AsyncMock(return_value=True)))
    monkeypatch.setattr(callback_module, "db", fake_db)
    monkeypatch.setattr(callback_module, "requests", AsyncMock())

    await callback_module.support(callback, state)

    message.answer.assert_awaited_once()
    callback_module.requests.assert_awaited_once()


@pytest.mark.asyncio
async def test_support_reply_sets_state_when_not_answered(callback_module, monkeypatch):
    message = FakeMessage()
    callback = FakeCallback("req|reply|5", message)
    state = FakeState({"requests": [(123, 5, "tg")], "i": 0})

    fake_db = SimpleNamespace(users=SimpleNamespace(is_answered=AsyncMock(return_value=False)))
    monkeypatch.setattr(callback_module, "db", fake_db)

    await callback_module.support(callback, state)

    message.answer.assert_awaited_once()
    assert state.data["user_id"] == "5"
    assert state.state == callback_module.st.support_reply
