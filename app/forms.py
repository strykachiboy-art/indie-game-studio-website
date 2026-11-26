from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (
    BooleanField,
    PasswordField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError,
)


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    body = TextAreaField("Message", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField("Send message")


class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    body = TextAreaField("Body", validators=[DataRequired()])
    published = BooleanField("Published", default=True)
    submit = SubmitField("Save post")



class ProfileForm(FlaskForm):
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=280)])
    submit = SubmitField("Save profile")


class AvatarForm(FlaskForm):
    avatar = FileField(
        "Profile picture",
        validators=[
            FileRequired(message="Choose an image first."),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Use a JPG, PNG or WebP image."),
        ],
    )
    submit = SubmitField("Upload")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[DataRequired(), Length(min=8)])
    confirm = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit = SubmitField("Change password")


class DeleteAccountForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Delete my account")
