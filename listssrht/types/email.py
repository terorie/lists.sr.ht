import email
import io
import sqlalchemy as sa
from email import policy
from srht.database import Base
from unidiff import PatchSet

class Email(Base):
    __tablename__ = 'email'
    id = sa.Column(sa.Integer, primary_key=True)
    created = sa.Column(sa.DateTime, nullable=False)
    updated = sa.Column(sa.DateTime, nullable=False)
    subject = sa.Column(sa.Unicode(512), nullable=False)
    # This will be generated if not present
    message_id = sa.Column(sa.Unicode(512), nullable=False)
    headers = sa.Column(sa.JSON, nullable=False)
    body = sa.Column(sa.Unicode, nullable=False)
    envelope = sa.Column(sa.Unicode, nullable=False)
    is_patch = sa.Column(sa.Boolean, nullable=False)
    """true if email is via git format-patch"""
    is_request_pull = sa.Column(sa.Boolean, nullable=False)
    """true if email is via git request-pull"""

    list_id = sa.Column(sa.Integer, sa.ForeignKey('list.id'))
    list = sa.orm.relationship('List', backref=sa.orm.backref('messages'))

    parent_id = sa.Column(sa.Integer, sa.ForeignKey('email.id'))
    replies = sa.orm.relationship('Email',
            backref=sa.orm.backref('parent',
                remote_side=[id]),
            foreign_keys=[parent_id])

    thread_id = sa.Column(sa.Integer, sa.ForeignKey('email.id'))
    descendants = sa.orm.relationship('Email',
            backref=sa.orm.backref('thread',
                remote_side=[id]),
            foreign_keys=[thread_id])

    nreplies = sa.Column(sa.Integer, server_default='0')
    nparticipants = sa.Column(sa.Integer, server_default='1')

    sender_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'))
    sender = sa.orm.relationship('User',
            backref=sa.orm.backref('sent_messages'))

    # TODO: Enumerate CC's and create a relationship there

    def __repr__(self):
        return '<Email {} {}>'.format(self.id, self.subject)

    def parsed(self):
        if hasattr(self, "_parsed"):
            return self._parsed
        self._parsed = email.message_from_string(
                self.envelope, policy=policy.default)
        return self._parsed

    def patch(self):
        if not self.is_patch:
            return None
        if hasattr(self, "_patch"):
            return self._patch
        with io.StringIO(self.envelope) as f:
            self._patch = PatchSet(f)
        return self._patch
