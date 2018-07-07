from flask import render_template, request
from flask_login import LoginManager, current_user
from jinja2 import Markup
from datetime import datetime, timedelta
import locale
import urllib

from srht.config import cfg, cfgi, load_config
load_config("lists")
from srht.database import DbSession
db = DbSession(cfg("sr.ht", "connection-string"))
from listssrht.types import User
db.init()

from srht.flask import SrhtFlask
app = SrhtFlask("lists", __name__)
app.url_map.strict_slashes = False
app.secret_key = cfg("server", "secret-key")
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(username):
    return User.query.filter(User.username == username).one_or_none()

login_manager.anonymous_user = lambda: None

try:
    locale.setlocale(locale.LC_ALL, 'en_US')
except:
    pass

def oauth_url(return_to):
    return "{}/oauth/authorize?client_id={}&scopes=profile&state={}".format(
        meta_sr_ht, meta_client_id, urllib.parse.quote_plus(return_to))

from listssrht.blueprints.auth import auth
from listssrht.blueprints.html import html

app.register_blueprint(auth)
app.register_blueprint(html)

meta_sr_ht = cfg("network", "meta")
meta_client_id = cfg("meta.sr.ht", "oauth-client-id")

def post_address(ml, suffix=""):
    domain = cfg("lists", "posting-domain")
    return "{}/{}{}@{}".format(
            ml.owner.canonical_name(), ml.name, suffix, domain)

@app.context_processor
def inject():
    return {
        "test": datetime.utcnow() + timedelta(minutes=-5),
        "oauth_url": oauth_url(request.full_path),
        "current_user": (User.query
                .filter(User.id == current_user.id).one_or_none()
            if current_user else None),
        "post_address": post_address
    }
