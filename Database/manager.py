from Database.queries.users import UsersQueries
from Database.queries.ta import TaQueries
from Database.queries.smm import SmmQueries
from Database.queries.contacts import ContactsQueries
from Bot.config import config


class Database:
    users = UsersQueries(config)
    ta = TaQueries(config)
    smm = SmmQueries(config)
    contacts = ContactsQueries(config)


db = Database()