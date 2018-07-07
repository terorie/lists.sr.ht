from srht.config import cfg, cfgi, load_config, loaded
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
import smtplib
from celery import Celery
from email import policy
from email.utils import make_msgid 
from unidiff import PatchSet

dispatch = Celery("lists.sr.ht", broker=cfg("lists", "redis"))

smtp_host = cfg("mail", "smtp-host", default=None)
smtp_port = cfgi("mail", "smtp-port", default=None)
smtp_user = cfg("mail", "smtp-user", default=None)
smtp_password = cfg("mail", "smtp-password", default=None)

def _forward(dest, mail):
    domain = cfg("lists", "posting-domain")
    list_name = "{}/{}".format(dest.owner.canonical_name(), dest.name)
    list_unsubscribe = list_name + "+unsubscribe@" + domain
    list_subscribe = list_name + "+subscribe@" + domain
    mail["List-Unsubscribe"] = (
            "<mailto:{}?subject=unsubscribe>".format(list_unsubscribe))
    mail["List-Subscribe"] = (
            "<mailto:{}?subject=subscribe>".format(list_subscribe))
    mail["List-Archive"] = "<{}://{}/{}>".format(
            cfg("server", "protocol"), cfg("server", "domain"), list_name)
    mail["List-Post"] = "<mailto:{}@{}>".format(list_name, domain)
    mail["Sender"] = "{} <{}@{}>".format(list_name, list_name, domain)
    # TODO: Encrypt emails
    smtp = smtplib.SMTP(smtp_host, smtp_port)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(smtp_user, smtp_password)
    for sub in dest.subscribers:
        if not sub.confirmed:
            continue
        to = sub.email
        if sub.user:
            to = sub.user.email
        print("Forwarding message to " + to)
        smtp.sendmail(smtp_user, [to], mail.as_string(unixfrom=True))
    smtp.quit()

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
    mail.body = envelope.get_content()
    reply_to = envelope["In-Reply-To"]
    parent = Email.query.filter(Email.message_id == reply_to).one_or_none()
    if parent is not None:
        mail.parent_id = parent.id
        thread = parent
        tenvelope = email.message_from_string(thread.envelope)
        participants = set([envelope["From"], tenvelope["From"]])
        while thread.parent_id != None:
            tenvelope = email.message_from_string(thread.envelope)
            participants.update([tenvelope["From"]])
            thread = thread.parent
        mail.thread_id = thread.id
        thread.nreplies += 1
        thread.nparticipants = len(participants)
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
    mail = email.message_from_string(mail, policy=policy.default)
    msgid = mail["Message-ID"]
    if Email.query.filter(Email.message_id == msgid).count() > 0:
        print("Dropping email due to duplicate message ID")
        return
    dest = List.query.filter(List.id == list_id).one_or_none()
    _archive(dest, mail)
    _forward(dest, mail)
