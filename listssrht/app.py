from srht.flask import SrhtFlask, LoginConfig
from srht.config import cfg, cfgi, load_config
load_config("lists")
from srht.database import DbSession
db = DbSession(cfg("sr.ht", "connection-string"))
from listssrht.types import User
db.init()

meta_client_id = cfg("meta.sr.ht", "oauth-client-id")
login_config = LoginConfig(meta_client_id, User)
app = SrhtFlask("lists", __name__, login_config)

app.url_map.strict_slashes = False

from listssrht.blueprints.archives import archives
from listssrht.blueprints.auth import auth
from listssrht.blueprints.user import user

app.register_blueprint(archives)
app.register_blueprint(auth)
app.register_blueprint(user)

def post_address(ml, suffix=""):
    domain = cfg("lists", "posting-domain")
    return "{}/{}{}@{}".format(
            ml.owner.canonical_name(), ml.name, suffix, domain)

@app.context_processor
def inject():
    return {
        "post_address": post_address
    }
