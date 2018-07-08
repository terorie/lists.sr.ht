"""Add subscribed user permissions

Revision ID: 4a6c771785ff
Revises: 9d264a430403
Create Date: 2018-07-08 14:10:36.638296

"""

# revision identifiers, used by Alembic.
revision = '4a6c771785ff'
down_revision = '9d264a430403'

from alembic import op
import sqlalchemy as sa
from enum import IntFlag

class ListAccess(IntFlag):
    browse = 1
    reply = 2
    post = 4
    all = browse | reply | post


def upgrade():
    op.add_column('list', sa.Column(
        'subscriber_permissions',
        sa.Integer(), nullable=False, server_default=str(ListAccess.all.value)))


def downgrade():
    op.drop_column('list', 'subscriber_permissions')
