from flask import Flask
from flask_login import LoginManager
from models import db
from config import DevConfig

app = Flask(__name__)
app.config.from_object(DevConfig)
db.init_app(app)

# login manager
lm = LoginManager()
lm.init_app(app)

from views.api import api
from views.main import main

# setup blueprints
app.register_blueprint(api, url_prefix='/api')
# app.register_blueprint(api)
app.register_blueprint(main)
