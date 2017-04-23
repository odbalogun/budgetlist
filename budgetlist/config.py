# Configuration module
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """
    Base configuration object from which subclasses will inherit
    # set database variable
    export BUDGET_DB_CONN="postgresql://budgetuser:budge1234list*@localhost:5432/budgetlist"

    """

    DEBUG = False
    USE_LDAP_AUTH = True
    LDAP_PROVIDER_URL = 'ldap://ldap.forumsys.com:389/'
    LDAP_BIND_DN = 'dc=example,dc=com'
    SECRET_KEY = 'rcace2376bde12345'
    SQLALCHEMY_DATABASE_URI = "postgresql://budgetuser:budge1234list*@localhost:5432/budgetlist"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SERVER_NAME = 'budgetlist.local:5000'


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