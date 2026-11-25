from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..forms import LoginForm, RegisterForm
from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        elif User.query.filter_by(username=username).first():
            flash("That username is taken.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome aboard!", "success")
            return redirect(url_for("main.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash("Logged in successfully.", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/") and not next_page.startswith("//") and "\\" not in next_page:
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("main.index"))

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))
