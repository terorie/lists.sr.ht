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
from listssrht.types import Email, List, User, Subscription

import email
import email.utils
import io
import json
import smtplib
from celery import Celery
from email import policy
from email.mime.text import MIMEText
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
    mail.body = envelope.get_payload()
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
    sender = email.utils.parseaddr(envelope["From"])
    sender = User.query.filter(User.email == sender[1]).one_or_none()
    if sender:
        mail.sender_id = sender.id
    db.session.add(mail)
    db.session.commit()

def _subscribe(dest, mail):
    sender = email.utils.parseaddr(mail["From"])
    user = User.query.filter(User.email == sender[1]).one_or_none()
    if user:
        sub = Subscription.query.filter(
            Subscription.user_id == user.id).one_or_none()
    else:
        sub = Subscription.query.filter(
            Subscription.email == sender[1]).one_or_none()
    list_addr = dest.owner.canonical_name() + "/" + dest.name
    message = None
    if sub is None:
        reply = MIMEText("""Hi {}!

Your subscription to {} is confirmed! To unsubscribe in the future, send an
email to this address:

{}+unsubscribe@{}

Feel free to reply to this email if you have any questions.""".format(
                sender[0] or sender[1], list_addr, list_addr,
                cfg("lists", "posting-domain")))
        sub = Subscription()
        sub.user_id = user.id if user else None
        sub.email = sender[1] if not user else None
        db.session.add(sub)
    else:
        reply = MIMEText("""Hi {}!
        
We got an email asking to subscribe you to the {} mailing list. However, it
looks like you're already subscribed. To unsubscribe, send an email to:

{}+unsubscribe@{}

Feel free to reply to this email if you have any questions.""".format(
                sender[0] or sender[1], list_addr, list_addr,
                cfg("lists", "posting-domain")))
    reply["To"] = mail["From"]
    reply["From"] = "mailer@" + cfg("lists", "posting-domain")
    reply["In-Reply-To"] = mail["Message-ID"]
    reply["Subject"] = "Re: " + (
            mail.get("Subject") or "Your subscription request")
    reply["Reply-To"] = "{} <{}>".format(
            cfg("sr.ht", "owner-name"), cfg("sr.ht", "owner-email"))
    print(reply.as_string(unixfrom=True))
    smtp = smtplib.SMTP(smtp_host, smtp_port)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(smtp_user, smtp_password)
    smtp.sendmail(smtp_user, [sender[1]], reply.as_string(unixfrom=True))
    smtp.quit()
    db.session.commit()

def _unsubscribe(dest, mail):
    sender = email.utils.parseaddr(mail["From"])
    user = User.query.filter(User.email == sender[1]).one_or_none()
    if user:
        sub = Subscription.query.filter(
            Subscription.user_id == user.id).one_or_none()
    else:
        sub = Subscription.query.filter(
            Subscription.email == sender[1]).one_or_none()
    list_addr = dest.owner.canonical_name() + "/" + dest.name
    message = None
    if sub is None:
        reply = MIMEText("""Hi {}!

We got your request to unsubscribe from {}, but we did not find a subscription
from your email. If you continue to receive undesirable emails from this list,
please reply to this email for support.""".format(
                sender[0] or sender[1], list_addr))
    else:
        db.session.delete(sub)
        reply = MIMEText("""Hi {}!
        
You have been successfully unsubscribed from the {} mailing list. If you wish to
re-subscribe, send an email to:

{}+subscribe@{}

Feel free to reply to this email if you have any questions.""".format(
                sender[0] or sender[1], list_addr, list_addr,
                cfg("lists", "posting-domain")))
    reply["To"] = mail["From"]
    reply["From"] = "mailer@" + cfg("lists", "posting-domain")
    reply["In-Reply-To"] = mail["Message-ID"]
    reply["Subject"] = "Re: " + (
            mail.get("Subject") or "Your subscription request")
    reply["Reply-To"] = "{} <{}>".format(
            cfg("sr.ht", "owner-name"), cfg("sr.ht", "owner-email"))
    print(reply.as_string(unixfrom=True))
    smtp = smtplib.SMTP(smtp_host, smtp_port)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(smtp_user, smtp_password)
    smtp.sendmail(smtp_user, [sender[1]], reply.as_string(unixfrom=True))
    smtp.quit()
    db.session.commit()

@dispatch.task
def dispatch_message(address, list_id, mail):
    address = address[:address.rfind("@")]
    command = "post"
    if "+" in address:
        command = address[address.rfind("+") + 1:].lower()
        address = address[:address.rfind("+")]
    dest = List.query.filter(List.id == list_id).one_or_none()
    mail = email.message_from_string(mail, policy=policy.default)

    if command == "post":
        msgid = mail.get("Message-ID")
        if not msgid or Email.query.filter(Email.message_id == msgid).count():
            print("Dropping email due to duplicate message ID")
            return
        _archive(dest, mail)
        _forward(dest, mail)
    elif command == "subscribe":
        _subscribe(dest, mail)
    elif command == "unsubscribe":
        _unsubscribe(dest, mail)
