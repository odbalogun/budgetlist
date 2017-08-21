# Configuration module
import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """
    Base configuration object from which subclasses will inherit
    # set database variable
    export BUDGET_DB_CONN="postgresql://budgetuser:budge1234list*@localhost:5432/budgetlist"

    """

    DEBUG = False
    USE_LDAP_AUTH = False
    LDAP_PROVIDER_URL = 'ldap://ldap.forumsys.com:389/'
    LDAP_BIND_DN = 'dc=example,dc=com'
    SECRET_KEY = 'rcace2376bde12345'
    SQLALCHEMY_DATABASE_URI = "postgresql://budgetuser:budge1234list*@localhost:5432/budgetlist"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SERVER_NAME = 'budgetlist.local:5000'

    # for mail sending on dev
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'sigma.balogun@gmail.com'
    MAIL_PASSWORD = 'dimeji@19'
    MAIL_DEFAULT_SENDER = 'flask@example.com'

    #ADMIN_USER = 'oduntan'


class DevConfig(Config):
    """
    Development config object

    """

    DEBUG = True
    DEVELOPMENT = True


class ProductionConfig(Config):
    """
    Production config object

    """

    DEBUG = False