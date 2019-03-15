from sqlalchemy import Column, Integer, String, Date, DateTime, func, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import dump_datetime, to_json, list_task_status, list_audit_models, list_audit_types
from flask_login import UserMixin

db = SQLAlchemy()

ADMIN_USER = 'oduntan'

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    full_name = Column(String(100))
    username = Column(String(50), unique=True)
    email = Column(String(120), unique=True)
    department_id = Column(Integer, ForeignKey('departments.id'))
    password_hash = Column(String(200))
    account_type = Column(Integer, default=0)
    # 0 for Basic: 1 for Super: 2 for Admin
    status = Column(Integer, default=0)
    # 0 for Active: 1 for Inactive
    date_created = Column(DateTime, default=func.now())

    projects = relationship("Project", back_populates="owner")
    ownTasks = relationship("Task", back_populates="owner")
    department = relationship("Department", back_populates="members", foreign_keys=[department_id])
    permissions = relationship("Permissions", back_populates="owner")

    def __init__(self, full_name, username, email, password, department, account_type=0):
        self.full_name = full_name
        self.username = username.lower()
        self.email = email.lower()
        self.department_id = department
        self.set_password(password)
        self.account_type = account_type

    def __repr__(self):
        return self.full_name

    @property
    def user_type(self):
        if self.account_type == 1:
            return 'Super User'
        elif self.account_type == 0:
            return 'Basic User'
        else:
            return 'Administrator'

    @property
    def is_super(self):
        if self.account_type == 1 or self.username == ADMIN_USER:
            return True
        return False

    @property
    def is_basic(self):
        if self.account_type == 0 or self.username == ADMIN_USER:
            return True
        return False

    @property
    def is_admin(self):
        if self.account_type == 2 or self.username == ADMIN_USER:
            return True
        return False

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'username': self.username,
            'email': self.email,
            'account_type': self.account_type,
            'date_created': dump_datetime(self.date_created),
            # This is an example how to deal with Many2Many relations
            # 'projects': self.serialize_projects
        }

    @property
    def serialize_projects(self):
        """
        Return object's relations in easily serializeable format.
        NB! Calls many2many's serialize property.
        """
        return [item.serialize for item in self.projects]


class Project(db.Model):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    budget_limit = Column(Integer)
    budget_id = Column(Integer, ForeignKey('sub_budgets.id'))
    period_id = Column(Integer, ForeignKey('periods.id'))
    start_date = Column(Date)
    end_date = Column(Date)
    priority = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey('users.id'))
    date_created = Column(DateTime, default=func.now())
    status = Column(Integer, default=0)
    # 0 for open: 1 for ongoing: 2 for completed: 3 for suspended

    amt_allocated_task = Column(Integer, default=0)

    owner = relationship("User", uselist=False, back_populates="projects")
    main_tasks = relationship("Task", foreign_keys="Task.project_id", primaryjoin="and_(Project.id==Task.project_id, Task.parent_task == None)")
    tasks = relationship("Task", back_populates="project")
    budget = relationship("SubBudgets", uselist=False, back_populates="projects")
    period = relationship("Period", uselist=False)

    def __repr__(self):
        return self.title

    def __init__(self, title, description, budget_limit, budget_id, start_date, end_date, priority, owner_id, period_id):
        self.title = title
        self.description = description
        self.budget_limit = budget_limit
        self.budget_id = budget_id
        self.start_date = start_date
        self.end_date = end_date
        self.priority = priority
        self.owner_id = owner_id
        self.period_id = period_id

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'budget_limit': self.budget_limit,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'status': self.status,
            'completion': self.completion,
            'date_created': dump_datetime(self.date_created),
            # This is an example how to deal with Many2Many relations
            'owner': self.serialize_owner
        }

    @property
    def is_completed(self):
        if self.status == 2:
            return True
        return False

    @property
    def completion(self):
        if self.status == 2:
            return 100
        else:
            if len(self.tasks) > 0:
                percent = 0
                for task in self.tasks:
                    percent += task.percent

                return int(percent / len(self.tasks))
            else:
                return 0

    @property
    def amount_spent(self):
        return self.amt_allocated_task

    @property
    def amount_remaining(self):
        return self.budget_limit - self.amount_spent

    @property
    def serialize_owner(self):
        return self.owner.serialize

    @property
    def serialize_tasks(self):
        """
        Return object's relations in easily serializeable format.
        NB! Calls many2many's serialize property.
        """
        return [item.serialize for item in self.tasks]


