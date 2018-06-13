from srht.config import cfg, load_config, loaded
is_celery = False
if not loaded():
    load_config("lists")
    is_celery = True
from srht.database import DbSession, db
if is_celery:
    db = DbSession(cfg("sr.ht", "connection-string"))
    import listssrht.types
    db.init()
from listssrht.types import Email, List, User

import email
import io
import json
from celery import Celery
from email.utils import make_msgid 
from unidiff import PatchSet

dispatch = Celery("lists.sr.ht", broker=cfg("lists", "redis"))

def _archive(dest, envelope):
    mail = Email()
    mail.subject = envelope["Subject"]
    mail.message_id = envelope["Message-ID"]
    mail.headers = json.dumps({
        key: value for key, value in envelope.items()
    })
    mail.envelope = str(envelope)
    with io.StringIO(mail.envelope) as f:
        patch = PatchSet(f)
    mail.is_patch = len(patch) > 0
    mail.is_request_pull = False # TODO: Detect git request-pull
    mail.list_id = dest.id
    reply_to = envelope["In-Reply-To"]
    parent = Email.query.filter(Email.message_id == reply_to).one_or_none()
    if parent is not None:
        mail.parent_id = parent.id
    # TODO: Enumerate CC's and create SQL relationships for them
    # TODO: Some users will have many email addresses
    sender = envelope["From"]
    sender = User.query.filter(User.email == sender).one_or_none()
    if sender:
        mail.sender_id = sender.id
    db.session.add(mail)
    db.session.commit()

@dispatch.task
def dispatch_message(list_id, mail):
    mail = email.message_from_string(mail)
    # We need all Message-IDs to be unique so it's better not to trust users
    # MTAs to generate them
    mail["Message-ID"] = make_msgid(domain=cfg("server", "domain"))
    dest = List.query.filter(List.id == list_id).one_or_none()
    _archive(dest, mail)
    # TODO: forward to subscribers
