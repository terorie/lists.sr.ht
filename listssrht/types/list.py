import sqlalchemy as sa
from srht.database import Base

class List(Base):
    __tablename__ = 'list'
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    name = sa.Column(sa.String(128), nullable=False)
    description = sa.Column(sa.Unicode(2048))

    allow_nonsubscriber_postings = sa.Column(sa.Boolean,
            nullable=False,
            server_default='true')
    """
    When true, allow postings to this mailing list from senders who are not
    subscribed to the list.
    """
    allow_external_postings = sa.Column(sa.Boolean,
            nullable=False,
            server_default='true')
    """
    When true, allow postings to this mailing list from senders who do not have
    sr.ht accounts.
    """

    owner_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    owner = sa.orm.relationship('User', backref=sa.orm.backref('lists'))

    def __repr__(self):
        return '<List {} {}>'.format(self.id, self.name)
