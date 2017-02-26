from flask import Blueprint, redirect, url_for, abort, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from budgetlist.models import db, User, Project, Task, Company, Period, Department, Permissions, Budget
from functools import wraps
from budgetlist import lm
from budgetlist.forms import LoginForm, CompanyForm, PeriodForm, DepartmentForm, UserForm, BudgetForm, ProjectForm
from budgetlist.helpers import list_budget_types, list_priority

main = Blueprint('main', __name__)
lm.login_view = '.login'
lm.blueprint_login_views = '.login'

# login manager user loader
@lm.user_loader
def load_user(userid):
    return User.query.filter(User.id == userid).first_or_404()

# decorator to determine if user is admin
def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# decorator to determine if user is super
def is_super(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_super:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# function redirects to user's home page based on user type
@main.route('/home', methods=['GET'])
@login_required
def home():
    # switch this check to is_super
    if current_user.is_basic:
        return redirect(url_for('.assigned_tasks'))
    else:
        return redirect(url_for('.overview'))

@main.route('/overview', methods=['GET'])
@login_required
def overview():
    form = ProjectForm()
    form.priority.choices = [(list_priority.index(a), a) for a in list_priority]
    form.budget_id.choices = [(a.id, a.name) for a in Budget.query.all()]

    # get all projects
    projects = Project.query.order_by(Project.date_created.desc()).limit(5).all()
    ongoing = Project.query.order_by(Project.date_created.desc()).limit(3).all()
    overdue = Project.query.filter().order_by(Project.date_created.desc()).limit(3).all()

    return render_template('overview.html', projects=projects, overdue=overdue, ongoing=ongoing, form=form)

@main.route('/all-projects', methods=['GET'])
def all_projects():
    projects = Project.query.order_by(Project.date_created.desc()).all()

    return render_template('allProjects.html', projects=projects)

@main.route('/project-detail/<int:id>', methods=['GET'])
def project_detail(id):
    pass

@main.route('/completed-projects', methods=['GET'])
def completed_projects():
    projects = Project.query.filter(Project.status==2).order_by(Project.date_created.desc()).all()

    return render_template('completedProjects.html', projects=projects)

@main.route('/overdue-projects', methods=['GET'])
def overdue_projects():
    projects = Project.query.filter().order_by(Project.date_created.desc()).all()

    return render_template('overdueProjects.html', projects=projects)

@main.route('/assigned-tasks', methods=['GET'])
def assigned_tasks():
    tasks = Permissions.query.filter(Permissions.user_id==current_user.id).all()

    return render_template('assigned.html', tasks=tasks)

# login function
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username==form.username.data).one_or_none()

        if not user:
            flash('Invalid login credentials', 'error')
        else:
            if user.check_password(form.password.data):
                login_user(user)
                return redirect(url_for('.home'))
            else:
                flash('Invalid login credentials', 'error')
    return render_template('login.html', form=form)


# user management
@main.route('/users', methods=['GET'])
def users():
    # get users
    users = User.query.all()

    return render_template('members.html', users=users)

@main.route('/activeUsers', methods=['GET'])
def active_users():
    # get users
    users = User.query.filter(User.status==0).all()

    return render_template('members.html', users=users)

@main.route('/inactiveUsers', methods=['GET'])
def inactive_users():
    # get users
    users = User.query.filter(User.status==1).all()

    return render_template('members.html', users=users)

@main.route('/edit-user/<int:userid>', methods=['GET'])
def edit_user(userid):
    # get users
    users = User.query.filter(User.account_type==1).all()

    return render_template('members.html', users=users)

@main.route('/toggle_user_status/<int:action>/<int:userid>', methods=['GET'])
def toggle_user_status(action, userid):
    # check if action is valid
    if action in [0, 1]:
        # check if user exists
        user = User.query.get(userid)
        if user:
            user.status = action
            db.session.add(user)
            db.session.commit()
            flash('The user\'s account status has been updated', 'success')
            return redirect(url_for('.users'))
        else:
            abort(404)
    else:
        abort(400)


# settings
@main.route('/settings', methods=['GET', 'POST'])
def settings():
    company = Company.query.first()
    form = CompanyForm()
    if company:
        if form.validate_on_submit():
            company.name = form.name.data
            company.address = form.address.data
            company.website = form.website.data
            db.session.add(company)
            db.session.commit()
            flash('Company details have been successfully updated', 'success')
        return render_template('settings.html', company=company, form=form)
    else:
        c = Company()
        c.name = 'Test Company'
        c.address = 'Test Address'
        c.website = 'www.test.com'
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('.settings'))

@main.route('/periods', methods=['GET', 'POST'])
def periods():
    form = PeriodForm()
    if form.validate_on_submit():
        period = Period()
        period.name = form.name.data
        period.start_date = form.start_date.data
        period.end_date = form.end_date.data
        period.status = 0
        db.session.add(period)
        db.session.commit()
        flash('The period has been successfully created', 'success')
    return render_template('periodSettings.html', form=form)

@main.route('/departments', methods=['GET', 'POST'])
def departments():
    form = DepartmentForm()

    if form.validate_on_submit():
        dep = Department()
        dep.name = form.name.data

        db.session.add(dep)
        db.session.commit()
        flash('The department has been successfully created', 'success')
    return render_template('departmentSetting.html', form=form)

@main.route('/create-user', methods=['GET', 'POST'])
def create_user():
    form = UserForm()
    form.department.choices = [(a.id, a.name) for a in Department.query.all()]

    if form.validate_on_submit():
        user = User(form.full_name.data, form.username.data, form.email.data, form.password.data,
                form.user_type.data)
        db.session.add(user)
        db.session.commit()
        flash('The user has been successfully created', 'success')
    return render_template('userSetting.html', form=form)

@main.route('/budgets', methods=['GET', 'POST'])
def budgets():
    form = BudgetForm()
    form.period.choices = [(a.id, a.name) for a in Period.query.all()]
    form.budget_type.choices = [(list_budget_types.index(a), a) for a in list_budget_types]

    if form.validate_on_submit():
        budget = Budget()
        budget.name = form.name.data
        budget.period_id = form.period.data
        budget.allocation = form.allocation.data
        budget.budget_type = form.budget_type.data
        db.session.add(budget)
        db.session.commit()
        flash('The budget has been successfully created', 'success')
    return render_template('budgetSetting.html', form=form)

# error handling
@main.app_errorhandler(404)
def error_not_found(e):
    return render_template('error.html'), 404