class Task(db.Model):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    budget = Column(Integer)
    priority = Column(Integer, default=0)
    project_id = Column(Integer, ForeignKey('projects.id'))
    parent_task = Column(Integer, ForeignKey('tasks.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    date_created = Column(DateTime, default=func.now())
    start_date = Column(Date)
    deadline = Column(Date)
    status = Column(Integer, default=0)
    amount_spent = Column(Integer)
    # 0 for open: 1 for done

    owner = relationship("User", uselist=False, back_populates="ownTasks")
    project = relationship("Project", uselist=False, back_populates="tasks")
    child_tasks = relationship("Task", primaryjoin="Task.id == Task.parent_task")
    history = relationship("TaskHistory", back_populates="task", order_by="TaskHistory.date_created")

    def __init__(self, title, description, budget, project_id, owner_id, priority, start_date, deadline=None):
        self.title = title
        self.description = description
        self.budget = int(budget)
        self.project_id = int(project_id)
        self.owner_id = int(owner_id)
        self.priority = int(priority)
        self.start_date = start_date
        self.deadline = deadline

    def __repr__(self):
        return self.title

    @property
    def percent(self):
        if self.history:
            return self.history[-1].percent
        return 0

    @property
    def amount_performed(self):
        #if self.history:
        #    price = 0
        #    for his in self.history:
        #        if his.amount_spent:
        #            price = price + his.amount_spent
        #        else:
        #            price = price + 0
        #    return price
        return self.budget

    @property
    def statusText(self):
        return list_task_status[self.status]

    @property
    def deadline_string(self):
        return dump_datetime(self.deadline)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'title': self.title,
            'budget': self.budget,
            'description': self.description,
            'project_id': self.project_id,
            'percent': self.percent,
            'owner_id': self.owner_id,
            'start_date': self.start_date,
            'start_date_format': dump_datetime(self.start_date),
            'deadline': self.deadline,
            'deadline_format': dump_datetime(self.deadline),
            'status': self.status,
            'statusText': self.statusText,
            'date_created': dump_datetime(self.date_created),
            # This is an example how to deal with Many2Many relations
            'owner': self.owner.serialize,
            'history': self.serialize_history
        }

    @property
    def serialize_history(self):
        """
        Return object's relations in easily serializeable format.
        NB! Calls many2many's serialize property.
        """
        return [item.serialize for item in self.history]

class TaskHistory(db.Model):
    __tablename__ = 'task_history'

    id = Column(Integer, primary_key=True)
    note = Column(Text)
    percent = Column(Integer)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    date_created = Column(DateTime, default=func.now())

    owner = relationship("User", uselist=False)
    task = relationship("Task", uselist=False, back_populates="history")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'note': self.note,
            'percent': self.percent,
            'date_created': dump_datetime(self.date_created),
            'task_id': self.task_id,
            'owner': self.owner.full_name
        }

class Permissions(db.Model):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    access_level = Column(Integer)
    date_created = Column(DateTime, default=func.now())

    def __init__(self, user_id, task_id, access_level=0):
        self.user_id = user_id
        self.task_id = task_id
        self.access_level = access_level

    owner = relationship("User", uselist=False)
    task = relationship("Task", uselist=False)


class Company(db.Model):
    __tablename__ = 'company'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    address = Column(Text)
    website = Column(String(100))
    date_created = Column(DateTime, default=func.now())


