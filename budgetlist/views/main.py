from flask import Blueprint, redirect, url_for, abort, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from budgetlist.models import db, User, Project, Task, Period, Department, Permissions, Budget, TaskHistory, \
    SubBudgets, Audit, SubBudgetClass
from functools import wraps
from budgetlist import lm, app
from budgetlist.forms import LoginForm, PeriodForm, DepartmentForm, UserForm, BudgetForm, ProjectForm, \
    TaskForm, SubTaskForm, EditUserForm, UpdateTaskForm, SubBudgetForm, EditSubBudgetForm, ChangePasswordForm
from budgetlist.helpers import list_budget_types, list_priority
from datetime import date
import ldap

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
        if not current_user.is_admin:
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

# decorator to determine if user is not basic
def is_not_basic(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_basic:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def user_status(username):
    user = User.query.filter(User.username == username).one_or_none()

    if user:
        # check status
        return user.status
    return 2

def user_type(username):
    user = User.query.filter(User.username == username).one_or_none()

    if user:
        return user.user_type
    return None

# function redirects to user's home page based on user type
@main.route('/home', methods=['GET'])
@login_required
def home():
    # switch this check to is_super
    if current_user.is_super:
        return redirect(url_for('.budget_overview'))
    else:
        return redirect(url_for('.assigned_tasks'))

@main.route('/overview', methods=['GET'])
@login_required
@is_super
def overview():
    # get active period
    period = Period.query.filter(Period.status==0).first()
    b = Budget.query.filter(Budget.period_id==period.id).first()

    # get budgets
    # budget_types = SubBudgets.query.filter(SubBudgets.budget_id==b.id, SubBudgets.parent_budget==None).all()

    form = ProjectForm()
    form.owner_id.data = current_user.id
    form.priority.choices = [(list_priority.index(a), a) for a in list_priority]

    # get all projects
    projects = Project.query.filter(Project.period_id==period.id).order_by(Project.date_created.desc()).limit(5).all()
    overdue = Project.query.filter(date.today() > Project.end_date, Project.status != 2, Project.period_id==period.id).order_by(Project.date_created.desc()).limit(3).all()
    ongoing = Project.query.filter(Project.status != 2, Project.period_id==period.id).order_by(Project.date_created.desc()).limit(3).all()

    # get count of projects
    completed_count = db.session.query(Project.id).filter(Project.status == 2, Project.period_id==period.id).count()
    # todo add deficit conditions
    ongoing_count = len(Project.query.filter(Project.status != 2, Project.period_id==period.id).all())
    overdue_count = len(Project.query.filter(date.today() > Project.end_date, Project.status != 2, Project.period_id==period.id).all())

    return render_template('overview.html', projects=projects, overdue=overdue, ongoing=ongoing, form=form, completed_count=completed_count,
                           ongoing_count=ongoing_count, overdue_count=overdue_count, budgets=b.main_subs)

@main.route('/all-activities', methods=['GET'])
@is_super
def all_projects():
    period = Period.query.filter(Period.status==0).first()
    projects = Project.query.filter(Project.period_id==period.id).order_by(Project.date_created.desc()).all()

    return render_template('allProjects.html', projects=projects)

@main.route('/activity-detail/<int:id>', methods=['GET', 'POST'])
@is_super
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
            print(project.amount_remaining)
            print(form.allocation.data)
            if project.amount_remaining > form.allocation.data:
                task = Task(form.title.data, form.description.data, form.allocation.data, id, current_user.id,
                            form.priority.data, form.start_date.data, form.end_date.data)
                project.amt_allocated_task += form.allocation.data
                db.session.add(task)
                db.session.add(project)
                db.session.commit()
                for userid in form.assigned_to.data:
                    permission = Permissions(userid, task.id, 0)
                    db.session.add(permission)
                    db.session.commit()
                audit = Audit(current_user.id, "User created a task", 2, 'Task', task.id)
                db.session.add(audit)
                db.session.commit()
                flash('Task has been successfully created', 'success')
            else:
                flash('Total task amount cannot exceed the limit for this activity', 'error')
            return redirect(url_for('.project_detail', id=id))
    elif subform.parent_id.data:
        if subform.validate_on_submit():
            if project.amount_remaining > form.allocation.data:
                task = Task(subform.title.data, subform.description.data, subform.allocation.data, id, current_user.id,
                            subform.priority.data, subform.start_date1.data, subform.end_date1.data)
                task.parent_task = subform.parent_id.data
                project.amt_allocated_task += subform.allocation.data
                db.session.add(task)
                db.session.add(project)
                db.session.commit()
                for userid in form.assigned_to.data:
                    permission = Permissions(userid, task.id, 0)
                    db.session.add(permission)
                    db.session.commit()
                audit = Audit(current_user.id, "User created a task", 2, 'Task', task.id)
                db.session.add(audit)
                db.session.commit()
                flash('Task has been successfully created', 'success')
            else:
                flash('Total task amount cannot exceed the limit for this activity', 'error')
            return redirect(url_for('.project_detail', id=id))
    return render_template('backlogs.html', project=project, form=form, subform=subform)

@main.route('/close-project/<int:id>', methods=['GET', 'POST'])
@is_super
def close_project(id):
    project = Project.query.get(id)
    project.status = 2
    db.session.add(project)

    audit = Audit(current_user.id, "User closed a project", 8, 'Project', project.id)
    db.session.add(audit)
    db.session.commit()

    flash("The activity has been closed", 'success')
    return redirect(url_for('.project_detail', id=project.id))

@main.route('/completed-activities', methods=['GET'])
@is_super
def completed_projects():
    period = Period.query.filter(Period.status==0).first()
    projects = Project.query.filter(Project.status==2, Project.period_id==period.id).order_by(Project.date_created.desc()).all()

    return render_template('completedProjects.html', projects=projects)

@main.route('/overdue-activities', methods=['GET'])
@is_super
def overdue_projects():
    period = Period.query.filter(Period.status==0).first()
    projects = Project.query.filter(date.today() > Project.end_date, Project.status != 2, Project.period_id==period.id).order_by(Project.date_created.desc()).all()

    return render_template('overdueProjects.html', projects=projects)

@main.route('/assigned-tasks', methods=['GET', 'POST'])
@login_required
def assigned_tasks():
    form = UpdateTaskForm()

    if form.validate_on_submit():
        history = TaskHistory()
        history.percent = form.percent.data
        history.task_id = form.task_id.data
        history.owner_id = current_user.id
        history.note = form.note.data

        task = Task.query.get(form.task_id.data)
        task.status = form.status.data

        # contextual updates
        if form.percent.data != 0 and form.percent.data != 100 and form.status.data in [0, 2, 3]:
            task.status = 1
        if form.percent.data == 100:
            task.status = 2

        if form.status.data == 2:
            history.percent = 100

        audit = Audit(current_user.id, "User updated a task", 3, 'Task', task.id)
        db.session.add(audit)
        db.session.add(history)
        db.session.add(task)
        db.session.commit()
        flash('The task has been successfully updated', 'success')

    tasks = Permissions.query.filter(Permissions.user_id==current_user.id).order_by(Permissions.date_created.desc()).all()
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
        if not app.config['USE_LDAP_AUTH']:
            user = User.query.filter(User.username==form.username.data).one_or_none()

            if not user:
                flash('Invalid login credentials', 'error')
            else:
                if user.check_password(form.password.data):
                    login_user(user)
                    audit = Audit(user.id, "User logged in", 0, 'User', user.id)
                    db.session.add(audit)
                    db.session.commit()
                    return redirect(url_for('.home'))
                else:
                    flash('Invalid login credentials', 'error')
        else:
            connect = ldap.initialize(app.config['LDAP_PROVIDER_URL'])
            search_filter = "uid=" + form.username.data + ",dc=example,dc=com"

            try:
                connect.set_option(ldap.OPT_REFERRALS,0)
                res = connect.simple_bind_s(search_filter, form.password.data)
                # check if user exists in our database
                user = User.query.filter(User.username==form.username.data).one_or_none()
                if user and user.status == 0:
                    login_user(user)
                    audit = Audit(user.id, "User logged in", 0, 'User', user.id)
                    db.session.add(audit)
                    db.session.commit()
                    return redirect(url_for('.home'))
                else:
                    flash('You are not authorized to use this portal. Please contact an administrator')
            except ldap.INVALID_CREDENTIALS:
                flash('Invalid Active Directory credentials', 'error')
            except ldap.CONNECT_ERROR:
                flash('Could not connect to Active Directory', 'error')
    return render_template('login.html', form=form)

@main.route('/logout', methods=['GET'])
@login_required
def logout():
    audit = Audit(current_user.id, "User logged out", 0, 'User', current_user.id)
    db.session.add(audit)
    db.session.commit()
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('.login'))

