import sqlalchemy as sa
from srht.database import Base

class Email(Base):
    __tablename__ = 'email'
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    subject = sa.Column(sa.Unicode(512), nullable=False)
    # This will be generated if not present
    message_id = sa.Column(sa.Unicode(512), nullable=False)
    headers = sa.Column(sa.Unicode, nullable=False)
    envelope = sa.Column(sa.Unicode, nullable=False)
    is_patch = sa.Column(sa.Boolean, nullable=False)
    """true if email is via git format-patch"""
    is_request_pull = sa.Column(sa.Boolean, nullable=False)
    """true if email is via git request-pull"""

    list_id = sa.Column(sa.Integer, sa.ForeignKey('list.id'))
    list = sa.orm.relationship('List', backref=sa.orm.backref('messages'))

    parent_id = sa.Column(sa.Integer, sa.ForeignKey('email.id'))
    parent = sa.orm.relationship('Email', backref=sa.orm.backref('replies'))

    from_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    from = sa.orm.relationship('User', backref=sa.orm.backref('sent_messages'))

    to_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    to = sa.orm.relationship('User', backref=sa.orm.backref('received_messages'))

    # TODO: Enumerate CC's and create a relationship there

    def __repr__(self):
        return '<Email {} {}>'.format(self.id, self.subject)