class Period(db.Model):
    __tablename__ = 'periods'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(Integer)
    date_created = Column(DateTime, default=func.now())

    def __repr__(self):
        return self.name

    def string_date(self, value):
        return dump_datetime(value)

    def is_active(self):
        if self.status == 0:
            return True
        return False

    budget = relationship("Budget", uselist=False, back_populates="period")

class Department(db.Model):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    members = relationship("User", back_populates="department", foreign_keys="User.department_id")

    def __repr__(self):
        return self.name

    @property
    def member_count(self):
        return len(self.members)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name
        }


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    period_id = Column(Integer, ForeignKey('periods.id'))
    date_created = Column(DateTime, default=func.now())

    period = relationship("Period", uselist=False)
    main_subs = relationship("SubBudgets", foreign_keys="SubBudgets.budget_id", primaryjoin="and_(Budget.id==SubBudgets.budget_id, SubBudgets.parent_budget == None)", order_by="SubBudgets.name")
    subs = relationship("SubBudgets", foreign_keys="SubBudgets.budget_id")

    def __repr__(self):
        return self.title

    @property
    def title(self):
        return self.name + " for " + self.period.name

    @property
    def amount_allocated(self):
        amount = 0
        for sub in self.main_subs:
            amount = amount + sub.total_amount_allocated
        return amount

    @property
    def total_budget(self):
        budget = 0
        for item in self.main_subs:
            budget = budget + item.get_allocation
        return budget

    @property
    def budget_difference(self):
        return self.total_budget - self.amount_allocated

class SubBudgets(db.Model):
    __tablename__ = 'sub_budgets'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    allocation =Column(Integer, default=0)
    budget_id = Column(Integer, ForeignKey('budgets.id'))
    parent_budget = Column(Integer, ForeignKey('sub_budgets.id'))
    created_by = Column(Integer, ForeignKey('users.id'))
    date_created = Column(DateTime, default=func.now())
    status = Column(Integer, default=0)
    sub_budget_type = Column(Integer, ForeignKey('sub_budget_classes.id'))

    # amount allocated
    # amt_allocated_budget = Column(Integer, default=0)
    amt_allocated_project = Column(Integer, default=0)

    creator = relationship("User", uselist=False)
    budget = relationship("Budget", uselist=False)
    child_budgets = relationship("SubBudgets", primaryjoin="SubBudgets.id == SubBudgets.parent_budget", order_by="SubBudgets.id")
    projects = relationship("Project")
    budget_class = relationship("SubBudgetClass", primaryjoin="SubBudgets.sub_budget_type == SubBudgetClass.id", uselist=False)

    def __repr__(self):
        return self.name

    @property
    def amount_allocated(self):
        amount = self.amt_allocated_project
        return amount

    @property
    def total_amount_allocated(self):
        amount = self.amt_allocated_project
        for i in self.child_budgets:
            amount = amount + i.amount_allocated
        return amount

    @property
    def amount_remaining(self):
        return self.allocation - self.amount_allocated

    @property
    def get_allocation(self):
        # if self.allocation:
        #    return self.allocation
        # return 0
        amount = self.allocation
        for i in self.child_budgets:
            amount = amount + i.get_allocation
        return amount

    @property
    def is_editable(self):
        if self.parent_budget:
            return True
        return False

    @property
    def is_movable(self):
        if self.budget_class.movable == 0:
            return True
        return False

    @property
    def has_child_budget(self):
        if len(self.child_budgets) == 0:
            return False
        return True

    @property
    def date_created_string(self):
        return dump_datetime(self.date_created)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'allocation': self.allocation,
            'total_allocation': self.get_allocation,
            'amount_remaining': self.amount_remaining,
            'editable': self.is_editable,
            'statusText': self.statusText,
            'activityCount': len(self.projects),
            'subs': self.sub_budgets
        }

    @property
    def sub_budgets(self):
        """Return object data in easily serializeable format"""
        subs = []
        for i in self.child_budgets:
            subs.append({
                'id': i.id,
                'name': i.name,
                'allocation': i.allocation,
                'amount_remaining': i.amount_remaining,
                'has_child_budget': i.has_child_budget,
                'statusText': i.statusText,
                'editable': i.is_editable
            })
        return subs

    @property
    def statusText(self):
        if self.status == 0:
            return 'Active'
        else:
            return 'Suspended'

