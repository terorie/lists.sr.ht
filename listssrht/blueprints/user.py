from flask import Blueprint, render_template, redirect
from flask_login import current_user
from listssrht.types import List, User, Email, Subscription

user = Blueprint("user", __name__)

@user.route("/")
def index():
    if not current_user:
        return render_template("index.html")
    # TODO: This query is probably gonna get pretty expensive
    recent = (Email.query
            .join(List)
            .join(Subscription)
            .filter(Email.list_id == List.id)
            .filter(Subscription.list_id == List.id)
            .filter(Subscription.user_id == current_user.id)
            .order_by(Email.created.desc())).limit(10).all()
    return render_template("dashboard.html", recent=recent)
