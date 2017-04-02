from flask import Blueprint, jsonify, abort, make_response, request
from budgetlist.models import db, User, Project, Task, SubBudgets, Department, Audit, Period, SubBudgets

api = Blueprint('api', __name__)

@api.route('/v1.0/budgets/get/<int:budget_id>', methods=['GET'])
def get_budget(budget_id):
    budget = SubBudgets.query.get(budget_id)
    if not budget:
        abort(404)
    return jsonify(sub=budget.serialize)

@api.route('/v1.0/budgets/children/<int:budget_id>', methods=['GET'])
def get_budget_children(budget_id):
    budget = SubBudgets.query.get(budget_id)
    if not budget:
        abort(404)
    return jsonify(subs=budget.sub_budgets)

@api.route('/v1.0/budgets/create-sub', methods=['POST'])
def add_sub_budget():
    sub = SubBudgets()
    sub.allocation = request.json["allocation"]
    sub.name = request.json["name"]
    sub.parent_budget = request.json["budget_id"]
    sub.created_by = request.json["owner_id"]

    db.session.add(sub)
    db.session.commit()

    audit = Audit(sub.created_by, "User created a sub budget", 9, 'Sub Budget', sub.id)
    db.session.add(audit)
    db.session.commit()

    return jsonify({'status': 'success'}), 201

@api.route('/v1.0/users/get/<int:userid>', methods=['GET'])
def get_user(userid):
    user = User.query.get(userid)
    if not user:
        abort(404)
    return jsonify(user.serialize)

@api.route('/v1.0/departments/get/<int:department_id>', methods=['GET'])
def get_department(department_id):
    depart = Department.query.get(department_id)
    if not depart:
        abort(404)
    return jsonify(depart.serialize)

@api.route('/v1.0/users', methods=['GET'])
@api.route('/v1.0/users/<int:limit>', methods=['GET'])
def get_users(limit=False):
    if limit:
        users = User.query.limit(limit).all()
    else:
        users = User.query.all()
    if not users:
        abort(404)
    return jsonify(users=[i.serialize for i in users])


@api.route('/v1.0/users', methods=['POST'])
def create_user():
    if not request.json or 'full_name' not in request.json or 'username' not in request.json or 'email' not in \
            request.json or 'password' not in request.json:
        abort(400)

    user = User.query.filter(User.email==request.json['email']).all()
    if user:
        return jsonify({'error': 'Email already exists'}), 201

    user = User.query.filter(User.username==request.json['username']).all()
    if user:
        return jsonify({'error': 'Username already exists'}), 201

    user = User(request.json['full_name'], request.json['username'], request.json['email'], request.json['password'],
                request.json['account_type'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'status': 'success'}), 201


@api.route('/v1.0/users/login', methods=['POST'])
def login():
    if not request.json or 'username' not in request.json or 'password' not in request.json:
        abort(400)
    user = User.query.filter(User.username==request.json['username']).one_or_none()

    if not user:
        return jsonify({'error': 'User does not exist'}), 201

    if not user.check_password(request.json['password']):
        return jsonify({'error': 'Invalid login credentials'}), 201
    return jsonify({'status': 'Success', 'userid': user.id}), 201


@api.route('/v1.0/projects/create', methods=['POST'])
def create_project():

    if not request.json or 'title' not in request.json or 'description' not in request.json or 'budget_limit' not in \
            request.json or 'start_date' not in request.json or 'end_date' not in request.json or \
            'owner_id' not in request.json:
        abort(400)

    budget = SubBudgets.query.get(request.json['budget_id'])
    if budget.amount_remaining < int(request.json['budget_limit']):
        abort(400)

    period = Period.query.filter(Period.status==0).first()
    project = Project(request.json['title'], request.json['description'], request.json['budget_limit'], request.json['budget_id'],
                      request.json['start_date'], request.json['end_date'], request.json['priority'], request.json['owner_id'], period.id)
    budget.amt_allocated_project += int(request.json['budget_limit'])

    db.session.add(budget)
    db.session.add(project)
    db.session.commit()

    audit = Audit(request.json['owner_id'], "Activity was created", 1, 'Project', project.id)
    db.session.add(audit)
    db.session.commit()

    return jsonify({'status': 'success', 'project': project.serialize}), 201


@api.route('/v1.0/projects/get/<int:projectid>', methods=['GET'])
def get_project(projectid):
    project = Project.query.get(projectid)
    if not project:
        abort(404)
    return jsonify(project=project.serialize)


@api.route('/v1.0/projects', methods=['GET'])
@api.route('/v1.0/projects/<int:limit>', methods=['GET'])
def get_projects(limit=False):
    if limit:
        projects = Project.query.order_by(Project.date_created.desc()).limit(limit).all()
    else:
        projects = Project.query.order_by(Project.date_created.desc()).all()
    if not projects:
        abort(404)
    return jsonify(projects=[i.serialize for i in projects])


@api.route('/v1.0/projects/ongoing', methods=['GET'])
def get_ongoing_projects(limit=3):
    if limit:
        projects = Project.query.filter(Project.status != 2).order_by(Project.date_created.desc()).limit(limit).all()

    if not projects:
        abort(404)
    return jsonify(projects=[i.serialize for i in projects])


@api.route('/v1.0/projects/tasks/<int:projectid>', methods=['GET'])
def get_project_tasks(projectid):
    project = Project.query.get(projectid)
    if not project:
        abort(404)
    return jsonify(tasks=[i.serialize for i in project.tasks])


@api.route('/v1.0/tasks/get/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        abort(404)
    return jsonify(task=task.serialize)

@api.route('/v1.0/tasks/create', methods=['POST'])
def create_tasks():
    if not request.json or 'title' not in request.json or 'budget' not in request.json or 'project_id' not in \
            request.json or 'owner_id' not in request.json:
        abort(400)

    if 'deadline' in request.json:
        task = Task(request.json['title'], request.json['budget'], request.json['project_id'],
                      request.json['owner_id'], request.json['deadline'])
    else:
        task = Task(request.json['title'], request.json['budget'], request.json['project_id'], request.json['owner_id'])
    db.session.add(task)
    db.session.commit()
    audit = Audit(request.json['owner_id'], "Task was created", 2, 'Task', task.id)
    db.session.add(audit)
    db.session.commit()

    return jsonify({'status': 'success', 'task': task.serialize}), 201


@api.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@api.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)