from srht.config import cfg
from srht.oauth import AbstractOAuthService
from listssrht.types import User

client_id = cfg("lists.sr.ht", "oauth-client-id")
client_secret = cfg("lists.sr.ht", "oauth-client-secret")

class ListsOAuthService(AbstractOAuthService):
    def __init__(self):
        super().__init__(client_id, client_secret, user_class=User)
