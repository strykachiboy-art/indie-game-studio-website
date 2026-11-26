from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, logout_user

from ..extensions import db
from ..forms import (
    AvatarForm,
    ChangePasswordForm,
    DeleteAccountForm,
    ProfileForm,
)
from ..models import Post, User
from ..utils.images import AvatarError, process_avatar

profile_bp = Blueprint("profile", __name__)


def _flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            label = getattr(getattr(form, field, None), "label", None)
            flash(f"{label.text + ': ' if label else ''}{error}", "error")


@profile_bp.get("/avatar/<int:user_id>")
def avatar(user_id):
    user = db.session.get(User, user_id)
    if not user or not user.has_avatar or not user.avatar_data:
        abort(404)
    resp = Response(user.avatar_data, mimetype="image/webp")
    # The URL carries ?v=<version>, so a matching version can be cached forever.
    if request.args.get("v", type=int) == user.avatar_version:
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        resp.headers["Cache-Control"] = "public, max-age=300"
    return resp


@profile_bp.get("/profile")
@login_required
def view():
    post_count = Post.query.filter_by(user_id=current_user.id).count()
    return render_template(
        "profile.html",
        profile_form=ProfileForm(obj=current_user),
        avatar_form=AvatarForm(),
        password_form=ChangePasswordForm(),
        delete_form=DeleteAccountForm(),
        post_count=post_count,
    )


@profile_bp.post("/profile")
@login_required
def update():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.bio = (form.bio.data or "").strip() or None
        db.session.commit()
        flash("Profile updated.", "success")
    else:
        _flash_errors(form)
    return redirect(url_for("profile.view"))


@profile_bp.post("/profile/avatar")
@login_required
def upload_avatar():
    form = AvatarForm()
    if not form.validate_on_submit():
        _flash_errors(form)
        return redirect(url_for("profile.view"))
    try:
        data = process_avatar(form.avatar.data.stream)
    except AvatarError as exc:
        flash(str(exc), "error")
        return redirect(url_for("profile.view"))

    current_user.avatar_data = data
    current_user.avatar_version = (current_user.avatar_version or 0) + 1
    db.session.commit()
    flash("Profile picture updated.", "success")
    return redirect(url_for("profile.view"))


@profile_bp.post("/profile/avatar/remove")
@login_required
def remove_avatar():
    current_user.avatar_data = None
    current_user.avatar_version = 0
    db.session.commit()
    flash("Profile picture removed.", "success")
    return redirect(url_for("profile.view"))


@profile_bp.post("/profile/password")
@login_required
def change_password():
    form = ChangePasswordForm()
    if not form.validate_on_submit():
        _flash_errors(form)
    elif not current_user.check_password(form.current_password.data):
        flash("Current password is incorrect.", "error")
    else:
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Password changed.", "success")
    return redirect(url_for("profile.view"))


@profile_bp.post("/profile/delete")
@login_required
def delete_account():
    if current_user.is_admin:
        flash("Admin accounts can't be deleted here.", "error")
        return redirect(url_for("profile.view"))

    form = DeleteAccountForm()
    if not form.validate_on_submit():
        _flash_errors(form)
        return redirect(url_for("profile.view"))
    if not current_user.check_password(form.password.data):
        flash("Password is incorrect, account not deleted.", "error")
        return redirect(url_for("profile.view"))

    user = current_user._get_current_object()
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash("Your account has been deleted.", "success")
    return redirect(url_for("main.index"))
