from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, BooleanField, TelField, DecimalField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp

class BaseLoginInfo(FlaskForm):
    email = StringField("Email", 
    validators=[
        DataRequired()
        ]
    )

    password = PasswordField("Password", 
    validators=[DataRequired()]
    )

class BaseRegisterInfo(BaseLoginInfo):
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", 
        message="Passwords must match!")]
    )

class RegisterInfo(FlaskForm):
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    register = SubmitField("Register")
    address = StringField("Address", 
    validators=[
        DataRequired()
        ]
    )
    phone = TelField("Phone Number",
    validators=[
            DataRequired(),
            Length(min=7, max=15),
            Regexp(r"^\+?\d{7,15}$", message="Enter a valid phone number")
        ]
    )

class RegisterNormalUser(RegisterInfo, BaseRegisterInfo):
    birthday = DateField("Birthday", format="%Y-%m-%d", 
    validators=[DataRequired()]
    )

class RegisterSeller(RegisterInfo, BaseRegisterInfo):
    shopname = StringField("Shop Name", 
    validators=[DataRequired()]
    )

class LoginNormalUser(BaseLoginInfo):
    remember_me = BooleanField("Remember Me")
    loginNormal = SubmitField("Login")

class LoginSeller(BaseLoginInfo):
    remember_me = BooleanField("Remember Me")
    loginSeller = SubmitField("Login")

class Product_Form(FlaskForm):
    product_name = StringField("Product name: ", 
    validators=[DataRequired()]
    )
    product_price = DecimalField("Price: ", 
    validators=[DataRequired()]
    )
    description = StringField("Descriptions", 
    validators=[DataRequired()]
    )
