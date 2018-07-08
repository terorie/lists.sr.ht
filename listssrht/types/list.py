from srht.flagtype import FlagType
from srht.database import Base
from listssrht.types.listaccess import ListAccess
import sqlalchemy as sa

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

    subscriber_permissions = sa.Column(FlagType(ListAccess),
            nullable=False, server_default=str(ListAccess.all.value))
    """
    Permissions granted to users who are subscribed to the list.
    """

    account_permissions = sa.Column(FlagType(ListAccess),
            nullable=False, server_default=str(ListAccess.all.value))
    """
    Permissions granted to holders of sr.ht accounts.
    """

    owner_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    owner = sa.orm.relationship('User', backref=sa.orm.backref('lists'))

    def __repr__(self):
        return '<List {} {}>'.format(self.id, self.name)
