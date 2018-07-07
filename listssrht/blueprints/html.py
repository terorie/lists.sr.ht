from flask import Blueprint, render_template, abort, request
from flask_login import current_user
from srht.flask import paginate_query
from listssrht.types import List, User, Email, Subscription
from sqlalchemy import or_
import email
import email.utils

html = Blueprint("html", __name__)

@html.route("/")
def index():
    if current_user is None:
        return redirect(cfg("network", "meta"))
    # TODO: This query is probably gonna get pretty expensive
    recent = (Email.query
            .join(List)
            .join(Subscription)
            .filter(Email.list_id == List.id)
            .filter(Subscription.list_id == List.id)
            .filter(Subscription.user_id == current_user.id)
            .order_by(Email.created.desc())).limit(10).all()
    return render_template("dashboard.html", recent=recent)

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

def apply_search(query):
    search = request.args.get("search")
    if not search:
        return query, None
    terms = search.split(" ")
    for term in terms:
        term = term.lower()
        if ":" in term:
            prop, value = term.split(":")
        else:
            prop, value = None, term
        # TODO: Custom search critiera
        query = query.filter(or_(
            Email.envelope.ilike("%" + value + "%"),
            Email.subject.ilike("%" + value + "%")))
    return query, search

@html.route("/<owner_name>/<list_name>")
def archives(owner_name, list_name):
    owner, ml = get_list(owner_name, list_name)
    if not ml:
        abort(404)
    threads = (Email.query
            .filter(Email.list_id == ml.id)
            .filter(Email.parent_id == None)
        ).order_by(Email.updated.desc())
    threads, search = apply_search(threads)
    threads, pagination = paginate_query(threads)
    return render_template("archive.html",
            owner=owner, ml=ml, threads=threads,
            search=search, **pagination)

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
        m.message_id: email.message_from_string(m.envelope)
            for m in [thread] + thread.descendants
    }
    # Redirect to top-level message if this is a child
    # With the hash set to the child's message ID
    return render_template("thread.html",
            owner=owner,
            ml=ml,
            thread=thread,
            envelopes=envelopes,
            parseaddr=email.utils.parseaddr)
