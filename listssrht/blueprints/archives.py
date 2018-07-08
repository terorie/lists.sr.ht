from flask import Blueprint, render_template, abort, request, redirect, url_for
from flask_login import current_user
from srht.database import db
from srht.flask import paginate_query, loginrequired
from srht.validation import Validation
from listssrht.types import List, User, Email, Subscription, ListAccess
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

    subscription = None
    if current_user:
        subscription = (Subscription.query
                .filter(Subscription.list_id == ml.id)
                .filter(Subscription.user_id == current_user.id)).one_or_none()

    return render_template("archive.html",
            owner=owner, ml=ml, threads=threads,
            search=search, subscription=subscription, **pagination)

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

@loginrequired
@archives.route("/<owner_name>/<list_name>/subscribe", methods=["POST"])
def subscribe(owner_name, list_name):
    owner, ml = get_list(owner_name, list_name)
    if not ml:
        abort(404)
    sub = (Subscription.query
        .filter(Subscription.list_id == ml.id)
        .filter(Subscription.user_id == current_user.id)).one_or_none()
    if sub:
        return redirect(url_for("archives.list",
            owner_name=owner_name, list_name=list_name))
    sub = Subscription()
    sub.user_id = current_user.id
    sub.list_id = ml.id
    db.session.add(sub)
    db.session.commit()
    return redirect(url_for("archives.list",
        owner_name=owner_name, list_name=list_name))

@loginrequired
@archives.route("/<owner_name>/<list_name>/unsubscribe", methods=["POST"])
def unsubscribe(owner_name, list_name):
    owner, ml = get_list(owner_name, list_name)
    if not ml:
        abort(404)
    sub = (Subscription.query
        .filter(Subscription.list_id == ml.id)
        .filter(Subscription.user_id == current_user.id)).one_or_none()
    if sub:
        db.session.delete(sub)
        db.session.commit()
    return redirect(url_for("archives.list",
        owner_name=owner_name, list_name=list_name))

access_help_map = {
    ListAccess.browse:
        "Permission to subscribe and browse the archives",
    ListAccess.reply:
        "Permission to reply to threads submitted by an authorized user.",
    ListAccess.post:
        "Permission to submit new threads."
}

@loginrequired
@archives.route("/<owner_name>/<list_name>/settings")
def settings_GET(owner_name, list_name):
    owner, ml = get_list(owner_name, list_name)
    if not ml:
        abort(404)
    if ml.owner_id != current_user.id:
        abort(401)
    return render_template("list-settings.html", list=ml, owner=owner,
            access_type_list=ListAccess, access_help_map=access_help_map)

@loginrequired
@archives.route("/<owner_name>/<list_name>/settings", methods=["POST"])
def settings_POST(owner_name, list_name):
    owner, ml = get_list(owner_name, list_name)
    if not ml:
        abort(404)
    if ml.owner_id != current_user.id:
        abort(401)

    valid = Validation(request)
    list_desc = valid.optional("list_desc")
    if list_desc == "":
        list_desc = None
    valid.expect(not list_desc or 16 < len(list_desc) < 2048,
            "Description must be between 16 and 2048 characters.",
            field="list_desc")

    if not valid.ok:
        return render_template("list-settings.html", list=ml, owner=owner,
                access_type_list=ListAccess, access_help_map=access_help_map,
                **valid.kwargs)

    def process(perm):
        bitfield = ListAccess.none
        for access in ListAccess:
            if access in [ListAccess.none]:
                continue
            if valid.optional("perm_{}_{}".format(
                    perm, access.name)) != None:
                bitfield |= access
        return bitfield

    ml.description = list_desc
    ml.nonsubscriber_permissions = process("nonsub")
    ml.account_permissions = process("account")

    db.session.commit()

    return redirect(url_for("archives.list",
        owner_name=owner_name, list_name=list_name))
