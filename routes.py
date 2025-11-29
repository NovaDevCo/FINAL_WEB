from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import secrets
from sqlalchemy.exc import IntegrityError
# CHANGED: Imported ShopAdmin
from models import User, ShopAdmin, Product, db
from flask_login import login_user, current_user, login_required
from functools import wraps

# Import forms (Make sure your forms.py exists)
from forms import (
    LoginNormalUser, LoginSeller,
    RegisterNormalUser, RegisterSeller,
    Product_Form
)

views = Blueprint("views", __name__, url_prefix="/")

# --- ROLE DECORATOR ---
def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required 
        def decorated_function(*args, **kwargs):
            # Strict check for 'viewer' or 'admin'
            if current_user.role != role:
                flash(f"Access denied. You must be logged in as a {role} to view this page.", "danger")
                return redirect(url_for('views.login_viewer')) # Redirect safe default
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + secure_filename(f_ext)
    
    upload_path = os.path.join(current_app.root_path, 'static/product_images')
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    picture_path = os.path.join(upload_path, picture_fn)
    form_picture.save(picture_path)
    return url_for('static', filename=f'product_images/{picture_fn}')


# =========================================================
#  SECTION 1: VIEWER ROUTES (Normal User)
# =========================================================

@views.route("/dashboard/viewer")
@role_required("viewer")
def viewer_dashboard():
    # Renders the user dashboard
    return render_template("user_dashboard.html", user=current_user)

@views.route("/login/viewer", methods=["GET", "POST"])
def login_viewer():
    form = LoginNormalUser()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("Email not registered.", "warning")
        elif not user.check_password(form.password.data):
            flash("Incorrect password.", "danger")
        else:
            # Optional: Ensure Admins don't login as Viewers
            if user.role == 'admin':
                flash("Admins should login via the Admin Portal.", "info")
                return redirect(url_for("views.login_admin"))
                
            login_user(user, remember=form.remember_me.data)
            flash("Login successful!", "success")
            return redirect(url_for("home")) # Assuming you have a home route
    return render_template("viewer_login.html", form=form, is_exclude=True)

@views.route("/register/viewer", methods=["GET", "POST"])
def register_viewer():
    form = RegisterNormalUser()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("Email already exists.", "warning")
            return redirect(url_for("views.login_viewer"))
        try:
            new_user = User(
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                birthday=form.birthday.data,
                phone=form.phone.data,
                address=form.address.data,
                role="viewer",  # CHANGED: 'viewer'
                is_default=False
            )
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("views.login_viewer"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already used.", "danger")
    return render_template("reg_viewer.html", form=form, is_exclude=True)


# =========================================================
#  SECTION 2: ADMIN ROUTES (Shop Owner)
# =========================================================

@views.route("/login/admin", methods=["GET", "POST"])
def login_admin():
    form = LoginSeller()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash("Email not registered.", "warning")
            return redirect(url_for("views.register_admin"))

        # CHANGED: Checking shop_admin table
        shop_admin = ShopAdmin.query.filter_by(user_id=user.id).first()
        if not shop_admin:
            flash("This account is not registered as a Shop Admin.", "warning")
            return redirect(url_for("views.login_viewer"))

        if not user.check_password(form.password.data):
            flash("Incorrect password.", "danger")
        else:
            login_user(user, remember=form.remember_me.data)
            flash("Admin login successful!", "success")
            return redirect(url_for("views.admin_dashboard"))
    return render_template("admin_login.html", form=form, is_exclude=True)

@views.route("/register/admin", methods=["GET", "POST"])
def register_admin():
    form = RegisterSeller()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already exists.", "warning")
            return redirect(url_for("views.login_admin"))
        try:
            # 1. Create Base User
            new_user = User(
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data),
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                address=form.address.data,
                role="admin",   # CHANGED: 'admin'
                is_default=False
            )
            db.session.add(new_user)
            db.session.flush()

            # 2. Create ShopAdmin
            new_admin = ShopAdmin(
                shop_name=form.shopname.data,
                user_id=new_user.id,
                is_default=False
            )
            db.session.add(new_admin)
            db.session.commit()
            flash("Admin registration successful! Please log in.", "success")
            return redirect(url_for("views.login_admin"))
        except IntegrityError:
            db.session.rollback()
            flash("Email already used!", "danger")
    return render_template("reg_admin.html", form=form, is_exclude=True)

