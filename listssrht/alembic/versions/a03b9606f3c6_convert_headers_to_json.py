"""Convert headers to JSON

Revision ID: a03b9606f3c6
Revises: 07257ddd8bb7
Create Date: 2019-02-05 09:43:21.358237

"""

# revision identifiers, used by Alembic.
revision = 'a03b9606f3c6'
down_revision = '07257ddd8bb7'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as BaseSession, relationship
import json

Session = sessionmaker()
Base = declarative_base()

class Email(Base):
    __tablename__ = 'email'
    id = sa.Column(sa.Integer, primary_key=True)
    headers = sa.Column(sa.JSON, nullable=False)

def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    for email in session.query(Email).all():
        headers = json.loads(email.headers)
        email.headers = headers
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    for email in session.query(Email).all():
        headers = json.dumps(email.headers)
        email.headers = headers
    session.commit()
