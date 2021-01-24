from flask import Flask
from main import api, database


def create_app(dsn=""):

    app = Flask(__name__)

    database.DatabaseConnection.initialize(dsn)

    api.bcrypt.init_app(app)
    app.register_blueprint(api.bp)
    app.teardown_appcontext(database.DatabaseConnection.close)

    return app
