from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from ..extensions import db
from ..forms import ContactForm
from ..models import Message, Post

main_bp = Blueprint("main", __name__)


GAMES = [
    {
        "title": "Neon Drift",
        "genre": "Arcade Racer",
        "status": "Released",
        "blurb": "A synthwave-soaked racer where you outrun the horizon at 200mph.",
    },
    {
        "title": "Hollow Signal",
        "genre": "Atmospheric Horror",
        "status": "Early Access",
        "blurb": "Decode a dead space station's final transmission before it decodes you.",
    },
    {
        "title": "Bloom & Blade",
        "genre": "Roguelike Deckbuilder",
        "status": "Coming Soon",
        "blurb": "Grow a garden of cards, then cut down everything that threatens it.",
    },
    {
        "title": "Pocket Cosmos",
        "genre": "Cozy Sim",
        "status": "Released",
        "blurb": "Terraform tiny planets and befriend the odd creatures that move in.",
    },
]


@main_bp.route("/")
def index():
    posts = (
        Post.query.filter_by(published=True)
        .order_by(Post.created_at.desc())
        .limit(3)
        .all()
    )
    return render_template("index.html", games=GAMES[:4], posts=posts)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/games")
def games():
    return render_template("games.html", games=GAMES)


@main_bp.route("/devlog")
def devlog():
    posts = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).all()
    return render_template("devlog.html", posts=posts)


@main_bp.route("/devlog/<slug>")
def post_detail(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    is_admin = current_user.is_authenticated and current_user.is_admin
    if not post.published and not is_admin:
        abort(404)

    published = Post.query.filter(Post.published.is_(True))
    newer = published.filter(Post.created_at > post.created_at).order_by(Post.created_at.asc()).first()
    older = published.filter(Post.created_at < post.created_at).order_by(Post.created_at.desc()).first()
    return render_template("post.html", post=post, newer=newer, older=older)


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        message = Message(
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            body=form.body.data.strip(),
        )
        db.session.add(message)
        db.session.commit()
        flash("Thanks for reaching out — we'll get back to you soon!", "success")
        return redirect(url_for("main.contact"))

    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", "error")
    return render_template("contact.html", form=form)