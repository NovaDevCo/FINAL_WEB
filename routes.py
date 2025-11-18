from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from flask_login import login_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models import User, SellerProfile, db

# import from forms - reusable classess
from forms import (
    LoginNormalUser, LoginSeller,
    RegisterNormalUser, RegisterSeller    
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# --- USER LOGIN ---
@auth_bp.route("/login/user", methods=["GET", "POST"])
def login_user_route():
    form = LoginNormalUser()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("Email not registered. Please create an account.", "warning")
        elif not user.check_password(form.password.data):
            flash("Incorrect password. Please try again.", "danger")
        else:
            login_user(user, remember=form.remember_me.data)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
    return render_template("user_login.html", form=form)


# --- SELLER LOGIN ---
@auth_bp.route("/login/seller", methods=["GET", "POST"])
def seller_login():
    form = LoginSeller()
    if form.validate_on_submit():
        seller = SellerProfile.query.filter_by(email=form.email.data).first()
        if not seller:
            flash("Email not registered as a seller. Please sign up first.", "warning")
        elif not seller.check_password(form.password.data):
            flash("Incorrect password. Please try again.", "danger")
        else:
            linked_user = seller.user
            if linked_user:
                login_user(linked_user, remember=form.remember_me.data)
                flash("Seller login successful!", "success")
                return redirect(url_for("home"))
            else:
                flash("Linked user account not found.", "danger")
    return render_template("seller_login.html", form=form)


# --- USER REGISTER ---
@auth_bp.route("/register/user", methods=["GET", "POST"])
def register_user():
    form = RegisterNormalUser()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists. Please log in instead.", "warning")
            return redirect(url_for("auth.login_user_route"))

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
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login_user_route"))
        except IntegrityError:
            db.session.rollback()
            flash("An account with this email already exists.", "danger")

    return render_template("register_as_user.html", form=form)


# --- SELLER REGISTER ---
@auth_bp.route("/register/seller", methods=["GET", "POST"])
def register_seller():
    form = RegisterSeller()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        existing_seller = SellerProfile.query.filter_by(email=form.email.data).first()
        if existing_user or existing_seller:
            flash("Email already exists. Please log in instead.", "warning")
            return redirect(url_for("auth.seller_login"))

        try:
            hashed_pw = generate_password_hash(form.password.data)
            new_user = User(
                email=form.email.data,
                password_hash=hashed_pw,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                address=form.address.data,
            )
            db.session.add(new_user)
            db.session.flush()
            new_seller_profile = SellerProfile(
                shop_name=form.shopname.data,
                email=form.email.data,
                password_hash=hashed_pw,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                address=form.address.data,
                user_id=new_user.id,
            )
            db.session.add(new_seller_profile)
            db.session.commit()
            flash("Seller registration successful! Please log in.", "success")
            return redirect(url_for("auth.seller_login"))
        except IntegrityError:
            db.session.rollback()
            flash("An account with this email already exists.", "danger")

    return render_template("register_as_seller.html", form=form)



# no html yet
@auth_bp.route("/forgotpassword", methods=["GET", "POST"])
def forgot_password():
    try:
        if request.method == "POST":
            email = request.form.get("email").strip()
            new_password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            # Validate form input
            if not email or not new_password or not confirm_password:
                flash("Please fill out all fields.", "warning")
                return redirect(url_for("auth.forgot_password"))

            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("auth.forgot_password"))

            # Query user by email
            user = User.query.filter_by(email=email).first()

            if not user:
                flash("No account found with that email address.", "danger")
                return redirect(url_for("auth.forgot_password"))

            # Update password securely
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()

            flash("Password successfully updated! Please log in.", "success")
            return redirect(url_for("auth.login_user_route"))

        # Render the form
        return render_template("forgot_password.html")

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"[DB Error] Forgot Password: {e}")
        flash("A database error occurred. Please try again later.", "danger")
        return redirect(url_for("auth.forgot_password"))

    except Exception as e:
        print(f"[Error] Forgot Password: {e}")
        flash("An unexpected error occurred. Please try again later.", "danger")
        return redirect(url_for("auth.forgot_password"))
