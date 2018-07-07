from flask import Blueprint, render_template, abort, request, redirect, url_for
from flask_login import current_user
from srht.flask import paginate_query
from listssrht.types import List, User, Email, Subscription
from sqlalchemy import or_
import email
import email.utils

archives = Blueprint("archives", __name__)

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
            Email.body.ilike("%" + value + "%"),
            Email.subject.ilike("%" + value + "%")))
    return query, search

@archives.route("/<owner_name>/<list_name>")
def list(owner_name, list_name):
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

@archives.route("/<owner_name>/<list_name>/<message_id>")
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
    if thread.thread_id != None:
        return redirect(url_for("archives.thread",
            owner_name=owner_name,
            list_name=list_name,
            message_id=thread.thread.message_id) + "#" + thread.message_id)
    return render_template("thread.html",
            owner=owner,
            ml=ml,
            thread=thread,
            parseaddr=email.utils.parseaddr)
