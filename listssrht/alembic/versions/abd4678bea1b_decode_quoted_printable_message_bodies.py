"""Decode quoted printable message bodies

Revision ID: abd4678bea1b
Revises: 4a6c771785ff
Create Date: 2018-07-24 08:35:51.240552

"""

# revision identifiers, used by Alembic.
revision = 'abd4678bea1b'
down_revision = '4a6c771785ff'

import email
from email import policy
from alembic import op
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as BaseSession, relationship
import sqlalchemy as sa

Session = sessionmaker()
Base = declarative_base()

class Email(Base):
    __tablename__ = 'email'
    id = sa.Column(sa.Integer, primary_key=True)
    body = sa.Column(sa.Unicode, nullable=False)
    envelope = sa.Column(sa.Unicode, nullable=False)

def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    for mail in session.query(Email).all():
        envelope = email.message_from_string(
                mail.envelope, policy=policy.default)
        mail.body = envelope.get_payload(decode=True).decode()
    session.commit()

def downgrade():
    pass
