from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select

db = SQLAlchemy()

# ==========================
# USER MODEL
# ==========================
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

    seller_profile = db.relationship("SellerProfile", back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ==========================
# SELLER PROFILE MODEL
# ==========================
class SellerProfile(db.Model):
    __tablename__ = "seller_profile"

    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(100), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    user = db.relationship("User", back_populates="seller_profile")

    # ---- Hybrid Property + Expression ----
    @hybrid_property
    def email(self):
        """Get seller email in Python."""
        return self.user.email

    @email.expression
    def email(cls):
        """
        SQL expression for querying SellerProfile.email.

        SELECT user.email FROM user WHERE user.id = seller_profile.user_id
        """
        return (
            select(User.email)
            .where(User.id == cls.user_id)
            .scalar_subquery()
        )