@views.route("/dashboard/admin")
@role_required("admin")
def admin_dashboard():
    # CHANGED: Using shop_admin relationship
    if not current_user.shop_admin:
        flash("Admin account not found.", "danger")
        return redirect(url_for('home'))

    # Fetch products associated with the current admin
    products = Product.query.filter_by(admin_id=current_user.shop_admin.id).all()
    
    # --- SEEDING LOGIC ---
    if not products:
        demo_products = [
            Product(name="Handmade Wooden Bowl", price=350, description_text="Crafted from local mahogany.", admin_id=current_user.shop_admin.id, image_url=url_for('static', filename='products/1.1.jpg')),
            Product(name="Woven Artisan Bag", price=1200, description_text="Eco-friendly handwoven bag.", admin_id=current_user.shop_admin.id, image_url=url_for('static', filename='products/1.2.jpg')),
            Product(name="Ceramic Coffee Mug", price=250, description_text="Hand-painted ceramic mug.", admin_id=current_user.shop_admin.id, image_url=url_for('static', filename='products/1.3.jpg')),
        ]
        db.session.add_all(demo_products)
        db.session.commit()
        products = demo_products
    # --- END SEEDING ---

    shop_name = current_user.shop_admin.shop_name 

    return render_template(
        "admin_dashboard.html", # You can rename this file to admin_dashboard.html if you wish
        user=current_user,
        products=products,
        has_products=(len(products) > 0),
        shop_name=shop_name
    )


# =========================================================
#  SECTION 3: PRODUCT MANAGEMENT (Admin Only)
# =========================================================

@views.route("/product/add", methods=["GET", "POST"])
@role_required("admin")
def add_product():
    form = Product_Form()
    if form.validate_on_submit():
        image_url = url_for('static', filename='default/default_product.jpg')
        if form.image_file.data:
            try:
                image_url = save_picture(form.image_file.data)
            except Exception as e:
                flash(f"Error saving image: {e}", "danger")
                return redirect(url_for('views.add_product'))

        new_product = Product(
            name=form.product_name.data,
            price=form.product_price.data,
            description_text=form.description.data,
            image_url=image_url,
            admin_id=current_user.shop_admin.id  # CHANGED: admin_id
        )
        db.session.add(new_product)
        db.session.commit()
        flash(f"Product '{new_product.name}' added successfully!", "success")
        return redirect(url_for('views.admin_dashboard'))

    return render_template("product_form.html", 
                           form=form, 
                           title="Add New Product",
                           action_url=url_for('views.add_product'),
                           is_edit=False)

@views.route("/product/edit/<int:product_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_product(product_id):
    # Ensure product belongs to this admin
    product = Product.query.filter_by(id=product_id, admin_id=current_user.shop_admin.id).first_or_404()
    form = Product_Form()
    
    form.image_file.validators = [v for v in form.image_file.validators if v.__class__.__name__ != 'DataRequired']

    if form.validate_on_submit():
        if form.image_file.data:
            try:
                image_url = save_picture(form.image_file.data)
                product.image_url = image_url
            except Exception as e:
                flash(f"Error saving image: {e}", "danger")
                return redirect(url_for('views.edit_product', product_id=product.id))
        
        product.name = form.product_name.data
        product.price = form.product_price.data
        product.description_text = form.description.data
        
        db.session.commit()
        flash(f"Product '{product.name}' updated successfully!", "success")
        return redirect(url_for('views.admin_dashboard'))

    elif request.method == 'GET':
        form.product_name.data = product.name
        form.product_price.data = product.price
        form.description.data = product.description_text
        
    current_image = product.image_url

    return render_template("product_form.html", 
                           form=form, 
                           title=f"Edit Product: {product.name}",
                           product=product,
                           action_url=url_for('views.edit_product', product_id=product.id),
                           is_edit=True,
                           current_image=current_image)

@views.route("/product/delete/<int:product_id>", methods=["POST", "GET"])
@role_required("admin")
def delete_product(product_id):
    # Ensure product belongs to this admin
    product = Product.query.filter_by(id=product_id, admin_id=current_user.shop_admin.id).first_or_404()
    
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{product.name}' deleted successfully.", "success")
    return redirect(url_for('views.admin_dashboard'))


