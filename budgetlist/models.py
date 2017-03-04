from sqlalchemy import Column, Integer, DECIMAL, String, Date, DateTime, func, ForeignKey, Table, Text
from sqlalchemy.orm import relationship, remote, foreign
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import dump_datetime, to_json, list_task_status
import random
from flask_login import UserMixin

db = SQLAlchemy()

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
            return 'Super'
        elif self.account_type == 0:
            return 'Basic'
        else:
            return 'Admin'

    @property
    def is_super(self):
        if self.account_type == 1:
            return True
        return False

    @property
    def is_basic(self):
        if self.account_type == 0:
            return True
        return False

    @property
    def is_admin(self):
        if self.account_type == 2:
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



class Task(db.Model):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    description = Column(Text)
    budget = Column(Integer)
    percent = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    project_id = Column(Integer, ForeignKey('projects.id'))
    parent_task = Column(Integer, ForeignKey('tasks.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    date_created = Column(DateTime, default=func.now())
    deadline = Column(Date)
    status = Column(Integer, default=0)
    # 0 for open: 1 for done

    owner = relationship("User", uselist=False, back_populates="ownTasks")
    project = relationship("Project", uselist=False, back_populates="tasks")
    child_tasks = relationship("Task", primaryjoin="Task.id == Task.parent_task")
    notes = relationship("Notes", back_populates="task")

    def __init__(self, title, description, budget, project_id, owner_id, priority, deadline=None):
        self.title = title
        self.description = description
        self.budget = int(budget)
        self.project_id = int(project_id)
        self.owner_id = int(owner_id)
        self.priority = int(priority)
        self.deadline = deadline
        self.percent = random.randrange(20, 100)

    def __repr__(self):
        return self.title

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
            'project_id': self.project_id,
            'owner_id': self.owner_id,
            'deadline': self.deadline,
            'status': self.status,
            'date_created': dump_datetime(self.date_created),
            # This is an example how to deal with Many2Many relations
            'owner': self.owner.serialize
        }

class Project(db.Model):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    percent = Column(Integer)
    description = Column(Text)
    budget_limit = Column(Integer)
    budget_id = Column(Integer)
    start_date = Column(Date)
    end_date = Column(Date)
    priority = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey('users.id'))
    date_created = Column(DateTime, default=func.now())
    status = Column(Integer, default=0)
    # 0 for open: 1 for ongoing: 2 for completed: 3 for suspended

    owner = relationship("User", uselist=False, back_populates="projects")
    main_tasks = relationship("Task", foreign_keys="Task.project_id", primaryjoin="and_(Project.id==Task.project_id, Task.parent_task == None)")
    tasks = relationship("Task", back_populates="project")

    def __repr__(self):
        return self.title

    def __init__(self, title, description, budget_limit, budget_id, start_date, end_date, priority, owner_id):
        self.title = title
        self.description = description
        self.budget_limit = budget_limit
        self.budget_id = budget_id
        self.start_date = start_date
        self.end_date = end_date
        self.priority = priority
        self.owner_id = owner_id
        self.percent = random.randrange(20, 100)

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
    def completion(self):
        return self.percent

    @property
    def amount_spent(self):
        return int(0.25 * self.budget_limit)

    @property
    def amount_remaining(self):
        return int(0.75 * self.budget_limit)

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

class Notes(db.Model):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    note = Column(Text)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    date_created = Column(DateTime, default=func.now())

    owner = relationship("User", uselist=False)
    task = relationship("Task", uselist=False, back_populates="notes")


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

    def string_date(self, value):
        return dump_datetime(value)

    budgets = relationship("Budget")

class Department(db.Model):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    members = relationship("User", back_populates="department", foreign_keys="User.department_id")


class Budget(db.Model):
    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    period_id = Column(Integer, ForeignKey('periods.id'))
    budget_type = Column(Integer, default=0)
    allocation = Column(Integer)
    date_created = Column(DateTime, default=func.now())

    period = relationship("Period", uselist=False)