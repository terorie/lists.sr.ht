"""Drop confirmed column from subscription

Revision ID: 9d264a430403
Revises: fbbc6b346aee
Create Date: 2018-07-08 13:59:05.762759

"""

# revision identifiers, used by Alembic.
revision = '9d264a430403'
down_revision = 'fbbc6b346aee'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('subscription', 'confirmed')


def downgrade():
    op.add_column('subscription', sa.Column('confirmed',
        sa.Boolean(), nullable=False))
