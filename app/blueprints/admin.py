import re

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..decorators import admin_required
from ..extensions import db
from ..forms import PostForm
from ..models import Message, Post, User

admin_bp = Blueprint("admin", __name__)


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug or "post"


def unique_slug(title: str, post_id: int | None = None) -> str:
    base = slugify(title)
    slug = base
    counter = 2
    while True:
        existing = Post.query.filter_by(slug=slug).first()
        if not existing or existing.id == post_id:
            return slug
        slug = f"{base}-{counter}"
        counter += 1


@admin_bp.before_request
@login_required
@admin_required
def restrict_to_admins():
    """Guard every admin route."""
    pass


@admin_bp.route("/")
def dashboard():
    stats = {
        "users": User.query.count(),
        "admins": User.query.filter_by(is_admin=True).count(),
        "posts": Post.query.count(),
        "published": Post.query.filter_by(published=True).count(),
        "messages": Message.query.count(),
        "unread": Message.query.filter_by(is_read=False).count(),
    }
    recent_messages = (
        Message.query.order_by(Message.created_at.desc()).limit(5).all()
    )
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_messages=recent_messages,
        recent_users=recent_users,
    )


# ----- Users -----
@admin_bp.route("/users")
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
def toggle_admin(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You can't change your own admin status.", "error")
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f"Updated admin rights for {user.username}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You can't delete your own account.", "error")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"Deleted user {user.username}.", "success")
    return redirect(url_for("admin.users"))


# ----- Posts -----
@admin_bp.route("/posts")
def posts():
    all_posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("admin/posts.html", posts=all_posts)


@admin_bp.route("/posts/new", methods=["GET", "POST"])
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data.strip(),
            slug=unique_slug(form.title.data),
            body=form.body.data.strip(),
            published=form.published.data,
            user_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash("Post created.", "success")
        return redirect(url_for("admin.posts"))
    return render_template("admin/post_form.html", form=form, heading="New post")


@admin_bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
def edit_post(post_id):
    post = db.get_or_404(Post, post_id)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data.strip()
        post.slug = unique_slug(form.title.data, post.id)
        post.body = form.body.data.strip()
        post.published = form.published.data
        db.session.commit()
        flash("Post updated.", "success")
        return redirect(url_for("admin.posts"))
    return render_template("admin/post_form.html", form=form, heading="Edit post")


@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "success")
    return redirect(url_for("admin.posts"))


# ----- Messages -----
@admin_bp.route("/messages")
def messages():
    all_messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template("admin/messages.html", messages=all_messages)


@admin_bp.route("/messages/<int:message_id>/toggle-read", methods=["POST"])
def toggle_read(message_id):
    message = db.get_or_404(Message, message_id)
    message.is_read = not message.is_read
    db.session.commit()
    return redirect(url_for("admin.messages"))


@admin_bp.route("/messages/<int:message_id>/delete", methods=["POST"])
def delete_message(message_id):
    message = db.get_or_404(Message, message_id)
    db.session.delete(message)
    db.session.commit()
    flash("Message deleted.", "success")
    return redirect(url_for("admin.messages"))