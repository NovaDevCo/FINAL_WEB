from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import secrets
from sqlalchemy.exc import IntegrityError
from models import User, SellerAccount, Product, db
from flask_login import login_user, current_user, login_required
from functools import wraps

from forms import (
    LoginNormalUser, LoginSeller,
    RegisterNormalUser, RegisterSeller,
    Product_Form
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


def save_picture(form_picture):
    # 1. Generate a unique filename
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + secure_filename(f_ext) # Use secure_filename on extension
    
    # 2. Define the absolute path for saving
    upload_path = os.path.join(current_app.root_path, 'static/product_images')

    # Ensure the directory exists
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    picture_path = os.path.join(upload_path, picture_fn)
    
    # 3. Save the file
    form_picture.save(picture_path)

    # 4. Return the URL path relative to the static folder
    return url_for('static', filename=f'product_images/{picture_fn}')


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



# --- SELLER DASHBOARD (Reads, Seeds, and passes Shop Name) ---
@views.route("/dashboard/seller")
@role_required("seller")
def seller_dashboard():
    if not current_user.sellerAccount:
        flash("Seller account not found.", "danger")
        return redirect(url_for('home'))

    # Fetch products associated with the current seller
    products = Product.query.filter_by(seller_id=current_user.sellerAccount.id).all()
    
    # --- SEEDING LOGIC (KEPT INTACT) ---
    if not products:  # Seed products if none exist
        demo_products = [
            Product(name="Handmade Wooden Bowl", price=350, description_text="Crafted from local mahogany.", seller_id=current_user.sellerAccount.id, image_url=url_for('static', filename='products/1.1.jpg')),
            Product(name="Woven Artisan Bag", price=1200, description_text="Eco-friendly handwoven bag.", seller_id=current_user.sellerAccount.id, image_url=url_for('static', filename='products/1.2.jpg')),
            Product(name="Ceramic Coffee Mug", price=250, description_text="Hand-painted ceramic mug.", seller_id=current_user.sellerAccount.id, image_url=url_for('static', filename='products/1.3.jpg')),
            Product(name="Leather Journal", price=800, description_text="Hand-stitched leather journal.", seller_id=current_user.sellerAccount.id, image_url=url_for('static', filename='products/1.4.jpg')),
            Product(name="Decorative Wall Hanging", price=600, description_text="Colorful wall hanging.", seller_id=current_user.sellerAccount.id, image_url=url_for('static', filename='products/1.5.jpg'))
        ]
        db.session.add_all(demo_products)
        db.session.commit()
        products = demo_products
    # --- END SEEDING LOGIC ---

    has_products = len(products) > 0
    shop_name = current_user.sellerAccount.shop_name 

    return render_template(
        "seller_dashboard.html",
        user=current_user,
        products=products,
        has_products=has_products,
        shop_name=shop_name
    )






@views.route("/product/add", methods=["GET", "POST"])
@role_required("seller")
def add_product():
    form = Product_Form()
    if form.validate_on_submit():
        # Handle file upload
        image_url = url_for('static', filename='default/default_product.jpg') # Default fallback
        if form.image_file.data:
            try:
                image_url = save_picture(form.image_file.data)
            except Exception as e:
                flash(f"Error saving image: {e}", "danger")
                return redirect(url_for('views.add_product'))

        # Create new product
        new_product = Product(
            name=form.product_name.data,
            price=form.product_price.data,
            description_text=form.description.data, # Use form.description.data
            image_url=image_url,
            seller_id=current_user.sellerAccount.id
        )
        db.session.add(new_product)
        db.session.commit()
        flash(f"Product '{new_product.name}' added successfully!", "success")
        return redirect(url_for('views.seller_dashboard'))

    # Load perfectly: uses the same form template
    return render_template("product_form.html", 
                           form=form, 
                           title="Add New Product",
                           action_url=url_for('views.add_product'),
                           is_edit=False)


# --- NEW: EDIT PRODUCT ---
@views.route("/product/edit/<int:product_id>", methods=["GET", "POST"])
@role_required("seller")
def edit_product(product_id):
    # Fetch the product, ensuring it belongs to the current seller
    product = Product.query.filter_by(id=product_id, seller_id=current_user.sellerAccount.id).first_or_404()
    form = Product_Form()
    
    # Remove the DataRequired validator from image_file when editing
    # so the user doesn't have to re-upload it every time.
    form.image_file.validators = [v for v in form.image_file.validators if v.__class__.__name__ != 'DataRequired']

    if form.validate_on_submit():
        # Check if a new image was uploaded
        if form.image_file.data:
            try:
                image_url = save_picture(form.image_file.data)
                product.image_url = image_url # Update image URL
            except Exception as e:
                flash(f"Error saving image: {e}", "danger")
                return redirect(url_for('views.edit_product', product_id=product.id))
        
        # Update other product fields
        product.name = form.product_name.data
        product.price = form.product_price.data
        product.description_text = form.description.data # Use form.description.data
        
        db.session.commit()
        flash(f"Product '{product.name}' updated successfully!", "success")
        return redirect(url_for('views.seller_dashboard'))

    elif request.method == 'GET':
        # Pre-populate form fields on GET request
        form.product_name.data = product.name
        form.product_price.data = product.price
        form.description.data = product.description_text
        # Note: image_file field cannot be pre-populated
        
    # Pass current image URL for preview
    current_image = product.image_url

    return render_template("product_form.html", 
                           form=form, 
                           title=f"Edit Product: {product.name}",
                           product=product,
                           action_url=url_for('views.edit_product', product_id=product.id),
                           is_edit=True,
                           current_image=current_image)


# --- NEW: DELETE PRODUCT (simple POST route) ---
@views.route("/product/delete/<int:product_id>", methods=["POST"])
@role_required("seller")
def delete_product(product_id):
    product = Product.query.filter_by(id=product_id, seller_id=current_user.sellerAccount.id).first_or_404()
    
    # Optional: Delete the image file from the server here if it exists
    
    db.session.delete(product)
    db.session.commit()
    flash(f"Product '{product.name}' deleted successfully.", "success")
    return redirect(url_for('views.seller_dashboard'))