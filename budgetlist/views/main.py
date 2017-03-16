from flask import Blueprint, redirect, url_for, abort, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from budgetlist.models import db, User, Project, Task, Company, Period, Department, Permissions, Budget, TaskHistory, SubBudgets
from functools import wraps
from budgetlist import lm
from budgetlist.forms import LoginForm, CompanyForm, PeriodForm, DepartmentForm, UserForm, BudgetForm, ProjectForm, \
    TaskForm, SubTaskForm, EditUserForm, UpdateTaskForm, SubBudgetForm, EditSubBudgetForm
from budgetlist.helpers import list_budget_types, list_priority
from datetime import date

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
        return redirect(url_for('.budget_overview'))

@main.route('/overview', methods=['GET'])
@login_required
def overview():
    # get active period
    period = Period.query.filter(Period.status==0).first()
    b = Budget.query.filter(Budget.period_id==period.id).first()

    # get budgets
    budget_types = SubBudgets.query.filter(SubBudgets.budget_id==b.id, SubBudgets.parent_budget==None).all()

    form = ProjectForm()
    form.owner_id.data = current_user.id
    form.priority.choices = [(list_priority.index(a), a) for a in list_priority]

    # get all projects
    projects = Project.query.order_by(Project.date_created.desc()).limit(5).all()
    overdue = Project.query.filter(date.today() > Project.end_date, Project.status != 2).order_by(Project.date_created.desc()).limit(3).all()
    ongoing = Project.query.filter(Project.status == 1).order_by(Project.date_created.desc()).limit(3).all()

    # get count of projects
    completed_count = db.session.query(Project.id).filter(Project.status == 2).count()
    # todo add deficit conditions
    deficit_count = db.session.query(Project.id).filter(Project.amount_remaining < 0).count()
    overdue_count = len(overdue)

    return render_template('overview.html', projects=projects, overdue=overdue, ongoing=ongoing, form=form, completed_count=completed_count,
                           deficit_count=deficit_count, overdue_count=overdue_count, budget_types=budget_types)

@main.route('/all-projects', methods=['GET'])
def all_projects():
    projects = Project.query.order_by(Project.date_created.desc()).all()

    return render_template('allProjects.html', projects=projects)

@main.route('/project-detail/<int:id>', methods=['GET', 'POST'])
def project_detail(id):
    project = Project.query.get(id)
    form = TaskForm()
    form.assigned_to.choices = [(a.id, a.full_name) for a in User.query.all()]
    form.priority.choices = [(list_priority.index(a), a) for a in list_priority]

    subform = SubTaskForm()
    subform.assigned_to.choices = [(a.id, a.full_name) for a in User.query.all()]
    subform.priority.choices = [(list_priority.index(a), a) for a in list_priority]

    if form.task_submit.data:
        if form.validate_on_submit():
            task = Task(form.title.data, form.description.data, form.allocation.data, id, current_user.id,
                        form.priority.data, form.start_date.data, form.end_date.data)
            db.session.add(task)
            db.session.commit()
            permission = Permissions(current_user.id, task.id, 0)
            db.session.add(permission)
            db.session.commit()
            flash('Task has been successfully created', 'success')
    elif subform.parent_id.data:
        if subform.validate_on_submit():
            task = Task(subform.title.data, subform.description.data, subform.allocation.data, id, current_user.id,
                        subform.priority.data, subform.start_date.data, subform.end_date.data)
            task.parent_task = subform.parent_id.data
            db.session.add(task)
            db.session.commit()
            permission = Permissions(current_user.id, task.id, 0)
            db.session.add(permission)
            db.session.commit()
            flash('Task has been successfully created', 'success')
    

    return render_template('backlogs.html', project=project, form=form, subform=subform)

@main.route('/completed-projects', methods=['GET'])
def completed_projects():
    projects = Project.query.filter(Project.status==2).order_by(Project.date_created.desc()).all()

    return render_template('completedProjects.html', projects=projects)

@main.route('/overdue-projects', methods=['GET'])
def overdue_projects():
    projects = Project.query.filter(date.today() > Project.end_date, Project.status != 2).order_by(Project.date_created.desc()).all()

    return render_template('overdueProjects.html', projects=projects)

