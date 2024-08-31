from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Identity, Integer, Text, text

from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TargetAudience(Base):
    __tablename__ = 'target_audience'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    name = Column(Text, nullable=False)
    category = Column(Text)

    target_audience_smm = relationship('TargetAudienceSmm', back_populates='target_audience')


class Users(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(Text)

    contacts = relationship('Contacts', foreign_keys=['Contacts.smm_id'], back_populates='smm')
    contacts_ = relationship('Contacts', foreign_keys=['Contacts.user_id'], back_populates='user')
    payments = relationship('Payments', back_populates='user')
    smm = relationship('Smm', uselist=False, back_populates='user')


class Contacts(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    smm_id = Column(ForeignKey('users.id'), nullable=False)

    smm = relationship('Users', foreign_keys=[smm_id], back_populates='contacts')
    user = relationship('Users', foreign_keys=[user_id], back_populates='contacts_')


class Payments(Base):
    __tablename__ = 'payments'

    id = Column(Integer, Identity(start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), primary_key=True)
    user_id = Column(ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    finish_time = Column(DateTime, nullable=False)
    cost = Column(Integer, nullable=False)

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

    user = relationship('Users', back_populates='smm')
    cases = relationship('Cases', back_populates='smm')


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
