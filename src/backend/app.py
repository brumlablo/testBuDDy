from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# import logging

# logging.basicConfig(format="%d(pathname)s - %(lineno)d - %(levelname)s : %(message)s", level=logging.DEBUG)
# logger = logging.getLogger()
# print = logger.info

from flask import Flask
from flask_cors import CORS, cross_origin
from swagger_ui import flask_api_doc


app = Flask(__name__)
CORS(app)
flask_api_doc(app, config_path='./doc/swagger.yaml', url_prefix='', title='API doc')

app.config.from_object('config.Config') #app.config.from_envvar('.env', silent=True)
print(app.config["SQLALCHEMY_DATABASE_URI"])
dbs = SQLAlchemy(app, session_options={"autocommit": True})
# database model is initiated by init script from dbs container