from srht.flask import SrhtFlask
from srht.config import cfg, load_config
load_config("lists")
from urllib.parse import quote

from srht.database import DbSession
db = DbSession(cfg("sr.ht", "connection-string"))

from listssrht.types import User
db.init()

from listssrht.blueprints.archives import archives
from listssrht.blueprints.user import user

def _post_address(ml, suffix=""):
    domain = cfg("lists", "posting-domain")
    return "{}/{}{}@{}".format(
            ml.owner.canonical_name(), ml.name, suffix, domain)

class LoginApp(SrhtFlask):
    def __init__(self):
        super().__init__("lists", __name__)

        self.url_map.strict_slashes = False

        self.register_blueprint(archives)
        self.register_blueprint(user)

        meta_client_id = cfg("meta.sr.ht", "oauth-client-id")
        meta_client_secret = cfg("meta.sr.ht", "oauth-client-secret")
        self.configure_meta_auth(meta_client_id, meta_client_secret)

        @self.context_processor
        def inject():
            return {
                "post_address": _post_address,
                "quote": quote,
            }

        @self.login_manager.user_loader
        def user_loader(session):
            return User.query.filter(User.session == session).one_or_none()

    def lookup_or_register(self, exchange, profile, scopes):
        user = User.query.filter(User.username == profile["username"]).first()
        if not user:
            user = User()
            db.session.add(user)
        user.username = profile.get("username")
        user.email = profile.get("email")
        user.admin = profile.get("admin")
        user.oauth_token = exchange["token"]
        user.oauth_token_expires = exchange["expires"]
        user.oauth_token_scopes = scopes
        user.generate_session()
        db.session.commit()
        return user

app = LoginApp()
