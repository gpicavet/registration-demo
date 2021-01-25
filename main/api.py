from datetime import datetime, timedelta
from string import digits
from random import choice
from email.utils import parseaddr
from flask import request, Blueprint
from flask_bcrypt import Bcrypt
from flask_api import status
from dependency_injector.wiring import inject, Provide
from main.user_repository import UserRepository
from main.mail_service import MailService
from main.container import ApplicationContainer

ACTIVATION_TIMEOUT = 60

bcrypt = Bcrypt()

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route('/register', methods=['POST'])
@inject
def register(user_repository: UserRepository = Provide[ApplicationContainer.user_repository],
             mail_service: MailService = Provide[ApplicationContainer.mail_service]):
    """Register a user or renew the activation code if timed out

    Request : JSON payload :
    {
      "email": "VALID EMAIL",
      "password": "PASSWORD between 12 and 255 characters"
    }

    Response:
    status 400 if not json data, or if email or password is invalid
    status 200 if account created or activation code renewed. An activation mail is sent
    status 200 if account exists, for security reasons (dont expose existing emails)
    """
    print(user_repository)
    if not request.json:
        return "Invalid json", status.HTTP_400_BAD_REQUEST

    tmpname, parsed_email = parseaddr(request.json.get("email"))
    if not parsed_email or '@' not in parsed_email:
        return "Invalid email", status.HTTP_400_BAD_REQUEST

    if not "password" in request.json or not (12 <= len(request.json.get("password")) <= 255):
        return "Invalid password : must be between 12 and 255 characters", status.HTTP_400_BAD_REQUEST

    account = user_repository.account_get(request.json["email"])

    if account and account["status"] != 'P':
        print("security : attempt to register again {0}".format(
            request.json["email"]))
    else:

        activation_key = ''.join(
            [choice(digits) for i in range(4)])

        if account:
            # only renew activation key. ignore new password for security
            user_repository.account_set_activation_key(
                request.json["email"], activation_key)
        else:
            password_hash = bcrypt.generate_password_hash(
                request.json["password"]).decode('utf8')
            user_repository.account_add(request.json["email"],
                            password_hash, 'P', activation_key)

        # TODO should retry or queue
        mail_service.send(
            request.json["email"], "Hello, here is your activation code {0}. Please go to /api/activate".format(activation_key))

    return 'Thanks, you will receive an email with the activation code', status.HTTP_200_OK


@bp.route('/activate', methods=['POST'])
@inject
def activate(user_repository: UserRepository = Provide[ApplicationContainer.user_repository]):
    """Activate a pending account

        Request: BASIC AUTH providing email and password given during registration
        JSON Payload:
        {
           "activation_code": "4 characters code"
        }

        Response:
        status 400 if invalid input or if no activation code provided, or if it doesnt match our database or if timed out
        status 401 if invalid credentials (no pending account with email and password)
        status 200 if activated or already activated
    """

    if not request.json:
        return "Invalid json", status.HTTP_400_BAD_REQUEST

    if not "activation_code" in request.json:
        return "Invalid input", status.HTTP_400_BAD_REQUEST

    if not request.authorization:
        return 'invalid email or password', status.HTTP_401_UNAUTHORIZED

    email = request.authorization["username"]
    password = request.authorization["password"]

    if not email or not password:
        return 'invalid email or password', status.HTTP_401_UNAUTHORIZED

    rep = UserRepository()
    account = rep.account_get(email)

    if not account or not bcrypt.check_password_hash(account["password"], password):
        return 'invalid email or password', status.HTTP_401_UNAUTHORIZED

    if account["status"] != 'P':
        return 'Your account is already activated', status.HTTP_200_OK

    if request.json["activation_code"] != account["activation_key"]:
        return 'invalid activation code', status.HTTP_400_BAD_REQUEST

    if (datetime.now() - account["registred_date"]) > timedelta(seconds=ACTIVATION_TIMEOUT):
        return 'activation code timed out, please register again', status.HTTP_400_BAD_REQUEST

    rep.account_activate(email)
    return 'Your account has been successfully activated', status.HTTP_200_OK
