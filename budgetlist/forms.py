from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, HiddenField, \
    DecimalField, TextAreaField, IntegerField, RadioField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from helpers import Unique, list_account_types, list_budget_types, list_percentages, list_task_status
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
    start_date = DateField('Start Date', validators=[DataRequired()], format='%d/%m/%Y')
    end_date = DateField('End Date', validators=[DataRequired()], format='%d/%m/%Y')

class DepartmentForm(FlaskForm):
    depart_id = HiddenField()
    name = StringField('Department Name', validators=[DataRequired()])

class UserForm(FlaskForm):
    user_id = HiddenField()
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email Address', validators=[DataRequired(), Length(min=6, max=120), Email()])
    password = PasswordField('Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm Password', [Optional(),
                                                          EqualTo('password', 'The passwords do not match')])
    department = SelectField('Department', validators=[DataRequired()], coerce=int)
    user_type = SelectField('Account Type', choices=[(list_account_types.index(a), a) for a in list_account_types], coerce=int)

class EditUserForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email Address', validators=[DataRequired(), Length(min=6, max=120), Email()])
    password = PasswordField('Password', validators=[Optional()])
    confirm_password = PasswordField('Confirm Password', [Optional(),
                                                          EqualTo('password', 'The passwords do not match')])
    department = SelectField('Department', validators=[DataRequired()], coerce=int)
    user_type = SelectField('Account Type', validators=[DataRequired()], choices=[(list_account_types.index(a), a) for a in list_account_types], coerce=int)

class BudgetForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    allocation = IntegerField('Allocation', validators=[DataRequired()])
    period = SelectField('Fiscal Period', validators=[DataRequired()], coerce=int)
    budget_type = SelectField('Budget Type', coerce=int)

class SubBudgetForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    allocation = IntegerField('Allocation', validators=[DataRequired()])
    parent_id = HiddenField()
    sub_budget_id = HiddenField(default=0)

class ProjectForm(FlaskForm):
    title = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    budget_limit = IntegerField('Allocation')
    budget_1 = SelectField('Budget Type', coerce=int)
    budget_2 = SelectField('Budget Type', coerce=int)
    budget_3 = SelectField('Budget Type', coerce=int)
    start_date = DateField('Start Date', validators=[DataRequired()], format='%d/%m/%Y')
    end_date = DateField('End Date', validators=[DataRequired()], format='%d/%m/%Y')
    priority = SelectField('Priority', coerce=int)
    owner_id = HiddenField()

class TaskForm(FlaskForm):
    title = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    allocation = IntegerField('Allocation')
    assigned_to = SelectField('Assigned To', coerce=int)
    start_date = DateField('Start Date', validators=[DataRequired()], format='%d/%m/%Y')
    end_date = DateField('End Date', validators=[DataRequired()], format='%d/%m/%Y')
    priority = SelectField('Priority', coerce=int)
    owner_id = HiddenField()
    task_submit = HiddenField()

class SubTaskForm(FlaskForm):
    title = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    allocation = IntegerField('Allocation')
    assigned_to = SelectField('Assigned To', coerce=int)
    start_date = DateField('Start Date', validators=[DataRequired()], format='%d/%m/%Y')
    end_date = DateField('End Date', validators=[DataRequired()], format='%d/%m/%Y')
    priority = SelectField('Priority', coerce=int)
    owner_id = HiddenField()
    parent_id = HiddenField()
    subtask_submit = SubmitField()

class UpdateTaskForm(FlaskForm):
    percent = SelectField('Percent Completed', coerce=int, choices=list_percentages)
    note = TextAreaField('Description')
    status = SelectField('Status', choices=[(list_task_status.index(a), a) for a in list_task_status], coerce=int)
    amount_spent = IntegerField('Amount Spent')
    task_id = HiddenField('Task ID')