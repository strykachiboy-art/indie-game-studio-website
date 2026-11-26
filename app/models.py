from datetime import datetime, timezone

from flask import url_for
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def utcnow() -> datetime:
    """Naive UTC now (matches the existing DateTime columns, no deprecation warning)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)  # index=True removed — redundant
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    bio = db.Column(db.String(280), nullable=True)
    # Deferred: the image bytes are only loaded when /avatar/<id> is served,
    # not on every request that loads current_user.
    avatar_data = db.deferred(db.Column(db.LargeBinary, nullable=True))
    avatar_version = db.Column(db.Integer, default=0, nullable=False, server_default="0")

    posts = db.relationship(
        "Post", backref="author", lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,          # let the DB handle the delete, not the ORM
    )
    
    messages = db.relationship(
        "Message", backref="author", lazy=True,
        cascade="all, delete-orphan",
        passive_deletes=True,          # let the DB handle the delete, not the ORM
    )

    @property
    def has_avatar(self) -> bool:
        return (self.avatar_version or 0) > 0

    @property
    def avatar_url(self):
        if not self.has_avatar:
            return None
        return url_for("profile.avatar", user_id=self.id, v=self.avatar_version)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    body = db.Column(db.Text, nullable=False)
    published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Post {self.title}>"


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    def __repr__(self) -> str:
        return f"<Message from {self.name}>"