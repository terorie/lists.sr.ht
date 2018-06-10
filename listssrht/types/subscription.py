import sqlalchemy as sa
from srht.database import Base

class Subscription(Base):
    __tablename__ = 'subscription'
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    email = sa.Column(sa.Unicode(512), nullable=False)
    confirmed = sa.Column(sa.Boolean, nullable=False)

    list_id = sa.Column(sa.Integer, sa.ForeignKey('list.id'))
    list = sa.orm.relationship('List', backref=sa.orm.backref('subscribers'))

    # Non-users can subscribe, so this might be null
    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    user = sa.orm.relationship('User', backref=sa.orm.backref('subscriptions'))

    def __repr__(self):
        return '<Subscription {} {} -> list {}>'.format(
                self.id, self.email, self.list_id)
