class Config(object):
    """Application backend configuration."""
    DEBUG = True
    TESTING = True
    DEVELOPMENT = True
    SECRET_KEY = 'super-secret'
    FLASK_HTPASSWD_PATH = '/secret/.htpasswd'
    FLASK_SECRET = 'testbuddy'
    DBS_HOST = 'dbs'
    DBS_PORT = '1234'
    DBS_USERNAME = 'root'
    DBS_PSW = 'admin'
    DBS_NAME = 'testbuddy'
    SQLALCHEMY_DATABASE_URI = f'mysql://{DBS_USERNAME}:{DBS_PSW}@{DBS_HOST}:{DBS_PORT}/{DBS_NAME}'