from flask import Blueprint, render_template, abort
from flask_login import current_user
from listssrht.types import List, User, Email
import email
import email.utils

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
    # TODO: pagination
    threads = (Email.query
            .filter(Email.list_id == ml.id)
            .filter(Email.parent_id == None)
        ).order_by(Email.updated.desc()).limit(25).all()
    return render_template("archive.html", owner=owner, ml=ml, threads=threads)

@html.route("/<owner_name>/<list_name>/<message_id>")
def thread(owner_name, list_name, message_id):
    owner, ml = get_list(owner_name, list_name)
    if not ml:
        abort(404)
    thread = (Email.query
            .filter(Email.message_id == message_id)
            .filter(Email.list_id == ml.id)
        ).one_or_none()
    if not thread:
        abort(404)
    envelopes = {
        thread.message_id: email.message_from_string(thread.envelope)
    }
    # Redirect to top-level message if this is a child
    # With the hash set to the child's message ID
    return render_template("thread.html",
            owner=owner,
            ml=ml,
            thread=thread,
            envelopes=envelopes,
            parseaddr=email.utils.parseaddr)
