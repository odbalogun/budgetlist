from flask import Blueprint
from flask_mail import Message
from sqlalchemy import func
from budgetlist import app, mail
from budgetlist.models import db, Messages, User, Task, Permissions, Project, Period
from datetime import date

tasks = Blueprint('tasks', __name__)

# save email messages
def log_message(message, subject, rtype, group, user_id):
    msg = Messages(subject, message, rtype, group, user_id)
    db.session.add(msg)
    db.session.commit()


def send_notification_mails():
    with app.app_context():
        # get unprocessed emails
        messages = Messages.query.filter(Messages.status==0).all()

        for msg in messages:
            # check if its to be sent to groups or individual
            if msg.recieve_type == 0:
                # if individual
                email = Message(subject=msg.subject, recipients=msg.user.email, html=msg.message, sender='notifications@budgetlist.com')
                #mail.send(email)
                print msg.subject
            else:
                # get all group members
                users = User.query.filter(User.account_type==msg.group).all()

                # process for each group member
                for user in users:
                    email = Message(subject=msg.subject, recipients=user.email, html=msg.message, sender='notifications@budgetlist.com')
                    # mail.send(email)
                    print msg.subject

            # update record
            msg.status = 1
            msg.date_processed = func.now()
            db.session.add(msg)
            db.session.commit()

def process_tasks():
    with app.app_context():
        # get outstanding tasks
        tasks = Task.query.filter(Task.status != 2, Task.status != 3, date.today() >= Task.deadline)
        for task in tasks:
            # get permissions
            for p in Permissions.query.filter(Permissions.task_id==task.id).all():
                if task.deadline == date.today():
                    msg = Messages("Expiring Task: "+task.title, "Your task "+task.title+" expires today. Kindly login and update it accordingly.", 0, None, p.user_id)
                else:
                    msg = Messages("Overdue Task: "+task.title, "The task "+task.title+" is overdue. Please login and update it as required.", 0, None, p.user_id)

                db.session.add(msg)
                db.session.commit()


def process_projects():
    with app.app_context():
        period = Period.query.filter(Period.status==0).first()
        # get overdue projects
        projects = Project.query.filter(date.today() >= Project.end_date, Project.status != 2, Project.period_id==period.id)

        for pro in projects:
            if pro.end_date == date.today():
                msg = Messages("Expiring Project: "+pro.title, "Your project "+pro.title+" expires today. Kindly login and update it accordingly.", 0, None, pro.owner_id)
            else:
                msg = Messages("Overdue Project: "+pro.title, "The project "+pro.title+" is overdue. Please login and update it as required.", 0, None, pro.owner_id)

            db.session.add(msg)
            db.session.commit()