@main.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.set_password(form.password.data)
        db.session.add(current_user)
        db.session.commit()
        flash('Your password has been updated', 'success')
    return render_template('change_password.html', form=form)

# user management
@main.route('/users', methods=['GET'])
@is_admin
def users():
    # get users
    users = User.query.all()

    return render_template('members.html', users=users)

@main.route('/activeUsers', methods=['GET'])
@is_admin
def active_users():
    # get users
    users = User.query.filter(User.status==0).all()

    return render_template('members.html', users=users)

@main.route('/inactiveUsers', methods=['GET'])
@is_admin
def inactive_users():
    # get users
    users = User.query.filter(User.status==1).all()

    return render_template('members.html', users=users)

@main.route('/edit-user/<int:userid>', methods=['GET', 'POST'])
@is_admin
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
        audit = Audit(current_user.id, "User account was updated", 5, 'User', user.id)
        db.session.add(audit)
        db.session.commit()
        flash('The user\'s account status has been updated', 'success')
        return redirect(url_for('.user_settings'))

    form.department.data = (user.department_id if user.department_id else 0)
    form.user_type.data = user.account_type

    users = User.query.order_by(User.date_created.asc()).all()
    return render_template('edit_user.html', user=user, users=users, form=form)

@main.route('/toggle_user_status/<int:action>/<int:userid>', methods=['GET'])
@is_admin
def toggle_user_status(action, userid):
    # check if action is valid
    if action in [0, 1]:
        # check if user exists
        user = User.query.get(userid)
        if user:
            user.status = action
            db.session.add(user)
            db.session.commit()

            if action == 0:
                audit = Audit(current_user.id, "User account was activated", 5, 'User', user.id)
            else:
                audit = Audit(current_user.id, "User account was deactivated", 5, 'User', user.id)
            db.session.add(audit)
            db.session.commit()
            flash('The user\'s account status has been updated', 'success')
            return redirect(url_for('.user_settings'))
        else:
            abort(404)
    else:
        abort(400)

