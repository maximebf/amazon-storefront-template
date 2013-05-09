from flask import Flask
import os


__all__ = ['app']


app = Flask(__name__)
app.config['ENV'] = os.environ.get('FLASK_ENV', 'prod')
app.config.from_object('amzstorefront.settings.%sConfig' % app.config['ENV'].capitalize())


import views

