from io import BytesIO

import pytest
from PIL import Image

from app.extensions import db
from app.models import Post, User


def _png(size=(600, 300), color=(163, 230, 53)):
    buf = BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    buf.seek(0)
    return buf


def _make_user(username="bob", admin=False):
    user = User(username=username, email=f"{username}@example.com", is_admin=admin)
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


def _login(client, username="bob"):
    client.post("/login", data={"email": f"{username}@example.com", "password": "password123"})


def _upload(client, fileobj, name="me.png"):
    return client.post(
        "/profile/avatar",
        data={"avatar": (fileobj, name)},
        content_type="multipart/form-data",
    )


def test_profile_requires_login(client):
    resp = client.get("/profile")
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]


def test_profile_page_renders(client, app):
    _make_user()
    _login(client)
    assert client.get("/profile").status_code == 200


def test_avatar_upload_is_resized_and_served(client, app):
    user = _make_user()
    _login(client)
    _upload(client, _png())
    db.session.refresh(user)
    assert user.avatar_version == 1

    resp = client.get(f"/avatar/{user.id}?v=1")
    assert resp.status_code == 200 and resp.mimetype == "image/webp"
    assert "immutable" in resp.headers["Cache-Control"]
    img = Image.open(BytesIO(resp.data))
    assert img.format == "WEBP" and img.size == (256, 256)


def test_avatar_shows_in_navbar_after_upload(client, app):
    user = _make_user()
    _login(client)
    _upload(client, _png())
    assert f"/avatar/{user.id}?v=1" in client.get("/").get_data(as_text=True)


def test_fake_image_rejected(client, app):
    user = _make_user()
    _login(client)
    _upload(client, BytesIO(b"<script>alert(1)</script>"), "evil.png")
    db.session.refresh(user)
    assert user.avatar_version == 0


def test_wrong_extension_rejected(client, app):
    user = _make_user()
    _login(client)
    _upload(client, _png(), "me.gif")
    db.session.refresh(user)
    assert user.avatar_version == 0


def test_oversized_avatar_rejected(client, app):
    user = _make_user()
    _login(client)
    big = BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * (2 * 1024 * 1024 + 10))
    _upload(client, big)
    db.session.refresh(user)
    assert user.avatar_version == 0


def test_remove_avatar(client, app):
    user = _make_user()
    _login(client)
    _upload(client, _png())
    client.post("/profile/avatar/remove")
    db.session.refresh(user)
    assert user.avatar_version == 0 and client.get(f"/avatar/{user.id}").status_code == 404


def test_avatar_404_when_none(client, app):
    user = _make_user()
    assert client.get(f"/avatar/{user.id}").status_code == 404


def test_update_bio(client, app):
    user = _make_user()
    _login(client)
    client.post("/profile", data={"bio": "Indie dev"})
    db.session.refresh(user)
    assert user.bio == "Indie dev"
    client.post("/profile", data={"bio": "x" * 281})
    db.session.refresh(user)
    assert user.bio == "Indie dev"  # too long, unchanged


def test_change_password(client, app):
    user = _make_user()
    _login(client)
    client.post("/profile/password", data={"current_password": "wrong", "new_password": "newpassword1", "confirm": "newpassword1"})
    db.session.refresh(user)
    assert user.check_password("password123")
    client.post("/profile/password", data={"current_password": "password123", "new_password": "newpassword1", "confirm": "newpassword1"})
    db.session.refresh(user)
    assert user.check_password("newpassword1")


def test_delete_account(client, app):
    _make_user()
    _login(client)
    client.post("/profile/delete", data={"password": "nope"})
    assert User.query.count() == 1
    client.post("/profile/delete", data={"password": "password123"})
    assert User.query.count() == 0


def test_admin_cannot_delete_account(client, app):
    _make_user("boss", admin=True)
    _login(client, "boss")
    client.post("/profile/delete", data={"password": "password123"})
    assert User.query.count() == 1


def test_logout_is_post_only(client, app):
    _make_user()
    _login(client)
    assert client.get("/logout").status_code == 405
    assert client.post("/logout").status_code == 302
    assert client.get("/profile").status_code == 302  # logged out now


def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"


# ---------- devlog / markdown ----------

def _post(user, title="Hello World", body="# Heading\n\nSome **bold** text", slug="hello-world", published=True):
    post = Post(title=title, slug=slug, body=body, published=published, user_id=user.id)
    db.session.add(post)
    db.session.commit()
    return post


def test_post_detail_renders_markdown(client, app):
    _post(_make_user())
    html = client.get("/devlog/hello-world").get_data(as_text=True)
    assert "<strong>bold</strong>" in html and "<h1>Heading</h1>" in html


