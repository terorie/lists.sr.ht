"""Add fine-grained access control columns

Revision ID: fbbc6b346aee
Revises: None
Create Date: 2018-07-08 09:53:14.216023

"""

# revision identifiers, used by Alembic.
revision = 'fbbc6b346aee'
down_revision = None

from alembic import op
import sqlalchemy as sa
from enum import IntFlag

class ListAccess(IntFlag):
    browse = 1
    reply = 2
    post = 4
    all = browse | reply | post

def upgrade():
    op.drop_column('list', 'allow_nonsubscriber_postings')
    op.drop_column('list', 'allow_external_postings')

    op.add_column('list', sa.Column(
        'nonsubscriber_permissions',
        sa.Integer(), nullable=False, server_default=str(ListAccess.all.value)))
    op.add_column('list', sa.Column(
        'account_permissions',
        sa.Integer(), nullable=False, server_default=str(ListAccess.all.value)))


def downgrade():
    op.drop_column('list', 'nonsubscriber_permissions')
    op.drop_column('list', 'account_permissions')

    op.add_column('list', sa.Column(
        'allow_nonsubscriber_postings',
        sa.Boolean(), nullable=False, server_default='t'))
    op.add_column('list', sa.Column(
        'allow_external_postings',
        sa.Boolean(), nullable=False, server_default='t'))
