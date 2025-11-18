# ----- IMPORTS -----
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from models import db, User
from routes import auth_bp  # import your blueprint


# ----- APP INITIALIZATION -----
app = Flask(__name__)

# ----- CONFIGURATION -----
app.config["SECRET_KEY"] = "Axtn3556et"  # change to something strong
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ----- INITIALIZE DATABASE -----
db.init_app(app)

# ----- FLASK-LOGIN SETUP -----
login_manager = LoginManager()
login_manager.init_app(app)

# Where Flask-Login redirects if user not logged in
login_manager.login_view = "auth.login_user_route"
login_manager.login_message_category = "info"


# ----- USER LOADER -----
@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader function"""
    return User.query.get(int(user_id))


# ----- REGISTER BLUEPRINTS -----
app.register_blueprint(auth_bp)


# ----- BASIC ROUTES -----
@app.route("/")
def home():
    return render_template("home.html")  # load the home.html

# ----- RUN THE APP -----
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ensures DB tables exist
    app.run(debug=True)
