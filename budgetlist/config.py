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
    SECRET_KEY = 'rcace2376bde12345'
    SQLALCHEMY_DATABASE_URI = os.environ['BUDGET_DB_CONN']
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