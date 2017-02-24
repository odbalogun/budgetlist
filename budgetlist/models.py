from sqlalchemy import Column, Integer, DECIMAL, String, Date, DateTime, func, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import dump_datetime, to_json, list_task_status
import random
from flask_login import UserMixin

db = SQLAlchemy()

# association tables
child_tasks = Table('task_mapping', db.metadata,
                        Column('parent_id', Integer, ForeignKey('tasks.id')),
                        Column('child_id', Integer, ForeignKey('tasks.id'))
                        )


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

    def __init__(self, full_name, username, email, password, account_type=0):
        self.full_name = full_name
        self.username = username.lower()
        self.email = email.lower()
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


class Project(db.Model):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
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
    tasks = relationship("Task", back_populates="project")

    def __repr__(self):
        return self.title

    def __init__(self, title, description, budget_limit, start_month_period, end_month_period, owner_id):
        self.title = title
        self.description = description
        self.budget_limit = budget_limit
        self.start_month_period = start_month_period
        self.end_month_period = end_month_period
        self.owner_id = owner_id

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'budget_limit': self.budget_limit,
            'start_month_period': self.start_month_period,
            'end_month_period': self.end_month_period,
            'status': self.status,
            'completion': self.completion,
            'date_created': dump_datetime(self.date_created),
            # This is an example how to deal with Many2Many relations
            'owner': self.serialize_owner
        }

    @property
    def completion(self):
        return random.randrange(20, 100)

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
    budget = Column(Integer)
    percent = Column(Integer)
    project_id = Column(Integer, ForeignKey('projects.id'))
    owner_id = Column(Integer, ForeignKey('users.id'))
    date_created = Column(DateTime, default=func.now())
    deadline = Column(Date)
    status = Column(Integer, default=0)
    # 0 for open: 1 for done

    owner = relationship("User", uselist=False, back_populates="ownTasks")
    project = relationship("Project", uselist=False, back_populates="tasks")
    notes = relationship("Notes", back_populates="task")

    def __init__(self, title, budget, project_id, owner_id, deadline=None):
        self.title = title
        self.budget = budget
        self.project_id = project_id
        self.owner_id = owner_id
        self.deadline = deadline

    def __repr__(self):
        return self.title

    @property
    def statusText(self):
        return list_task_status[self.status]

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


class Department(db.Model):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    head_id = Column(Integer, ForeignKey('users.id'))

    head = relationship("User", uselist=False, foreign_keys=[head_id])
    members = relationship("User", back_populates="department", foreign_keys="User.department_id")