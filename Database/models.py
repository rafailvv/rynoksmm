from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Identity, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Promocodes(Base):
    __tablename__ = 'promocodes'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    promo = Column(Text, nullable=False)
    usage = Column(Integer, nullable=False)
    users = Column(Text, nullable=False)
    duration = Column(Integer, nullable=False)
    text_ = Column('text', Text, nullable=False)


class Support(Base):
    __tablename__ = 'support'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    request = Column(Text)
    user_id = Column(BigInteger)
    answered = Column(Integer)
    tg_url = Column(Text)


class TargetAudience(Base):
    __tablename__ = 'target_audience'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    name = Column(Text, nullable=False)
    category = Column(Text)

    subscribe_notifications = relationship('SubscribeNotifications', back_populates='target_audience')
    target_audience_smm = relationship('TargetAudienceSmm', back_populates='target_audience')


class Users(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(Text)

    payments = relationship('Payments', back_populates='user')
    smm = relationship('Smm', uselist=False, back_populates='user')
    contacts = relationship('Contacts', back_populates='user')


class Payments(Base):
    __tablename__ = 'payments'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    finish_time = Column(DateTime, nullable=False)
    cost = Column(BigInteger, nullable=False)
    payment_id = Column(UUID)

    user = relationship('Users', back_populates='payments')


class Smm(Base):
    __tablename__ = 'smm'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False, unique=True)
    full_name = Column(Text)
    phone = Column(Text)
    age = Column(Integer)
    town = Column(Text)
    cost = Column(Integer)
    photo = Column(Text)
    free_sub = Column(Integer, server_default=text('0'))
    description = Column(Text)
    date_sub = Column(DateTime)
    promos = Column(Text)

    user = relationship('Users', back_populates='smm')
    cases = relationship('Cases', back_populates='smm')
    contacts = relationship('Contacts', back_populates='smm')


class SubscribeNotifications(Base):
    __tablename__ = 'subscribe_notifications'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    ta = Column(ForeignKey('target_audience.id'))
    town = Column(Text)
    cost = Column(Integer)
    user_id = Column(BigInteger)

    target_audience = relationship('TargetAudience', back_populates='subscribe_notifications')


class TargetAudienceSmm(Base):
    __tablename__ = 'target_audience_smm'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    smm_id = Column(BigInteger, nullable=False)
    target_audience_id = Column(ForeignKey('target_audience.id'), nullable=False)

    target_audience = relationship('TargetAudience', back_populates='target_audience_smm')


class Cases(Base):
    __tablename__ = 'cases'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    smm_id = Column(ForeignKey('smm.id'), nullable=False)
    name = Column(Text, nullable=False)
    link = Column(Text, nullable=False)

    smm = relationship('Smm', back_populates='cases')


class Contacts(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    smm_id = Column(ForeignKey('smm.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    smm = relationship('Smm', back_populates='contacts')
    user = relationship('Users', back_populates='contacts')