@main.route('/toggle_ldap_status/<int:action>/<username>', methods=['GET'])
@is_admin
def toggle_ldap_status(action, username):
    # check if action is valid
    if action in [0, 1]:
        # check if user exists
        user = User.query.filter(User.username == username).one_or_none()
        if user:
            user.status = action
            db.session.add(user)
            db.session.commit()

            if action == 0:
                audit = Audit(current_user.id, "User account was activated", 5, 'User', user.id)
            else:
                audit = Audit(current_user.id, "User account was deactivated", 5, 'User', user.id)
            db.session.add(audit)
            db.session.commit()
            flash('The user\'s account status has been updated', 'success')
            return redirect(url_for('.user_settings'))
        else:
            flash('Invalid user account', 'error')
            return redirect(url_for('.user_settings'))
    else:
        flash('Invalid action', 'error')
        return redirect(url_for('.user_settings'))

# settings
@main.route('/settings', methods=['GET', 'POST'])
@is_admin
def settings():
    return redirect(url_for('.periods'))

@main.route('/periods', methods=['GET', 'POST'])
@is_admin
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
        for i in SubBudgetClass.query.all():
            sub_budget = SubBudgets()
            sub_budget.name = i.sub_budget_class
            sub_budget.created_by = current_user.id
            sub_budget.parent_budget = None
            sub_budget.sub_budget_type = i.id

            budget.main_subs.append(sub_budget)

        period.budget = budget

        db.session.add(period)
        db.session.commit()

        audit = Audit(current_user.id, "Period was created", 6, 'Period', period.id)
        db.session.add(audit)
        baudit = Audit(current_user.id, "Budget for period," + period.name + " was created", 4, 'Budget', budget.id)
        db.session.add(baudit)
        db.session.commit()

        flash('The period has been successfully created', 'success')

        # if period.status == 0:
        #    return redirect(url_for('.manage_budget'))
    periods = Period.query.order_by(Period.date_created.asc()).all()
    return render_template('periodSettings.html', form=form, periods=periods)

