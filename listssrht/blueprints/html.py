from flask import Blueprint, render_template
from flask_login import current_user

html = Blueprint("html", __name__)

@html.route("/")
def index():
    if current_user is None:
        return render_template("index.html")
    return render_template("dashboard.html")
