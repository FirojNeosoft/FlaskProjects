from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from . import auth
from .. import db
from ..models import User
from ..email import send_email
from .forms import LoginForm, RegistrationForm
from datetime import datetime


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()

@auth.route("/", methods=["GET", "POST"])
def index():

    # rendering registration form
    form = RegistrationForm()
    current_time = datetime.utcnow()

    if request.method == "POST":
        if form.validate_on_submit():
            user = User(first_name=form.first_name.data,
                        last_name=form.last_name.data,
                        dob=form.dob.data,
                        gender=form.gender.data,
                        nationality=form.nationality.data,
                        residence=form.residence.data,
                        postal_code=form.postal_code.data,
                        username=form.username.data,
                        email=form.email.data,
                        password=form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Thanks for signing up! A confirmation email has been sent to your email address.')
            token = user.generate_confirmation_token()
            send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
            login_user(user)
            return redirect(url_for('main.home'))

    return render_template('auth/register.html', form=form)

@auth.route('/login', methods=["GET", "POST"])
def login():
    """ Log User In"""

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.home'))
        flash('Invalid Email and/or password')

    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """ Log user out """

    logout_user()
    return redirect(url_for('auth.index'))

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.home'))
    if current_user.confirmed(token):
        flash('You have confirmed your account, Thanks!')
    else:
        flash('the confirmation link has expired or is invalid')
    return redirect(url_for('main.home'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to your email address')
    return redirect(url_for('main.home'))

# check if user is confirmed and route accordingly
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for('main.home'))
    return render_template('auth/unconfirmed.html')

@auth.route('/register', methods=["GET", "POST"])
def register():
    return redirect(url_for('auth.index'))

