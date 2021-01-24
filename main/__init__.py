from flask import Flask
from main import api, database, container
from main.user_repository import UserRepository
from main.mail_service import MailService

def create_app(dsn=""):

    app = Flask(__name__)

    database.DatabaseConnection.initialize(dsn)

    app.container=container.ApplicationContainer()
    app.container.wire(modules=[api])

    api.bcrypt.init_app(app)
    app.register_blueprint(api.bp)
    app.teardown_appcontext(database.DatabaseConnection.close)

    return app
