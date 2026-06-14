from types import SimpleNamespace

import pytest

from Database.queries.contacts import ContactsQueries
from Database.queries.smm import SmmQueries
from Database.queries.users import UsersQueries


class FakeResult:
    def __init__(self, fetchall_data=None, scalar_data=None, first_data=None, rowcount=0, scalars_data=None, fetchone_data=None, scalar_one_or_none_data=None):
        self._fetchall_data = fetchall_data if fetchall_data is not None else []
        self._scalar_data = scalar_data
        self._first_data = first_data
        self.rowcount = rowcount
        self._scalars_data = scalars_data if scalars_data is not None else []
        self._fetchone_data = fetchone_data
        self._scalar_one_or_none_data = scalar_one_or_none_data

    def fetchall(self):
        return self._fetchall_data

    def scalar(self):
        return self._scalar_data

    def scalar_one_or_none(self):
        return self._scalar_one_or_none_data

    def first(self):
        return self._first_data

    def scalars(self):
        return SimpleNamespace(all=lambda: self._scalars_data)

    def fetchone(self):
        return self._fetchone_data


class FakeSession:
    def __init__(self, execute_results=None, add_raises=False):
        self.execute_results = list(execute_results or [])
        self.add_raises = add_raises
        self.add_calls = 0
        self.commit_calls = 0

    async def execute(self, *args, **kwargs):
        if self.execute_results:
            return self.execute_results.pop(0)
        return FakeResult()

    def add(self, _obj):
        self.add_calls += 1
        if self.add_raises:
            raise RuntimeError("add failed")

    async def commit(self):
        self.commit_calls += 1


class SessionCM:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_query(query_cls, session):
    obj = query_cls.__new__(query_cls)
    obj.db = lambda: SessionCM(session)
    return obj


@pytest.mark.asyncio
async def test_users_add_user_success():
    session = FakeSession()
    q = make_query(UsersQueries, session)

    await q.add_user(1, "name")

    assert session.add_calls == 1
    assert session.commit_calls == 1


@pytest.mark.asyncio
async def test_users_add_user_swallow_exception():
    session = FakeSession(add_raises=True)
    q = make_query(UsersQueries, session)

    await q.add_user(1, "name")

    assert session.add_calls == 1
    assert session.commit_calls == 0


@pytest.mark.asyncio
async def test_users_list_of_users():
    session = FakeSession(execute_results=[FakeResult(fetchall_data=[(1,), (2,)])])
    q = make_query(UsersQueries, session)

    result = await q.lst_of_users()

    assert result == [(1,), (2,)]


@pytest.mark.asyncio
async def test_users_support_flow():
    session = FakeSession(execute_results=[FakeResult(fetchall_data=[("req", 1, "tg")]), FakeResult()])
    q = make_query(UsersQueries, session)

    await q.add_support_request("req", 1, "tg")
    result = await q.get_support_requests()
    await q.answer_request("req", 1)

    assert session.commit_calls == 2
    assert result == [("req", 1, "tg")]


@pytest.mark.asyncio
async def test_users_is_answered_true_and_false():
    session_true = FakeSession(execute_results=[FakeResult(scalar_one_or_none_data=1)])
    q_true = make_query(UsersQueries, session_true)
    assert await q_true.is_answered("req", 1) is True

    session_false = FakeSession(execute_results=[FakeResult(scalar_one_or_none_data=0)])
    q_false = make_query(UsersQueries, session_false)
    assert await q_false.is_answered("req", 1) is False


@pytest.mark.asyncio
async def test_users_purchase_and_created_users():
    created = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    session = FakeSession(
        execute_results=[
            FakeResult(first_data=("payment",)),
            FakeResult(scalars_data=created),
        ]
    )
    q = make_query(UsersQueries, session)

    purchase = await q.get_purchase_by_payment_id("pid")
    users = await q.get_users_created("2026-01-01", "2026-01-02")

    assert purchase == ("payment",)
    assert users == created


@pytest.mark.asyncio
async def test_contacts_add_bought_contact():
    session = FakeSession()
    q = make_query(ContactsQueries, session)

    await q.add_bought_contact(1, 2)

    assert session.add_calls == 1
    assert session.commit_calls == 1


@pytest.mark.asyncio
async def test_contacts_get_bought_contacts(monkeypatch):
    session = FakeSession(execute_results=[FakeResult(fetchall_data=[(10,), (11,)])])
    q = make_query(ContactsQueries, session)

    async def fake_profile(user_id):
        return (user_id, f"name{user_id}")

    monkeypatch.setattr(q, "get_profile_by_id_str", fake_profile)

    result = await q.get_bought_contacts(1)

    assert result[10] == [10, "name10"]
    assert result[11] == [11, "name11"]


@pytest.mark.asyncio
async def test_contacts_get_profile_by_id_str():
    session = FakeSession(execute_results=[FakeResult(fetchone_data=(1, "name"))])
    q = make_query(ContactsQueries, session)

    result = await q.get_profile_by_id_str(1)

    assert result == (1, "name")


@pytest.mark.asyncio
async def test_contacts_is_contact_true_false():
    q_true = make_query(ContactsQueries, FakeSession(execute_results=[FakeResult(scalar_data=1)]))
    q_false = make_query(ContactsQueries, FakeSession(execute_results=[FakeResult(scalar_data=None)]))

    assert await q_true.is_contact(1, 2) is True
    assert await q_false.is_contact(1, 2) is False


@pytest.mark.asyncio
async def test_contacts_remove_contact_true_false():
    q_true = make_query(ContactsQueries, FakeSession(execute_results=[FakeResult(rowcount=1)]))
    q_false = make_query(ContactsQueries, FakeSession(execute_results=[FakeResult(rowcount=0)]))

    assert await q_true.remove_contact(1, 2) is True
    assert await q_false.remove_contact(1, 2) is False


@pytest.mark.asyncio
async def test_smm_add_description_updates_embedding(monkeypatch):
    session = FakeSession()
    q = make_query(SmmQueries, session)

    async def fake_embedding(text):
        assert text == "profile text"
        return [0.1, 0.2, 0.3]

    monkeypatch.setattr("Database.queries.smm.make_embedding_safe", fake_embedding)

    await q.add_description(1, "profile text")

    assert session.commit_calls == 1


@pytest.mark.asyncio
async def test_smm_updt_user_updates_embedding(monkeypatch):
    session = FakeSession()
    q = make_query(SmmQueries, session)

    async def fake_embedding(text):
        assert text == "profile text"
        return [0.4, 0.5]

    monkeypatch.setattr("Database.queries.smm.make_embedding_safe", fake_embedding)

    await q.updt_user(1, "Name", "123", 30, "Town", 50000, "profile text")

    assert session.commit_calls == 1
