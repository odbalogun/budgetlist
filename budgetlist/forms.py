from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, SelectMultipleField, \
    DecimalField, TextAreaField, IntegerField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from helpers import Unique, list_account_types
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username/Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    website = StringField('Website', validators=[DataRequired()])

class PeriodForm(FlaskForm):
    name = StringField('Period Name', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired()])
    head = SelectField('Department Head', validators=[DataRequired()], coerce=int)

class UserForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50), Unique(User, User.username, 'This username already exists')])
    email = StringField('Email Address', validators=[Optional(), Length(min=6, max=120), Email(), Unique(User, User.email, 'This email already exists')])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', [DataRequired(),
                                                          EqualTo('password', 'The passwords do not match')])
    user_type = SelectField('Account Type', [DataRequired()], choices=list_account_types, default=0)