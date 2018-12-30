from listssrht.filters import diffstat, format_body, post_address
from listssrht.oauth import ListsOAuthService
from srht.config import cfg
from srht.database import DbSession
from srht.flask import SrhtFlask
from urllib.parse import quote

db = DbSession(cfg("lists.sr.ht", "connection-string"))
db.init()

class ListsApp(SrhtFlask):
    def __init__(self):
        super().__init__("lists.sr.ht", __name__,
                oauth_service=ListsOAuthService())

        self.url_map.strict_slashes = False

        from listssrht.blueprints.archives import archives
        from listssrht.blueprints.user import user

        self.register_blueprint(archives)
        self.register_blueprint(user)

        @self.context_processor
        def inject():
            return {
                "diffstat": diffstat,
                "format_body": format_body,
                "post_address": post_address,
                "quote": quote,
            }

app = ListsApp()
