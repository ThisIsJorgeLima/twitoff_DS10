'''Code for our app'''

from flask import Flask
from .models import DB
# make our app factory


def create_app():
    app = Flask(__name__)

    # add config for database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    # have the database know about the app'
    DB.init_app(app)

    @app.route('/')
    def root():
        return 'Welcome to Twitoff!'
    return app
