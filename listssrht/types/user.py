from srht.database import Base
from srht.oauth import ExternalUserMixin
import sqlalchemy as sa
import base64
import os

class User(Base, ExternalUserMixin):
    # TODO: move sessions into core.sr.ht
    session = sa.Column(sa.String(128))

    def __init__(*args, **kwargs):
        ExternalUserMixin.__init__(*args, **kwargs)
