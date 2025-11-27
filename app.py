# ----- IMPORTS -----
from flask import Flask, render_template, flash, redirect, url_for
from flask_login import login_required, LoginManager, logout_user
from models import db, User
from routes import views  # blueprint import
from datetime import timedelta

# ----- APP INITIALIZATION -----
app = Flask(__name__)

# ----- CONFIGURATION -----
app.config["SECRET_KEY"] = "Axtn3556et"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///likharyo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = 'static/product_images'
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)  # CHANGE: user stays logged in for 30 days
app.config["REMEMBER_COOKIE_REFRESH_EACH_REQUEST"] = True    # CHANGE: refresh cookie every visit
app.config["SESSION_PERMANENT"] = False   # CHANGE: session not permanent

# ----- INITIALIZE DATABASE -----
db.init_app(app)

# ----- FLASK-LOGIN -----
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "home"
login_manager.login_message_category = "info"

# ----- USER LOADER -----
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----- BLUEPRINT REGISTRATION -----
app.register_blueprint(views)

# ----- ROUTES -----

@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/logout")
@login_required
def log_out():
    logout_user()
    return redirect(url_for('home'))
    
# ----- RUN -----
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=8000)
