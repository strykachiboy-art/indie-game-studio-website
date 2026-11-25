import pytest

from app.extensions import db
from app.models import Message, User


@pytest.mark.parametrize("path", ["/", "/about", "/games", "/devlog", "/contact", "/login", "/register"])
def test_public_pages_load(client, path):
    assert client.get(path).status_code == 200


def test_404_page(client):
    assert client.get("/nope").status_code == 404


def test_admin_requires_login(client):
    resp = client.get("/admin/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_admin_blocks_non_admin(client, app):
    user = User(username="bob", email="bob@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    client.post("/login", data={"email": "bob@example.com", "password": "password123"})
    assert client.get("/admin/").status_code == 403


def test_contact_form_saves_message(client, app):
    client.post("/contact", data={"name": "Sam", "email": "sam@example.com", "body": "Hello there, nice site"})
    assert Message.query.count() == 1


def test_login_does_not_redirect_offsite(client, app):
    user = User(username="bob", email="bob@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    resp = client.post("/login?next=//evil.com", data={"email": "bob@example.com", "password": "password123"})
    assert "evil.com" not in resp.headers["Location"]


def test_admin_pages_render_with_data(client, app):
    from app.models import Post
    admin = User(username="boss", email="boss@example.com", is_admin=True)
    admin.set_password("password123")
    db.session.add(admin)
    db.session.flush()
    db.session.add_all([
        Post(title="Hi", slug="hi", body="body", user_id=admin.id),
        Message(name="Sam", email="sam@example.com", body="hello there"),
    ])
    db.session.commit()
    client.post("/login", data={"email": "boss@example.com", "password": "password123"})
    for path in ["/admin/", "/admin/users", "/admin/posts", "/admin/messages", "/admin/posts/new"]:
        assert client.get(path).status_code == 200, path
