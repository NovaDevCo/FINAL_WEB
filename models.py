from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

db = SQLAlchemy()

# USER MODEL
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
    role = db.Column(db.String(20), nullable=False, default="user")
    # NEW: flag to mark a default showcase user
    is_default = db.Column(db.Boolean, default=False)
    
    sellerAccount = db.relationship("SellerAccount", back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# SELLER PROFILE MODEL
class SellerAccount(db.Model):
    __tablename__ = "SellerAccount"

    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)

    # NEW: flag to mark a default showcase seller
    is_default = db.Column(db.Boolean, default=False)



    user = db.relationship("User", back_populates="sellerAccount")

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
