from srht.database import Base
from srht.oauth import ExternalUserMixin
import sqlalchemy as sa

class User(Base, ExternalUserMixin):
    # TODO: move sessions into core.sr.ht
    session = sa.Column(sa.String(128))