class SubBudgetClass(db.Model):
    __tablename__ = 'sub_budget_classes'

    id = Column(Integer, primary_key=True)
    sub_budget_class = Column(String(100))
    movable = Column(Integer, default=0)

    def __repr__(self):
        return self.sub_budget_class

class Messages(db.Model):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    message = Column(Text)
    subject = Column(String(100))
    recieve_type = Column(Integer) # 0 for individual 1 for group
    group = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    status = Column(Integer, default=0)
    date_created = Column(DateTime, default=func.now())
    date_processed = Column(DateTime)

    user = relationship("User", uselist=False)

    def __repr__(self):
        return self.subject

    def __init__(self, subject, message, recieve_type, group=None, user_id=None):
        self.subject = subject
        self.message = message
        self.recieve_type = int(recieve_type)
        if self.recieve_type == 0:
            # send to a particular user
            self.group = None
            self.user_id = user_id
        else:
            # send to group
            self.user_id = None
            self.group = group

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'subject': self.subject,
            'status': self.status
        }

class Audit(db.Model):
    __tablename__ = 'audit'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(Text)
    action_type = Column(Integer)
    action_model = Column(String(100))
    item_id = Column(Integer)
    date_created = Column(DateTime, default=func.now())

    project = relationship("Project", foreign_keys="Audit.item_id", primaryjoin="and_(Project.id==Audit.item_id,"
                                                                                " Audit.action_model == 'Project')", uselist=False)
    task = relationship("Task", foreign_keys="Audit.item_id", primaryjoin="and_(Task.id==Audit.item_id,"
                                                                                " Audit.action_model == 'Task')", uselist=False)
    user = relationship("User", foreign_keys="Audit.item_id", primaryjoin="and_(User.id==Audit.item_id,"
                                                                                " Audit.action_model == 'User')", uselist=False)
    budget = relationship("Budget", foreign_keys="Audit.item_id", primaryjoin="and_(Budget.id==Audit.item_id,"
                                                                                " Audit.action_model == 'Budget')", uselist=False)
    sub_budget = relationship("SubBudgets", foreign_keys="Audit.item_id", primaryjoin="and_(SubBudgets.id==Audit.item_id,"
                                                                                " Audit.action_model == 'Sub Budget')", uselist=False)
    sub_budget_class = relationship("SubBudgetClass", foreign_keys="Audit.item_id", primaryjoin="and_(SubBudgetClass.id==Audit.item_id,"
                                                                                " Audit.action_model == 'Sub Budget Class')", uselist=False)
    department = relationship("Department", foreign_keys="Audit.item_id", primaryjoin="and_(Department.id==Audit.item_id,"
                                                                                " Audit.action_model == 'Department')", uselist=False)

    period = relationship("Period", foreign_keys="Audit.item_id", primaryjoin="and_(Period.id==Audit.item_id,"
                                                                                " Audit.action_model == 'Period')", uselist=False)

    owner = relationship("User", uselist=False)

    def __init__(self, user_id, desc, action_type, action_model, item_id):
        self.user_id = user_id
        self.description = desc
        self.action_type = action_type
        self.action_model = action_model
        self.item_id = item_id

    @property
    def get_item(self):
        if self.action_model == 'User':
            return self.user
        elif self.action_model == 'Project':
            return self.project
        elif self.action_model == 'Task':
            return self.task
        elif self.action_model == 'Budget':
            return self.budget
        elif self.action_model == 'Sub Budget':
            return self.sub_budget
        elif self.action_model == 'Sub Budget Class':
            return self.sub_budget_class
        elif self.action_model == 'Department':
            return self.department
        elif self.action_model == 'Period':
            return self.period

    @property
    def category(self):
        return list_audit_types[self.action_type]