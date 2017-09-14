from flask import Flask
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config.from_pyfile('config.py')
bootstrap = Bootstrap(app)

from web import views