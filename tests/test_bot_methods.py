import importlib
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from PIL import Image


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


class FakeChat:
    def __init__(self, chat_id=42):
        self.id = chat_id


class FakeMessage:
    def __init__(self, chat_id=42):
        self.chat = FakeChat(chat_id)
        self.answer = AsyncMock()
        self.answer_photo = AsyncMock()
        self.edit_media = AsyncMock()
        self.edit_text = AsyncMock()
        self.edit_reply_markup = AsyncMock()


@pytest.fixture
def methods_module():
    return importlib.import_module("Bot.misc.methods")


@pytest.mark.asyncio
async def test_get_image_url(methods_module):
    url = methods_module.get_image_url(777)
    assert url.endswith("/images/777.jpg")


@pytest.mark.asyncio
async def test_is_s3_image_exists_status_200(methods_module, monkeypatch):
    class FakeResp:
        def __init__(self, status):
            self.status = status

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def __init__(self, timeout=None):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def head(self, *args, **kwargs):
            return FakeResp(200)

        def get(self, *args, **kwargs):
            return FakeResp(200)

    monkeypatch.setattr(methods_module.aiohttp, "ClientSession", FakeSession)
    assert await methods_module.is_s3_image_exists(1) is True


@pytest.mark.asyncio
async def test_is_s3_image_exists_status_405_then_206(methods_module, monkeypatch):
    class FakeResp:
        def __init__(self, status):
            self.status = status

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def __init__(self, timeout=None):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def head(self, *args, **kwargs):
            return FakeResp(405)

        def get(self, *args, **kwargs):
            return FakeResp(206)

    monkeypatch.setattr(methods_module.aiohttp, "ClientSession", FakeSession)
    assert await methods_module.is_s3_image_exists(2) is True


@pytest.mark.asyncio
async def test_is_s3_image_exists_exception(methods_module, monkeypatch):
    class BrokenSession:
        def __init__(self, timeout=None):
            self.timeout = timeout

        async def __aenter__(self):
            raise RuntimeError("boom")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(methods_module.aiohttp, "ClientSession", BrokenSession)
    assert await methods_module.is_s3_image_exists(3) is False


@pytest.mark.asyncio
async def test_is_s3_image_exists_status_not_found(methods_module, monkeypatch):
    class FakeResp:
        def __init__(self, status):
            self.status = status

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class FakeSession:
        def __init__(self, timeout=None):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def head(self, *args, **kwargs):
            return FakeResp(404)

    monkeypatch.setattr(methods_module.aiohttp, "ClientSession", FakeSession)
    assert await methods_module.is_s3_image_exists(4) is False


@pytest.mark.asyncio
async def test_pay_for_publication_calls_send_invoice(methods_module, monkeypatch):
    fake_bot = SimpleNamespace(send_invoice=AsyncMock())
    monkeypatch.setattr(methods_module, "bot", fake_bot)

    await methods_module.pay_for_publication(123, 30, 99)

    fake_bot.send_invoice.assert_awaited_once()
    kwargs = fake_bot.send_invoice.await_args.kwargs
    assert kwargs["chat_id"] == 123
    assert kwargs["payload"] == "post|30"
    assert kwargs["prices"][0].amount == 9900


@pytest.mark.asyncio
async def test_contacts_empty_list(methods_module):
    message = FakeMessage()
    state = FakeState()

    await methods_module.contacts(message, state, {})

    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_contacts_send_photo(methods_module):
    message = FakeMessage()
    state = FakeState()
    data = {
        11: (1, "Ann", "+7999", 11, 21, "Moscow", 5000, None, "ann_tg", "desc")
    }

    await methods_module.contacts(message, state, data, i=0, fl=False)

    assert state.data["it"] == 0
    assert state.data["dos"] == data
    message.answer_photo.assert_awaited_once()


@pytest.mark.asyncio
async def test_contacts_edit_media(methods_module):
    message = FakeMessage()
    state = FakeState()
    data = {
        11: (1, "Ann", "+7999", 11, 21, "Moscow", 5000, None, "ann_tg", "desc")
    }

    await methods_module.contacts(message, state, data, i=0, fl=True)

    message.edit_media.assert_awaited_once()


@pytest.mark.asyncio
async def test_ta_choose_with_custom_list(methods_module):
    message = FakeMessage()

    await methods_module.ta_choose(message, t=["A", "B"], fl=True)

    message.edit_text.assert_awaited_once()
    kwargs = message.edit_text.await_args.kwargs
    assert "Выбери вашу сферу" in kwargs["text"]


