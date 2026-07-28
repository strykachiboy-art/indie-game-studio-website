from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(view):
    """Allow access only to authenticated users with is_admin=True."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped
