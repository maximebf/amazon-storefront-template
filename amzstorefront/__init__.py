from flask import Flask, g, session
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
import os


app = Flask(__name__)
app.config['ENV'] = os.environ.get('FLASK_ENV', 'prod')
app.config.from_object('amzstorefront.settings.%sConfig' % app.config['ENV'].capitalize())

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.setup_app(app)


from models import User, Category


@login_manager.user_loader
def load_user(id):
    return User()


@app.before_request
def setup_layout_vars():
    g.categories = Category.query.all()


import views

