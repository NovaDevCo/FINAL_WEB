from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

db = SQLAlchemy()

# -------------------------------
# USER MODEL (Base Authentication)
# -------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    birthday = db.Column(db.Date, nullable=True)
    address = db.Column(db.String(256), nullable=True)
    phone = db.Column(db.String(15), nullable=False)
    
    # CHANGED: Default role is now 'viewer' instead of 'user'
    role = db.Column(db.String(20), nullable=False, default="viewer") 
    is_default = db.Column(db.Boolean, default=False)

    # CHANGED: Renamed relationship from 'sellerAccount' to 'shop_admin'
    shop_admin = db.relationship("ShopAdmin", back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# -------------------------------
# SHOP ADMIN MODEL (Formerly SellerAccount)
# -------------------------------
# ShopAdmin is a Artisan or Shop Owner who can list products for sale.
class ShopAdmin(db.Model):
    __tablename__ = "shop_admin"    # ✅ Renamed table

    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    
    # Link to the User table
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    is_default = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship("User", back_populates="shop_admin")
    
    # CHANGED: Backref name updated
    products = db.relationship("Product", back_populates="admin", cascade="all, delete-orphan")

    @hybrid_property
    def email(self):
        return self.user.email

    @email.expression
    def email(cls):
        return (
            select(User.email)
            .where(User.id == cls.user_id)
            .scalar_subquery()
        )

# -------------------------------
# PRODUCT MODEL
# -------------------------------
class Product(db.Model):
    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(256), default="")
    description_text = db.Column(db.Text, nullable=False) 
    
    # CHANGED: Renamed foreign key from 'seller_id' to 'admin_id'
    admin_id = db.Column(db.Integer, db.ForeignKey("shop_admin.id"), nullable=False) 

    # CHANGED: Relationship is now 'admin'
    admin = db.relationship("ShopAdmin", back_populates="products") 