from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, BooleanField, TelField, DecimalField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, NumberRange
from flask_wtf.file import FileField, FileRequired, FileAllowed

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
    # NOTE: Changing 'Descriptions' to 'Description' for clarity
    product_name = StringField("Product Name: ",
    validators=[DataRequired()]
    )
    product_price = DecimalField("Price: ",
    validators=[DataRequired(), NumberRange(min=0.01, message="Price must be greater than zero.")]
    )
    description = StringField("Description: ", # Matches form field name 'description'
    validators=[DataRequired()]
    )
    # The file field used for image upload
    image_file = FileField("Product Image: ",
    validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Images only!')
        ]
    )
    submit = SubmitField("Save Product")