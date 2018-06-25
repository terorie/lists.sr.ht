from flask import Blueprint, render_template, abort
from flask_login import current_user
from listssrht.types import List, User

html = Blueprint("html", __name__)

@html.route("/")
def index():
    if current_user is None:
        return render_template("index.html")
    return render_template("dashboard.html")

def get_list(owner_name, list_name):
    if owner_name and owner_name.startswith('~'):
        owner_name = owner_name[1:]
        owner = User.query.filter(User.username == owner_name).one_or_none()
        if not owner:
            return None, None
    else:
        # TODO: orgs
        return None, None
    ml = List.query.filter(List.name == list_name).one_or_none()
    return owner, ml

@html.route("/<owner_name>/<list_name>")
def archives(owner_name, list_name):
    owner, ml = get_list(owner_name, list_name)
    if not ml:
        abort(404)
    return render_template("archive.html", owner=owner, ml=ml)
