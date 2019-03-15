from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from models import db
from config import DevConfig
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.config.from_object(DevConfig)
db.init_app(app)

# login manager
lm = LoginManager()
lm.init_app(app)

# mail setup
mail = Mail(app)

from views.api import api
from views.main import main
from views.tasks import tasks, send_notification_mails, process_projects, process_tasks

# setup blueprints
app.register_blueprint(api, url_prefix='/api')
# app.register_blueprint(api)
app.register_blueprint(main)
# blueprint for background tasks
app.register_blueprint(tasks)

# scheduler setup
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

scheduler.add_job('send_notifications', send_notification_mails, **{'trigger': 'interval', 'minutes': 3})
scheduler.add_job('process_tasks', process_tasks, **{'trigger': 'interval', 'days': 1, 'start_date': '2017-05-05 00:30:00'})
scheduler.add_job('process_projects', process_projects, **{'trigger': 'interval', 'days': 1, 'start_date': '2017-05-05 00:30:00'})