@main.route('/assigned-tasks', methods=['GET', 'POST'])
def assigned_tasks():
    form = UpdateTaskForm()

    if form.validate_on_submit():
        history = TaskHistory()
        history.percent = form.percent.data
        history.task_id = form.task_id.data
        history.owner_id = current_user.id
        history.note = form.note.data
        history.status = form.status.data

        if form.amount_spent.data:
            history.amount_spent = form.amount_spent.data

        # contextual updates
        if form.percent.data != 0 and form.percent.data != 100 and form.status.data in [0, 2, 3]:
            history.status = 1
        if form.percent.data == 100:
            history.status = 2

        if form.status.data == 2:
            history.percent = 100

        db.session.add(history)

        # update task status
        task = Task.query.get(history.task_id)
        task.status = history.status
        db.session.add(task)
        db.session.commit()
        flash('The task has been successfully updated', 'success')

    tasks = Permissions.query.filter(Permissions.user_id==current_user.id).all()
    return render_template('assigned.html', tasks=tasks, form=form)

# login function
@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
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

@main.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('.login'))

@main.route('/change-password', methods=['GET', 'POST'])
def change_password():

    return render_template('change_password.html')

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

@main.route('/edit-user/<int:userid>', methods=['GET', 'POST'])
def edit_user(userid):
    # get users
    user = User.query.get(userid)

    form = EditUserForm()
    form.department.choices = [(a.id, a.name) for a in Department.query.all()]

    if form.validate_on_submit():
        user.username = form.username.data
        user.full_name = form.full_name.data
        user.email = form.email.data
        user.account_type = form.user_type.data
        user.department_id = form.department.data

        if form.password.data:
            user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash('The user\'s account status has been updated', 'success')
        return redirect(url_for('.user_settings'))

    form.department.data = (user.department_id if user.department_id else 0)
    form.user_type.data = user.account_type

    users = User.query.order_by(User.date_created.asc()).all()
    return render_template('edit_user.html', user=user, users=users, form=form)

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
            return redirect(url_for('.user_settings'))
        else:
            abort(404)
    else:
        abort(400)


# settings
@main.route('/settings', methods=['GET', 'POST'])
def settings():
    return redirect(url_for('.periods'))
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
        # check if period already exists
        check = Period.query.all()

        period = Period()
        period.name = form.name.data
        period.start_date = form.start_date.data
        period.end_date = form.end_date.data
        if len(check) > 0:
            period.status = 1
        else:
            period.status = 0

        # create budget for period
        budget = Budget()
        budget.name = 'Budget'

        # add sub budgets
        for i in list_budget_types:
            sub_budget = SubBudgets()
            sub_budget.name = i
            sub_budget.created_by = current_user.id
            sub_budget.parent_budget = None

            budget.main_subs.append(sub_budget)

        period.budget = budget

        db.session.add(period)
        db.session.commit()
        flash('The period has been successfully created', 'success')

        # if period.status == 0:
        #    return redirect(url_for('.manage_budget'))
    periods = Period.query.order_by(Period.date_created.asc()).all()
    return render_template('periodSettings.html', form=form, periods=periods)

@main.route('/activate-period/<int:id>', methods=['GET'])
def activate_period(id):
    period = Period.query.get(id)
    if period:
        period.status = 0
        db.session.add(period)
        db.session.commit()

        db.session.query(Period).filter(Period.id != id).update({Period.status: 1})
        db.session.commit()
        flash('The period has been activated', 'success')
        return redirect(url_for('.manage_budget'))
    return redirect(url_for('.periods'))

@main.route('/departments', methods=['GET', 'POST'])
def departments():
    form = DepartmentForm()

    if form.validate_on_submit():
        if form.depart_id.data:
            # check if department already exists
            chk = Department.query.filter(Department.name == form.name.data, Department.id != form.depart_id.data).first()
            if chk:
                flash('This department already exists', 'error')
            else:
                dep = Department.query.get(form.depart_id.data)
                dep.name = form.name.data

                db.session.add(dep)
                db.session.commit()
                flash('The department has been successfully updated', 'success')
        else:
            # check if department already exists
            chk = Department.query.filter(Department.name == form.name.data).first()
            if chk:
                flash('This department already exists', 'error')
            else:
                dep = Department()
                dep.name = form.name.data

                db.session.add(dep)
                db.session.commit()
                flash('The department has been successfully created', 'success')
    departments = Department.query.all()
    return render_template('departmentSetting.html', form=form, departments=departments)

@main.route('/edit-department/<int:id>', methods=['GET', 'POST'])
def edit_department(id):
    dept = Department.query.get(id)

    form = DepartmentForm()
    if form.validate_on_submit():
        dept.name = form.name.data

        db.session.add(dept)
        db.session.commit()
        flash('The department has been successfully updated', 'success')
        return redirect(url_for('.departments'))
    departments = Department.query.all()
    return render_template('edit_department.html', form=form, dept=dept, departments=departments)