@main.route('/activate-period/<int:id>', methods=['GET'])
@is_admin
def activate_period(id):
    period = Period.query.get(id)
    if period:
        period.status = 0
        db.session.add(period)
        db.session.commit()

        db.session.query(Period).filter(Period.id != id).update({Period.status: 1})
        audit = Audit(current_user.id, "Period was activated", 6, 'Period', period.id)
        db.session.add(audit)
        db.session.commit()
        flash('The period has been activated', 'success')
        return redirect(url_for('.periods'))
    return redirect(url_for('.periods'))

@main.route('/departments', methods=['GET', 'POST'])
@is_admin
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
                audit = Audit(current_user.id, "Department was updated", 7, 'Department', dep.id)
                db.session.add(audit)
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
                audit = Audit(current_user.id, "Department was created", 7, 'Department', dep.id)
                db.session.add(audit)
                db.session.commit()
                flash('The department has been successfully created', 'success')
    departments = Department.query.all()
    return render_template('departmentSetting.html', form=form, departments=departments)

@main.route('/edit-department/<int:id>', methods=['GET', 'POST'])
@is_admin
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
@is_admin
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
@is_admin
def user_settings():
    if not app.config['USE_LDAP_AUTH']:
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
    else:
        connect = ldap.initialize(app.config['LDAP_PROVIDER_URL'])
        try:
            connect.set_option(ldap.OPT_REFERRALS, 0)
            criteria = "(objectClass=person)"
            attributes = ['uid', 'cn', 'mail']
            result = connect.search_s(app.config['LDAP_BIND_DN'], ldap.SCOPE_SUBTREE, criteria, attributes)
            users_stat = [entry for dn, entry in result if isinstance(entry, dict)]
            users = []
            for row in users_stat:
                user_dict = {}
                print row
                user_dict['uid'] = row['uid'][0] if 'uid' in row else None
                user_dict['cn'] = row['cn'][0] if 'cn' in row else None
                user_dict['mail'] = row['mail'][0] if 'mail' in row else None
                user_dict['status'] = user_status(row['uid'][0]) if 'uid' in row else None
                user_dict['type'] = user_type(row['uid'][0]) if 'uid' in row else None
                users.append(user_dict)
            connect.unbind()
        except ldap.CONNECT_ERROR:
            flash('Could not connect to Active Directory', 'error')
        return render_template('ldap_user_setting.html', users=users)

@main.route('/sub-budget-setup', methods=['GET'])
@is_admin
def sub_budget_settings():
    subs = SubBudgetClass.query.order_by(SubBudgetClass.id.asc()).all()
    return render_template('sub_budget_settings.html', subs=subs)

@main.route('/toggle-budget-movable-status/<int:sub>/<int:action>', methods=['GET'])
@is_admin
def toggle_budget_movable_status(sub, action):
    budget_class = SubBudgetClass.query.get(sub)

    if budget_class:
        budget_class.movable = action
        db.session.add(budget_class)
        db.session.commit()

        if action == 0:
            audit = Audit(current_user.id, "User marked budget as movable", 11, 'Sub Budget Class', budget_class.id)
        else:
            audit = Audit(current_user.id, "User marked budget as fixed", 11, 'Sub Budget Class', budget_class.id)
        db.session.add(audit)
        db.session.commit()

        flash('The budget has been updated successfully', 'success')
    else:
        flash('This budget does not exist', 'error')
    return redirect(url_for('.sub_budget_settings'))