def test_post_markdown_is_sanitised(client, app):
    _post(_make_user(), body='<script>alert(1)</script>[x](javascript:alert(1)) <img src=x onerror=alert(1)>')
    html = client.get("/devlog/hello-world").get_data(as_text=True)
    assert "<script>alert" not in html
    assert "javascript:" not in html
    assert "onerror" not in html


def test_unpublished_post_hidden_from_public_but_not_admin(client, app):
    admin = _make_user("boss", admin=True)
    _post(admin, published=False)
    assert client.get("/devlog/hello-world").status_code == 404
    _login(client, "boss")
    assert client.get("/devlog/hello-world").status_code == 200


def test_unknown_post_404(client):
    assert client.get("/devlog/nope").status_code == 404


def test_devlog_and_home_link_to_posts(client, app):
    user = _make_user()
    _post(user, title="First", slug="first")
    _post(user, title="Second", slug="second", body="Second body")
    for path in ("/devlog", "/"):
        html = client.get(path).get_data(as_text=True)
        assert "/devlog/first" in html and "/devlog/second" in html


def test_prev_next_navigation(client, app):
    from datetime import timedelta
    from app.models import utcnow
    user = _make_user()
    old = _post(user, title="Old", slug="old")
    new = _post(user, title="New", slug="new")
    old.created_at = utcnow() - timedelta(days=2)
    db.session.commit()
    html = client.get("/devlog/new").get_data(as_text=True)
    assert "/devlog/old" in html
    html = client.get("/devlog/old").get_data(as_text=True)
    assert "/devlog/new" in html


def test_filters():
    from app.filters import excerpt, reading_time
    assert excerpt("# Title\n\n**bold** & text", 50) == "Title bold & text"
    assert excerpt("word " * 100, 20).endswith("…")
    assert reading_time("one two") == "1 min read"
    assert reading_time("word " * 450) == "2 min read"


# ---------- migration ----------

def test_profile_migration_runs_on_old_schema(tmp_path):
    """Old users table (pre-profile) upgrades cleanly and keeps its rows."""
    import sqlalchemy as sa
    from alembic import command
    from alembic.config import Config

    db_file = tmp_path / "old.db"
    engine = sa.create_engine(f"sqlite:///{db_file}")
    with engine.begin() as conn:
        conn.execute(sa.text("CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(80), email VARCHAR(255), password_hash VARCHAR(255), is_admin BOOLEAN, created_at DATETIME)"))
        conn.execute(sa.text("INSERT INTO users (id, username, email, password_hash, is_admin) VALUES (1, 'old', 'o@x.com', 'h', 0)"))
        conn.execute(sa.text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(sa.text("INSERT INTO alembic_version VALUES ('57bded946b70')"))

    cfg = Config()
    cfg.set_main_option("script_location", "migrations")
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")
    import os
    os.environ["ALEMBIC_TEST_URL"] = f"sqlite:///{db_file}"
    from alembic.script import ScriptDirectory
    from alembic.runtime.environment import EnvironmentContext
    from alembic.runtime.migration import MigrationContext
    from alembic.operations import Operations

    script = ScriptDirectory.from_config(cfg)
    rev = script.get_revision("3f2c9a7d1b44")
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            rev.module.upgrade()

    cols = {c["name"] for c in sa.inspect(engine).get_columns("users")}
    assert {"bio", "avatar_data", "avatar_version"} <= cols
    with engine.connect() as conn:
        row = conn.execute(sa.text("SELECT username, avatar_version FROM users")).one()
    assert tuple(row) == ("old", 0)


# ---------- layout regressions ----------

def test_excerpt_skips_code_blocks():
    from app.filters import excerpt
    text = "Intro sentence here.\n\n```rust\nfn main() { println!(\"hi\"); }\n```\n\nOutro."
    out = excerpt(text, 200)
    assert "fn main" not in out and "Intro sentence here." in out and "Outro." in out


def test_navbar_switches_to_hamburger_at_lg_not_md(client):
    """The logged-in desktop nav is too wide for 768px, so it must only show from lg up."""
    html = client.get("/").get_data(as_text=True)
    assert "lg:flex" in html and "lg:hidden" in html
    assert "md:flex" not in html and "md:hidden" not in html


def test_admin_users_list_shows_uploaded_avatar(client, app):
    admin = _make_user("boss", admin=True)
    _login(client, "boss")
    _upload(client, _png())
    html = client.get("/admin/users").get_data(as_text=True)
    assert f"/avatar/{admin.id}?v=1" in html
