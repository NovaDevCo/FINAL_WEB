from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from models import User, SellerAccount, db
from flask_login import login_user, current_user, login_required
from functools import wraps 

from forms import (
    LoginNormalUser, LoginSeller,
    RegisterNormalUser, RegisterSeller
)


views = Blueprint("views", __name__, url_prefix="/")


# ROLE-BASED ACCESS DECORATOR
def role_required(role):
    """
    Custom decorator to restrict access to a route based on the user's role.
    It automatically wraps Flask-Login's @login_required.
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            # Check if the current user's role matches the required role
            if current_user.role != role:
                flash(f"Access denied. You must be logged in as a {role} to view this page.", "danger")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# NEW: SELLER DASHBOARD ROUTE (Protected)
@views.route("/dashboard/seller")
@role_required("seller")

def seller_dashboard():
    """Route accessible only by users with role='seller'."""
    # This page will only load if current_user.role == 'seller'
    return render_template("seller_dashboard.html", user=current_user)


# user ordinary user
@views.route("/login/user", methods=["GET", "POST"])
def login_user():
    form = LoginNormalUser()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Check if the user exists
        if not user:
            flash("Email not registered. Please create an account.", "warning")

        # Check password
        elif not user.check_password(form.password.data):
            flash("Incorrect password. Please try again.", "danger")

        else:
            login_user(user, remember=form.remember_me.data)
            flash("Login successful!", "success")
            return redirect(url_for("home"))

    return render_template("user_login.html", form=form)


# Login as seller
@views.route("/login/seller", methods=["GET", "POST"])
def seller_login():
    form = LoginSeller()
    if form.validate_on_submit():
        # Find the User first based on email
        user = User.query.filter_by(email=form.email.data).first()
        
        if not user:
             flash("Email not registered. Please sign up first.", "warning")
             return redirect(url_for("views.login_user"))

        # If user exists, check if they have a seller profile
        seller_profile = SellerProfile.query.filter_by(user_id=user.id).first()

        if not seller_profile:
            # If the user exists but is NOT a seller, give a specific message
            flash("This account is not registered as a seller.", "warning")
            return redirect(url_for("views.login_user"))

        # Check password
        if not user.check_password(form.password.data):
            flash("Incorrect password.", "danger")

        else:
            # Successfully logged in as a seller
            login_user(user, remember=form.remember_me.data)
            flash("Seller login successful!", "success")
            # Redirect seller to their protected dashboard
            return redirect(url_for("views.seller_dashboard"))

    return render_template("seller_login.html", form=form)



@views.route("/register/user", methods=["GET", "POST"])
def register_user():
    form = RegisterNormalUser()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists.", "warning")
            # FIX: Use corrected blueprint name 'views'
            return redirect(url_for("views.login_user"))

        try:
            hashed_pw = generate_password_hash(form.password.data)

            new_user = User(
                email=form.email.data,
                password_hash=hashed_pw,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                birthday=form.birthday.data,
                phone=form.phone.data,
                address=form.address.data,
                role="user"
            )

            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! Please log in.", "success")
            # FIX: Use corrected blueprint name 'views'
            return redirect(url_for("views.login_user"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already used.", "danger")
    return render_template("register_as_user.html", form=form)


@views.route("/register/seller", methods=["GET", "POST"])
def register_seller():
    form = RegisterSeller()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash("Email already exists.", "warning")

            return redirect(url_for("views.seller_login"))

        try:
            hashed_pw = generate_password_hash(form.password.data)

            new_user = User(
                email=form.email.data,
                password_hash=hashed_pw,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                address=form.address.data,
                role="seller"        # <<< ROLE SYSTEM
            )

            db.session.add(new_user)
            db.session.flush()

            new_seller = SellerAccount(
                shop_name=form.shopname.data,
                user_id=new_user.id
            )

            db.session.add(new_seller)
            db.session.commit()

            flash("Seller registration successful! Please log in to your account.", "success")
            # FIX: Use corrected blueprint name 'views'
            return redirect(url_for("views.seller_login"))

        except IntegrityError:
            db.session.rollback()
            flash("Email already used!", "danger")

    return render_template("register_as_seller.html", form=form)

@views.route("/Default/product")
def default_product():
    return render_template("#")