@main.route('/edit-ldap-access-level/<username>/<int:type>', methods=['GET', 'POST'])
@is_admin
def edit_ldap_access(username, type):
    # check if user exists
    user = User.query.filter(User.username == username).one_or_none()
    if user:
        user.account_type = type
        db.session.add(user)
        db.session.commit()

        # for audit
        audit = Audit(current_user.id, "User\'s account type was updated", 5, 'User', user.id)
        db.session.add(audit)
        db.session.commit()
        flash('This user\'s account type has been updated', 'success')
    else:
        flash('This user does not exist', 'error')
    return redirect(url_for('.user_settings'))

@main.route('/grant-ldap-access/<username>/<int:type>', methods=['GET', 'POST'])
@is_admin
def grant_ldap_access(username, type):
    # check if user exists
    user = User.query.filter(User.username == username).one_or_none()
    if not user:
        # get user details from ldap
        connect = ldap.initialize(app.config['LDAP_PROVIDER_URL'])
        try:
            connect.set_option(ldap.OPT_REFERRALS, 0)
            # searchFilter = "(&(gidNumber=123456)(objectClass=posixAccount))"
            criteria = "(&(objectClass=person)(uid=" + username + "))"
            attributes = ['uid', 'cn', 'mail']
            result = connect.search_s(app.config['LDAP_BIND_DN'], ldap.SCOPE_SUBTREE, criteria, attributes)
            ldap_user = [entry for dn, entry in result if isinstance(entry, dict)]
            if len(ldap_user) == 1:
                # create user
                user = User(ldap_user[0]['cn'][0], ldap_user[0]['uid'][0], ldap_user[0]['mail'][0], 'password', 1, type)
                db.session.add(user)
                db.session.commit()

                # for audit
                audit = Audit(current_user.id, "LDAP user was granted access", 5, 'User', user.id)
                db.session.add(audit)
                db.session.commit()
                flash('The user has been granted access', 'success')
            else:
                flash('Invalid number of users in AD', 'error')
        except ldap.CONNECT_ERROR:
            flash('Could not connect to Active Directory', 'error')
    else:
        flash('This user already exists', 'error')
    return redirect(url_for('.user_settings'))

@main.route('/budgets', methods=['GET', 'POST'])
@is_super
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
@is_super
def manage_budget():
    # get budget
    period = Period.query.filter(Period.status==0).first()
    budget = period.budget

    form = SubBudgetForm()
    editform = EditSubBudgetForm()
    if form.validate_on_submit() and (form.sub_budget_id.data == '0' or form.sub_budget_id.data == ""):
        # new budget
        sub = SubBudgets()
        sub.name = form.name.data
        sub.allocation = form.allocation.data
        sub.parent_budget = form.parent_id.data
        sub.budget_id = budget.id
        sub.created_by = current_user.id
        db.session.add(sub)
        db.session.commit()

        audit = Audit(current_user.id, "User created a sub budget", 9, 'Sub Budget', sub.id)
        db.session.add(audit)
        db.session.commit()

        flash('The sub budget has been successfully created', 'success')
        return redirect(url_for('.manage_budget'))
    elif editform.validate_on_submit() and editform.sub_budget_id.data != '0' and editform.sub_budget_id.data != "":
        # edit budget
        sub = SubBudgets.query.get(editform.sub_budget_id.data)
        if editform.name.data:
            sub.name = editform.name.data
        sub.allocation = editform.allocation.data
        db.session.add(sub)
        db.session.commit()

        audit = Audit(current_user.id, "User edited a sub budget", 10, 'Sub Budget', sub.id)
        db.session.add(audit)
        db.session.commit()

        flash('The sub budget has been successfully updated', 'success')
        return redirect(url_for('.manage_budget'))

    return render_template('manage_budget.html', budget=budget, form=form, editform=editform)

