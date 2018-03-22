# -*- coding: utf-8 -*-
"""
    flaskbb.auth.forms
    ~~~~~~~~~~~~~~~~~~

    It provides the forms that are needed for the auth views.

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
import logging

from flask_babelplus import lazy_gettext as _
from wtforms import (BooleanField, HiddenField, PasswordField, SelectField,
                     StringField, SubmitField)
from wtforms.validators import (DataRequired, Email, EqualTo, InputRequired,
                                ValidationError, regexp)

from flaskbb.user.models import User
from flaskbb.utils.fields import RecaptchaField
from flaskbb.utils.forms import FlaskBBForm
from flaskbb.utils.helpers import time_utcnow

logger = logging.getLogger(__name__)


USERNAME_RE = r'^[\w.+-]+$'
is_valid_username = regexp(
    USERNAME_RE, message=_("You can only use letters, numbers or dashes.")
)


class LoginForm(FlaskBBForm):
    login = StringField(_("Username or Email address"), validators=[
        DataRequired(message=_("Please enter your username or email address."))
    ])

    password = PasswordField(_("Password"), validators=[
        DataRequired(message=_("Please enter your password."))])

    remember_me = BooleanField(_("Remember me"), default=False)

    submit = SubmitField(_("Login"))
    recaptcha = HiddenField(_("Captcha"))


class LoginRecaptchaForm(LoginForm):
    recaptcha = RecaptchaField(_("Captcha"))


class RegisterForm(FlaskBBForm):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A valid username is required")),
        is_valid_username])

    email = StringField(_("Email address"), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email(message=_("Invalid email address."))])

    password = PasswordField(_('Password'), validators=[
        InputRequired(),
        EqualTo('confirm_password', message=_('Passwords must match.'))])

    confirm_password = PasswordField(_('Confirm password'))

    recaptcha = RecaptchaField(_("Captcha"))

    language = SelectField(_('Language'))

    accept_tos = BooleanField(_("I accept the Terms of Service"), validators=[
        DataRequired(message=_("Please accept the TOS."))], default=True)

    submit = SubmitField(_("Register"))

    def save(self):
        user = User(username=self.username.data,
                    email=self.email.data,
                    password=self.password.data,
                    date_joined=time_utcnow(),
                    primary_group_id=4,
                    language=self.language.data)
        return user.save()


class ReauthForm(FlaskBBForm):
    password = PasswordField(_('Password'), validators=[
        DataRequired(message=_("Please enter your password."))])

    submit = SubmitField(_("Refresh Login"))


class ForgotPasswordForm(FlaskBBForm):
    email = StringField(_('Email address'), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email()])

    recaptcha = RecaptchaField(_("Captcha"))

    submit = SubmitField(_("Request Password"))


class ResetPasswordForm(FlaskBBForm):
    token = HiddenField('Token')

    email = StringField(_('Email address'), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email()])

    password = PasswordField(_('Password'), validators=[
        InputRequired(),
        EqualTo('confirm_password', message=_('Passwords must match.'))])

    confirm_password = PasswordField(_('Confirm password'))

    submit = SubmitField(_("Reset password"))

    def validate_email(self, field):
        email = User.query.filter_by(email=field.data).first()
        if not email:
            raise ValidationError(_("Wrong email address."))


class RequestActivationForm(FlaskBBForm):
    username = StringField(_("Username"), validators=[
        DataRequired(message=_("A valid username is required.")),
        is_valid_username])

    email = StringField(_("Email address"), validators=[
        DataRequired(message=_("A valid email address is required.")),
        Email(message=_("Invalid email address."))])

    submit = SubmitField(_("Send Confirmation Mail"))

    def validate_email(self, field):
        self.user = User.query.filter_by(email=field.data).first()
        # check if the username matches the one found in the database
        if not self.user.username == self.username.data:
            raise ValidationError(_("User does not exist."))

        if self.user.activated is True:
            raise ValidationError(_("User is already active."))


class AccountActivationForm(FlaskBBForm):
    token = StringField(_("Email confirmation token"), validators=[
        DataRequired(message=_("Please enter the token that we have sent to "
                               "you."))
    ])

    submit = SubmitField(_("Confirm Email"))