@main.route('/create-user', methods=['GET', 'POST'])
def create_user():
    form = UserForm()
    form.department.choices = [(a.id, a.name) for a in Department.query.all()]

    if form.validate_on_submit():
        user = User(form.full_name.data, form.username.data, form.email.data, form.password.data, form.department.data,
                form.user_type.data)
        db.session.add(user)
        db.session.commit()
        flash('The user has been successfully created', 'success')
    return render_template('userSetting.html', form=form)

@main.route('/user-settings', methods=['GET', 'POST'])
def user_settings():
    form = UserForm()
    form.department.choices = [(a.id, a.name) for a in Department.query.all()]

    if form.validate_on_submit():
        if form.user_id.data:
            # check if username or email already exists
            chk = User.query.filter(User.username == form.username.data, User.id != form.user_id.data).first()
            chk2 = User.query.filter(User.email == form.email.data, User.id != form.user_id.data).first()

            if chk or chk2:
                if chk:
                    flash('This username already exists', 'error')
                if chk2:
                    flash('This email already exists', 'error')
            else:
                user = User.query.get(form.user_id.data)
                # assign values
                user.username = form.username.data
                user.full_name = form.full_name.data
                user.email = form.email.data
                user.department_id = form.department.data
                user.account_type = form.user_type.data

                if form.password.data:
                    user.set_password(form.password.data)

                db.session.add(user)
                db.session.commit()
                flash('The user\'s account has been successfully updated', 'success')
        else:
            # check if username or email already exists
            chk = User.query.filter(User.username == form.username.data).first()
            chk2 = User.query.filter(User.email == form.email.data).first()

            if chk or chk2:
                if chk:
                    flash('This username already exists', 'error')
                if chk2:
                    flash('This email already exists', 'error')
            else:
                user = User(form.full_name.data, form.username.data, form.email.data, form.password.data, form.department.data,
                        form.user_type.data)
                db.session.add(user)
                db.session.commit()
                flash('The user has been successfully created', 'success')
    users = User.query.order_by(User.date_created.asc()).all()
    return render_template('user_setting.html', form=form, users=users)

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
    budgets = Budget.query.all()
    return render_template('budgetSetting.html', form=form, budgets=budgets)

@main.route('/manage-budget', methods=['GET', 'POST'])
def manage_budget():
    # get budget
    period = Period.query.filter(Period.status==0).first()
    budget = period.budget

    form = SubBudgetForm()
    if form.validate_on_submit() and form.sub_budget_id.data == '0':
        # new budget
        sub = SubBudgets()
        sub.name = form.name.data
        sub.allocation = form.allocation.data
        sub.parent_budget = form.parent_id.data
        sub.budget_id = budget.id
        sub.created_by = current_user.id
        db.session.add(sub)
        db.session.commit()
        flash('The sub budget has been successfully created', 'success')

    editform = EditSubBudgetForm()
    if editform.validate_on_submit() and editform.sub_budget_id.data != '0':
        # edit budget
        sub = SubBudgets.query.get(editform.sub_budget_id.data)
        sub.name = editform.name.data
        sub.allocation = editform.allocation.data
        db.session.add(sub)
        db.session.commit()
        flash('The sub budget has been successfully updated', 'success')

    return render_template('manage_budget.html', budget=budget, form=form, editform=editform)

@main.route('/dashboard', methods=['GET', 'POST'])
def budget_overview():
    # get budget
    period = Period.query.filter(Period.status==0).first()
    budget = period.budget

    form = SubBudgetForm()
    if form.validate_on_submit():
        if not form.sub_budget_id.data or form.sub_budget_id.data == '':
            # new budget
            sub = SubBudgets()
            sub.name = form.name.data
            sub.allocation = form.allocation.data
            sub.parent_budget = form.parent_id.data
            sub.budget_id = budget.id
            sub.created_by = current_user.id
            db.session.add(sub)
            db.session.commit()
            flash('The sub budget has been successfully created', 'success')
        else:
            # edit budget
            sub = SubBudgets.query.get(form.sub_budget_id.data)
            sub.name = form.name.data
            sub.allocation = form.allocation.data
            db.session.add(sub)
            db.session.commit()
            flash('The sub budget has been successfully updated', 'success')

    return render_template('budgets.html', budget=budget, form=form)

# error handling
@main.app_errorhandler(404)
def error_not_found(e):
    return render_template('error.html'), 404