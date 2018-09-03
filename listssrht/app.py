from srht.flask import SrhtFlask
from srht.config import cfg
from srht.database import DbSession

db = DbSession(cfg("lists.sr.ht", "connection-string"))

from listssrht.types import User

db.init()

from jinja2 import Markup, escape
from urllib.parse import quote

def _post_address(ml, suffix=""):
    domain = cfg("lists.sr.ht", "posting-domain")
    return "{}/{}{}@{}".format(
            ml.owner.canonical_name(), ml.name, suffix, domain)

def _format_patch(msg, limit=None):
    text = Markup("")
    is_diff = False

    # Predict the starting lines of each file name
    patch = msg.patch()
    file_lines = {
        " {} ".format(f.path): f
        for f in patch.added_files + patch.modified_files + patch.removed_files
    }

    line_no = 0
    for line in msg.body.replace("\r", "").split("\n"):
        line_no += 1
        if line_no == limit:
            text = text.rstrip()
            text += Markup(
                "\n<span class='text-muted'>[message trimmed]</span>"
            )
            break
        if not is_diff:
            f = next((
                key for key in file_lines.keys() if line.startswith(key)
            ), None)
            if f != None:
                f = file_lines[f]
                text += Markup(" <a href='#{}'>{}</a>".format(
                    escape(msg.message_id) + "+" + escape(f.path),
                    escape(f.path)))
                try:
                    stat = line[line.rindex(" ") + 1:]
                    line = line[:line.rindex(" ") + 1]
                    if "+" in stat and "-" in stat:
                        removed = stat[stat.index("-"):]
                        added = stat[:stat.index("-")]
                        stat = Markup(("<span class='text-success'>{}</span>" +
                            "<span class='text-danger'>{}</span>"
                        ).format(escape(added), escape(removed)))
                    elif "-" in stat:
                        stat = Markup(
                                "<span class='text-danger'>{}</span>".format(
                                    escape(stat)))
                    elif "+" in stat:
                        stat = Markup(
                                "<span class='text-success'>{}</span>".format(
                                    escape(stat)))
                    else:
                        stat = escape(stat)
                except ValueError:
                    stat = Markup("")
                text += escape(line[len(f.path) + 1:])
                text += escape(stat)
                text += Markup("\n")
            else:
                text += escape(line + "\n")
            if line.startswith("diff"):
                is_diff = True
        else:
            if line.strip() == "--":
                text += escape(line + "\n")
            elif line.startswith("---"):
                path = line[4:].lstrip("a/")
                text += (
                    Markup("<a href='#{0}' id='{0}' class='text-info'>".format(
                        escape(msg.message_id) + "+" + escape(path)
                    ))
                    + escape(line)
                    + Markup("</a>\n"))
            elif line.startswith("+++"):
                text += (
                    Markup("<span class='text-info'>")
                    + escape(line)
                    + Markup("</span>\n"))
            elif line.startswith("+"):
                text += (
                    Markup("<span class='text-success'>")
                    + Markup(
                        "<a class='text-success' href='#{0}-{1}' " +
                        "id='{0}-{1}'>+</a>".format(
                            escape(msg.message_id), line_no))
                    + escape(line[1:])
                    + Markup("</span>\n"))
            elif line.startswith("-"):
                text += (
                    Markup("<span class='text-danger'>")
                    + Markup(
                        "<a class='text-danger' href='#{0}-{1}' " +
                        "id='{0}-{1}'>-</a>".format(
                            escape(msg.message_id), line_no))
                    + escape(line[1:])
                    + Markup("</span>\n"))
            elif line.startswith(" "):
                text += (
                    Markup("<a href='#{0}-{1}' id='{0}-{1}'> </a>".format(
                            escape(msg.message_id), line_no))
                    + escape(line[1:] + "\n"))
            else:
                text += escape(line + "\n")
    return text.rstrip()

def _format_body(msg, limit=None):
    if msg.is_patch:
        return _format_patch(msg, limit)
    text = Markup("")
    line_no = 0
    for line in msg.body.replace("\r", "").split("\n"):
        line_no += 1
        if line_no == limit:
            break
        if line.startswith(">"):
            text += (
                Markup("<span class='text-muted'>")
                    + escape(line)
                + Markup("</span>\n"))
        else:
            text += escape(line + "\n")
    return text.rstrip()

def _diffstat(patch):
    p = patch.patch()
    return type("diffstat", tuple(), {
        "added": sum(f.added for f in p.added_files + p.modified_files),
        "removed": sum(f.removed for f in p.removed_files + p.modified_files),
    })

class LoginApp(SrhtFlask):
    def __init__(self):
        super().__init__("lists.sr.ht", __name__)

        self.url_map.strict_slashes = False

        from listssrht.blueprints.archives import archives
        from listssrht.blueprints.user import user

        self.register_blueprint(archives)
        self.register_blueprint(user)

        meta_client_id = cfg("lists.sr.ht", "oauth-client-id")
        meta_client_secret = cfg("lists.sr.ht", "oauth-client-secret")
        self.configure_meta_auth(meta_client_id, meta_client_secret)

        @self.context_processor
        def inject():
            return {
                "diffstat": _diffstat,
                "format_body": _format_body,
                "post_address": _post_address,
                "quote": quote,
            }

        @self.login_manager.user_loader
        def user_loader(session):
            return User.query.filter(User.session == session).one_or_none()

    def lookup_or_register(self, exchange, profile, scopes):
        user = User.query.filter(User.username == profile["username"]).first()
        if not user:
            user = User()
            db.session.add(user)
        user.username = profile.get("username")
        user.email = profile.get("email")
        user.admin = profile.get("admin")
        user.oauth_token = exchange["token"]
        user.oauth_token_expires = exchange["expires"]
        user.oauth_token_scopes = scopes
        if user.session is None:
            user.generate_session()
        db.session.commit()
        return user

app = LoginApp()
