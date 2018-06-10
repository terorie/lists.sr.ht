import sqlalchemy as sa
from srht.database import Base

class List(Base):
    __tablename__ = 'list'
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    name = sa.Column(sa.String(128), nullable=False)

    owner_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    owner = sa.orm.relationship('User', backref=sa.orm.backref('lists'))

    def __repr__(self):
        return '<List {} {}>'.format(self.id, self.name)
