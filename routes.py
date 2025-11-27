from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from models import User, SellerAccount, Product, db
from flask_login import login_user, current_user, login_required
from functools import wraps

from forms import (
    LoginNormalUser, LoginSeller,
    RegisterNormalUser, RegisterSeller
)

views = Blueprint("views", __name__, url_prefix="/")

# ROLE-BASED ACCESS DECORATOR
def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required # This already handles the login requirement
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash(f"Access denied. You must be logged in as a {role} to view this page.", "danger")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# SELLER DASHBOARD
@views.route("/dashboard/seller")
@role_required("seller")
# REMOVED: @login_required (already included in @role_required)
def seller_dashboard():
    products = Product.query.filter_by(seller_id=current_user.sellerAccount.id).all()

    if not products:  # Seed products if none exist
        demo_products = [
            Product(
                name="Handmade Wooden Bowl",
                price=350,
                # FIXED: Changed 'description' to 'description_text' 
                # (or change model to 'description') - I'll stick to 'description_text' here
                description_text="Crafted from local mahogany, perfect for serving or decoration.",
                seller_id=current_user.sellerAccount.id
            ),
            Product(
                name="Woven Artisan Bag",
                price=1200,
                # FIXED: Argument name correction
                description_text="Eco-friendly handwoven bag made by local artisans.",
                seller_id=current_user.sellerAccount.id
            ),
            Product(
                name="Ceramic Coffee Mug",
                price=250,
                # FIXED: Argument name correction
                description_text="Hand-painted ceramic mug, dishwasher safe.",
                seller_id=current_user.sellerAccount.id
            ),
            Product(
                name="Leather Journal",
                price=800,
                # FIXED: Argument name correction
                description_text="Hand-stitched leather journal with recycled paper.",
                seller_id=current_user.sellerAccount.id
            ),
            Product(
                name="Decorative Wall Hanging",
                price=600,
                # FIXED: Argument name correction
                description_text="Colorful wall hanging made from natural fibers.",
                seller_id=current_user.sellerAccount.id
            )
        ]
        db.session.add_all(demo_products)
        db.session.commit()
        products = demo_products

    # Manual static image links
    manual_images = [
        url_for('static', filename='products/1.1.jpg'),
        url_for('static', filename='products/1.2.jpg'),
        url_for('static', filename='products/1.3.jpg'),
        url_for('static', filename='products/1.4.jpg'),
        url_for('static', filename='products/1.5.jpg'),
    ]

    for i, product in enumerate(products):
        if i < len(manual_images):
            product.image_url = manual_images[i]

    # Decide what to render based on products
    has_products = len(products) > 0

    return render_template(
        "seller_dashboard.html",
        user=current_user,
        products=products,
        has_products=has_products
    )


@views.route("/dashboard/user")
@role_required("user")
def user_dashboard():
    return render_template("user_dashboard.html", user=current_user)

# USER LOGIN
@views.route("/login/user", methods=["GET", "POST"])
def loginUser():
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
    return render_template("user_login.html", form=form, is_exclude=True)

# SELLER LOGIN
@views.route("/login/seller", methods=["GET", "POST"])
def seller_login():
    form = LoginSeller()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("Email not registered. Please sign up first.", "warning")
            return redirect(url_for("views.register_seller"))

        seller_account = SellerAccount.query.filter_by(user_id=user.id).first()
        if not seller_account:
            flash("This account is not registered as a seller.", "warning")
            return redirect(url_for("views.loginUser"))

        if not user.check_password(form.password.data):
            flash("Incorrect password.", "danger")
        else:
            login_user(user, remember=form.remember_me.data)
            flash("Seller login successful!", "success")
            return redirect(url_for("views.seller_dashboard"))
    return render_template("seller_login.html", form=form, is_exclude=True)

# USER REGISTRATION
@views.route("/register/user", methods=["GET", "POST"])
def register_user():
    form = RegisterNormalUser()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists.", "warning")
            return redirect(url_for("views.loginUser"))
        try:
            new_user = User(
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                birthday=form.birthday.data,
                phone=form.phone.data,
                address=form.address.data,
                role="user",
                is_default=False
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("views.loginUser"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already used.", "danger")
    return render_template("register_as_user.html", form=form, is_exclude=True)

# SELLER REGISTRATION
@views.route("/register/seller", methods=["GET", "POST"])
def register_seller():
    form = RegisterSeller()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already exists.", "warning")
            return redirect(url_for("views.seller_login"))
        try:
            new_user = User(
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                address=form.address.data,
                role="seller",
                is_default=False
            )
            db.session.add(new_user)
            db.session.flush()

            new_seller = SellerAccount(
                shop_name=form.shopname.data,
                user_id=new_user.id,
                is_default=False
            )
            db.session.add(new_seller)
            db.session.commit()
            flash("Seller registration successful! Please log in.", "success")
            return redirect(url_for("views.seller_login"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already used!", "danger")
    return render_template("register_as_seller.html", form=form, is_exclude=True)


@views.route("/about")
def about_page():
    return render_template("about.html")