from app.models import User
from app.extensions import db


def test_user_password_and_persistence(app):
    user = User(username="tester", email="tester@example.com")
    user.set_password("s3cret")

    assert user.check_password("s3cret")
    assert not user.check_password("wrong")

    db.session.add(user)
    db.session.commit()

    found = User.query.filter_by(username="tester").first()
    assert found is not None
    assert found.email == "tester@example.com"