@pytest.mark.asyncio
async def test_ta_choose_reads_db_when_t_is_none(methods_module, monkeypatch):
    message = FakeMessage()
    fake_db = SimpleNamespace(ta=SimpleNamespace(get_all_field=AsyncMock(return_value=[("A",), ("B",)])))
    monkeypatch.setattr(methods_module, "db", fake_db)

    await methods_module.ta_choose(message, t=None, fl=False)

    message.edit_reply_markup.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_by_ta_edit_reply_markup(methods_module):
    message = FakeMessage()

    await methods_module.search_by_ta(message, t=["X"], fl=False)

    message.edit_reply_markup.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_by_ta_reads_db_when_t_is_none(methods_module, monkeypatch):
    message = FakeMessage()
    fake_db = SimpleNamespace(ta=SimpleNamespace(get_all_field=AsyncMock(return_value=[("A",), ("B",)])))
    monkeypatch.setattr(methods_module, "db", fake_db)

    await methods_module.search_by_ta(message, t=None, fl=True)

    message.edit_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_notification_when_profile_incomplete(methods_module, monkeypatch):
    fake_db = SimpleNamespace(
        ta=SimpleNamespace(get_ta_by_user_id=AsyncMock(return_value=[])),
        smm=SimpleNamespace(
            get_profile_by_id=AsyncMock(
                return_value=(1, None, "7900", 55, 18, "SPB", 1000, None, "user", "desc", None)
            )
        ),
    )
    fake_bot = SimpleNamespace(send_message=AsyncMock())
    monkeypatch.setattr(methods_module, "db", fake_db)
    monkeypatch.setattr(methods_module, "bot", fake_bot)
    monkeypatch.setattr(methods_module, "is_s3_image_exists", AsyncMock(return_value=False))

    await methods_module.send_notification(55, "Ivan")

    fake_bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_notification_complete_profile_does_not_send(methods_module, monkeypatch):
    fake_db = SimpleNamespace(
        ta=SimpleNamespace(get_ta_by_user_id=AsyncMock(return_value=[(1,)])),
        smm=SimpleNamespace(
            get_profile_by_id=AsyncMock(
                return_value=(1, "Name", "7900", 77, 20, "Kazan", 2000, "p", "tg", "desc", "2026-01-01")
            )
        ),
    )
    fake_bot = SimpleNamespace(send_message=AsyncMock())
    monkeypatch.setattr(methods_module, "db", fake_db)
    monkeypatch.setattr(methods_module, "bot", fake_bot)
    monkeypatch.setattr(methods_module, "is_s3_image_exists", AsyncMock(return_value=True))

    await methods_module.send_notification(77, "Petr")

    fake_bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_cut_photo_returns_square_jpeg(methods_module):
    img = Image.new("RGB", (120, 80), "red")
    b = BytesIO()
    img.save(b, format="PNG")

    out = await methods_module.cut_photo(b.getvalue())
    out_img = Image.open(BytesIO(out))

    assert out_img.format == "JPEG"
    assert out_img.size[0] == out_img.size[1]


@pytest.mark.asyncio
async def test_change_photo_and_send_description(methods_module):
    message = FakeMessage()
    state = FakeState()

    await methods_module.change_photo(message, state)
    await methods_module.send_description(message, state)

    assert state.state == methods_module.st.description
    assert message.answer.await_count == 2


@pytest.mark.asyncio
async def test_search_by_town_and_cost(methods_module):
    message = FakeMessage()
    state = FakeState()
    data = {1: ("value",)}

    await methods_module.search_by_town(message, state, data)
    await methods_module.search_by_cost(message, state, data)

    assert state.data["town"] is True
    assert state.data["cost"] is True


@pytest.mark.asyncio
async def test_list_of_smm_empty_results(methods_module):
    message = FakeMessage(chat_id=999)
    state = FakeState({"ta": ["IT"], "town_search": "Moscow", "cost_search": 1000})

    await methods_module.list_of_smm(message, {}, 0, state)

    message.answer.assert_awaited()
    assert len(state.data) >= 4


@pytest.mark.asyncio
async def test_list_of_smm_non_empty(methods_module, monkeypatch):
    message = FakeMessage(chat_id=999)
    state = FakeState()

    fake_db = SimpleNamespace(
        contacts=SimpleNamespace(is_contact=AsyncMock(return_value=False)),
        smm=SimpleNamespace(
            get_phone_by_user_id=AsyncMock(return_value="+7000"),
            get_tg_by_user_id=AsyncMock(return_value="abc"),
        ),
    )
    monkeypatch.setattr(methods_module, "db", fake_db)

    data = [(10, ("Max", 27, "Moscow", None, 3500, "descr", 10))]
    await methods_module.list_of_smm(message, data, 0, state, fl=False)

    message.answer_photo.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_of_smm_non_empty_edit_media(methods_module, monkeypatch):
    message = FakeMessage(chat_id=999)
    state = FakeState()

    fake_db = SimpleNamespace(
        contacts=SimpleNamespace(is_contact=AsyncMock(return_value=True)),
        smm=SimpleNamespace(
            get_phone_by_user_id=AsyncMock(return_value="+7000"),
            get_tg_by_user_id=AsyncMock(return_value="abc"),
        ),
    )
    monkeypatch.setattr(methods_module, "db", fake_db)

    data = [
        (10, ("Max", 27, "Moscow", None, 3500, "descr", 10)),
        (11, ("Leo", 29, "SPB", None, 4500, "descr2", 11)),
    ]
    await methods_module.list_of_smm(message, data, 1, state, fl=True)

    message.edit_media.assert_awaited_once()


@pytest.mark.asyncio
async def test_sub_end(methods_module, monkeypatch):
    fake_bot = SimpleNamespace(send_message=AsyncMock())
    monkeypatch.setattr(methods_module, "bot", fake_bot)

    await methods_module.sub_end(321)

    fake_bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_iterate_requests_empty(methods_module):
    message = FakeMessage()
    state = FakeState()

    await methods_module.iterate_requests(message, state, [])

    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_iterate_requests_non_empty_edit(methods_module):
    message = FakeMessage()
    state = FakeState()
    reqs = [("Вопрос", 100, "https://t.me/test")]

    await methods_module.iterate_requests(message, state, reqs, i=0, fl=True)

    message.edit_text.assert_awaited_once()
    assert state.data["user_id"] == 100


@pytest.mark.asyncio
async def test_iterate_requests_non_empty_answer(methods_module):
    message = FakeMessage()
    state = FakeState()
    reqs = [
        ("Вопрос1", 100, "https://t.me/test1"),
        ("Вопрос2", 101, "https://t.me/test2"),
    ]

    await methods_module.iterate_requests(message, state, reqs, i=1, fl=False)

    message.answer.assert_awaited_once()
    assert state.data["i"] == 1
