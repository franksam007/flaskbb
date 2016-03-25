# -*- coding: utf-8 -*-
"""
    flaskbb.auth.views
    ~~~~~~~~~~~~~~~~~~~~

    This view provides user authentication, registration and a view for
    resetting the password of a user if he has lost his password

    :copyright: (c) 2014 by the FlaskBB Team.
    :license: BSD, see LICENSE for more details.
"""
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, url_for, request
from flask_login import (current_user, login_user, login_required,
                         logout_user, confirm_login, login_fresh)
from flask_babelplus import gettext as _

from flaskbb.utils.helpers import render_template, redirect_or_next
from flaskbb.email import send_reset_token
from flaskbb.exceptions import AuthenticationError, LoginAttemptsExceeded
from flaskbb.auth.forms import (LoginForm, ReauthForm, ForgotPasswordForm,
                                ResetPasswordForm, RegisterForm,
                                EmailConfirmationForm)
from flaskbb.user.models import User
from flaskbb.fixtures.settings import available_languages
from flaskbb.utils.settings import flaskbb_config
from flaskbb.utils.tokens import get_token_status, make_token

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Logs the user in."""
    if current_user is not None and current_user.is_authenticated:
        return redirect(current_user.url)

    form = LoginForm(request.form)
    if form.validate_on_submit():
        try:
            user = User.authenticate(form.login.data, form.password.data)
            login_user(user, remember=form.remember_me.data)
            return redirect_or_next(url_for("forum.index"))
        except AuthenticationError:
            flash(_("Wrong Username or Password."), "danger")
        except LoginAttemptsExceeded:
            #timeout = (user.last_failed_login +
            #           timedelta(minutes=flaskbb_config["LOGIN_TIMEOUT"]))
            #timeout_left = datetime.utcnow() - timeout

            flash(_("Your account has been locked for %(minutes)s minutes "
                    "for too many failed login attempts.",
                    minutes=flaskbb_config["LOGIN_TIMEOUT"]), "warning")

    return render_template("auth/login.html", form=form)


@auth.route("/reauth", methods=["GET", "POST"])
@login_required
def reauth():
    """
    Reauthenticates a user.
    """
    if not login_fresh():
        form = ReauthForm(request.form)
        if form.validate_on_submit():
            if current_user.check_password(form.password.data):
                confirm_login()
                flash(_("Reauthenticated."), "success")
                return redirect_or_next(current_user.url)

            flash(_("Wrong password."), "danger")
        return render_template("auth/reauth.html", form=form)
    return redirect(request.args.get("next") or current_user.url)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash(("Logged out"), "success")
    return redirect(url_for("forum.index"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    Register a new user.
    """
    if current_user is not None and current_user.is_authenticated:
        return redirect_or_next(current_user.url)

    if not flaskbb_config["REGISTRATION_ENABLED"]:
        flash(_("The registration has been disabled."), "info")
        return redirect(url_for("forum.index"))

    form = RegisterForm(request.form)

    form.language.choices = available_languages()
    form.language.default = flaskbb_config['DEFAULT_LANGUAGE']
    form.process(request.form)  # needed because a default is overriden

    if form.validate_on_submit():
        user = form.save()
        login_user(user)

        if flaskbb_config["VERFIY_EMAIL"]:

            flash(_("verify your email by blablaabla"))
        else:
            flash(_("Thanks for registering."), "success")
        return redirect_or_next(current_user.url)

    return render_template("auth/register.html", form=form)


@auth.route('/reset-password', methods=["GET", "POST"])
def forgot_password():
    """
    Sends a reset password token to the user.
    """

    if not current_user.is_anonymous:
        return redirect(url_for("forum.index"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user:
            token = make_token(user, "reset_password")
            send_reset_token(user, token=token)

            flash(_("E-Mail sent! Please check your inbox."), "info")
            return redirect(url_for("auth.forgot_password"))
        else:
            flash(_("You have entered a Username or E-Mail Address that is "
                    "not linked with your account."), "danger")
    return render_template("auth/forgot_password.html", form=form)


@auth.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Handles the reset password process.
    """

    if not current_user.is_anonymous:
        return redirect(url_for("forum.index"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        expired, invalid, user = get_token_status(form.token.data,
                                                  "reset_password")

        if invalid:
            flash(_("Your Password Token is invalid."), "danger")
            return redirect(url_for("auth.forgot_password"))

        if expired:
            flash(_("Your Password Token is expired."), "danger")
            return redirect(url_for("auth.forgot_password"))

        if user:
            user.password = form.password.data
            user.save()
            flash(_("Your Password has been updated."), "success")
            return redirect(url_for("auth.login"))

    form.token.data = token
    return render_template("auth/reset_password.html", form=form)


@auth.route("/confirm-email/<token>", methods=["GET", "POST"])
def email_confirmation(token=None):
    """Handles the email verification process."""
    if current_user.is_authenticated and current_user.confirmed is not None:
        return redirect(url_for('forum.index'))

    if token is not None:
        expired, invalid, user = get_token_status(token, "verify_email")
        return

    form = None
    if token is None:
        form = EmailConfirmationForm()
        if form.validate_on_submit():
            pass

    return render_template("auth/email_verification.html", form=form)
