"""Add user mixin properties

Revision ID: 07257ddd8bb7
Revises: 4c0b015574ef
Create Date: 2018-12-30 15:32:35.051730

"""

# revision identifiers, used by Alembic.
revision = '07257ddd8bb7'
down_revision = '4c0b015574ef'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("user", sa.Column("url", sa.String(256)))
    op.add_column("user", sa.Column("location", sa.Unicode(256)))
    op.add_column("user", sa.Column("bio", sa.Unicode(4096)))


def downgrade():
    op.delete_column("user", "url")
    op.delete_column("user", "location")
    op.delete_column("user", "bio")