@main.route('/budget-transfer/<int:bfrom>/<int:bto>/<amount>', methods=['GET'])
@is_super
def budget_transfer(bfrom, bto, amount):
    budget_from = SubBudgets.query.get(bfrom)
    budget_to = SubBudgets.query.get(bto)
    amount = int(amount)

    if not budget_from or not budget_to:
        flash('One or more budgets does not exist', 'error')
    elif budget_from.amount_remaining < amount:
        flash('Amount to be transferred exceeds budget balance', 'error')
    else:
        budget_from.allocation -= amount
        budget_to.allocation += amount
        db.session.add(budget_from)
        db.session.add(budget_to)
        db.session.commit()

        audit = Audit(current_user.id, "User transferred %d from %s to %s" % (amount, budget_from.name, budget_to.name), 10, 'Sub Budget', budget_from.id)
        db.session.add(audit)
        db.session.commit()

        flash('Budget transfer has been successfully carried out', 'success')
    return redirect(url_for('.manage_budget'))

@main.route('/toggle-budget/<int:id>/<int:action>', methods=['GET'])
@is_super
def toggle_budget_status(id, action):
    sub = SubBudgets.query.get(id)
    sub.status = action
    db.session.add(sub)
    db.session.commit()

    audit = Audit(current_user.id, "User updated sub budget status", 10, 'Sub Budget', sub.id)
    db.session.add(audit)
    db.session.commit()

    flash('The sub budget has been successfully updated', 'success')
    return redirect(url_for('.manage_budget'))

@main.route('/budget-details', methods=['GET', 'POST'])
@is_super
def budget_details():
    # get budget
    period = Period.query.filter(Period.status==0).first()
    budget = period.budget

    periods = Period.query.all()

    return render_template('budget-details.html', budget=budget, periods=periods)

@main.route('/dashboard', methods=['GET', 'POST'])
@is_super
def budget_overview():
    # get budget
    period = Period.query.filter(Period.status==0).first()
    budget = period.budget

    return render_template('budgets.html', budget=budget)

@main.route('/audit', methods=['GET', 'POST'])
@is_not_basic
def audit():
    audits = Audit.query.order_by(Audit.date_created.desc()).all()
    return render_template('audit.html', audits=audits)

# error handling
@main.app_errorhandler(404)
def error_not_found(e):
    return render_template('error.html', error=404), 404

@main.app_errorhandler(403)
def error_not_authorized(e):
    return render_template('error.html', error=403), 403

@main.route('/ldap-login', methods=['GET', 'POST'])
def ldap_login():
    if app.config['USE_LDAP_AUTH']:
        username ='einstein'
        connect = ldap.initialize(app.config['LDAP_PROVIDER_URL'])
        search_filter = "uid=" + username + ",dc=example,dc=com"
        #user_dn = "ou=scientists,dc=example,dc=com"

        try:
            connect.set_option(ldap.OPT_REFERRALS,0)
            res = connect.simple_bind_s(search_filter, "password")
            print res
            criteria = "(objectClass=person)"
            attributes = ['uid', 'cn', 'sn', 'mail']
            result = connect.search_s(app.config['LDAP_BIND_DN'], ldap.SCOPE_SUBTREE, criteria, attributes)
            results = [entry for dn, entry in result if isinstance(entry, dict)]
            print results
            connect.unbind()
            return "Successful binding"
        except ldap.INVALID_CREDENTIALS:
            print "Invalid credentials"
        finally:
            print "End"

@main.route('/prepare-existsing-budgets', methods=['GET'])
def prep_budgets():
    mains = Budget.query.all()

    for m in mains:
        # get subs
        for s in m.main_subs:
            # get child_budgets
            for a in s.child_budgets:
                a.sub_budget_type = s.sub_budget_type
                #print a.sub_budget_type
                db.session.add(a)
                db.session.commit()
                for b in a.child_budgets:
                    b.sub_budget_type = s.sub_budget_type
                    db.session.add(b)
                    db.session.commit()
                    for c in b.child_budgets:
                        c.sub_budget_type = s.sub_budget_type
                        db.session.add(c)
                        db.session.commit()
                        for d in c.child_budgets:
                            d.sub_budget_type = s.sub_budget_type
                            db.session.add(d)
                            db.session.commit()