from enum import IntFlag
from srht.database import Base
from srht.flagtype import FlagType
import sqlalchemy as sa

class ListAccess(IntFlag):
    """
    Permissions granted to users of a list.
    """
    none = 0
    """Grant no access to this list."""
    browse = 1
    """Permission to subscribe and browse the archives"""
    reply = 2
    """Permission to reply to threads submitted by an authorized user."""
    post = 3
    """Permission to submit new threads."""
    all = browse | reply | post

class List(Base):
    __tablename__ = 'list'
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    name = sa.Column(sa.String(128), nullable=False)
    description = sa.Column(sa.Unicode(2048))

    nonsubscriber_permissions = sa.Column(FlagType(ListAccess),
            nullable=False, server_default=str(ListAccess.all.value))
    """
    Permissions granted to users who are not subscribed or logged in.
    """

    account_permissions = sa.Column(FlagType(ListAccess),
            nullable=False, server_default=str(ListAccess.all.value))
    """
    Permissions granted to logged in holders of sr.ht accounts.
    """

    owner_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    owner = sa.orm.relationship('User', backref=sa.orm.backref('lists'))

    def __repr__(self):
        return '<List {} {}>'.format(self.id, self.name)
