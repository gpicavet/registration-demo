import pytest
import logging
import re

import sqlalchemy

from datetime import datetime,timedelta

from mock import patch, Mock

from pathlib import Path

from requests.auth import _basic_auth_str

from flask_bcrypt import Bcrypt

from testcontainers.postgres import PostgresContainer

from main import create_app
from main.database import DatabaseConnection
from main.mail_service import MailService


logging.basicConfig(level=logging.DEBUG)
mylogger = logging.getLogger()

bcrypt = Bcrypt()
password = bcrypt.generate_password_hash("aaaaaaaaaaaa").decode('utf8')


# create postgres container for all tests
@pytest.fixture(scope="module")
def app():
    postgres_container = PostgresContainer("postgres:13-alpine")
    code_dir = Path(__file__).parent
    with postgres_container as postgres:
        e = sqlalchemy.create_engine(postgres.get_connection_url())
        file=open(code_dir.parent.as_posix()+"/db.sql")
        escaped_sql = sqlalchemy.text(file.read())
        with e.connect().execution_options(autocommit=True) as conn:
            conn.execute(escaped_sql)
            conn.execute("DELETE FROM account")
        e.dispose()

        dsn = "dbname=test user=test password=test host=%s port=%s" % (postgres.get_container_host_ip(),
            postgres.get_exposed_port(port=5432))
        app = create_app(dsn)
        with app.app_context():
            yield app

# reset data and return cursor
@pytest.fixture()
def cursor():
        cursor = DatabaseConnection.get().cursor()
        cursor.execute("DELETE FROM account")
        return cursor

@patch.object(MailService,'send')
def test_shouldNotRegister(mock_send, app, cursor):
        #bad input

        response = app.test_client().post("/api/register")
        assert response.status_code == 400
        assert response.data == b'Invalid json'
        mock_send.assert_not_called()

        response = app.test_client().post(
            "/api/register", json={"email": "test3", "password": "aaaaaaaaaaaa"})
        assert response.status_code == 400
        assert response.data == b'Invalid email'
        mock_send.assert_not_called()

        response = app.test_client().post(
            "/api/register", json={"email": "test3@domain-test.fr", "password": "a"})
        assert response.status_code == 400
        assert b'Invalid password' in response.data
        mock_send.assert_not_called()

        cursor.execute("SELECT 1 FROM account WHERE email='test3@domain-test.fr'")
        assert not cursor.fetchone()


@patch.object(MailService,'send')
def test_shouldRegister(mock_send, app, cursor):
        #register first time
        assert app.test_client().post("/api/register",
                                      json={"email": "test3@domain-test.fr", "password": "aaaaaaaaaaaa"}).status_code == 200
        mock_send.assert_called_once()
        assert re.match('Hello, here is your activation code [a-zA-Z0-9]{4}. .*', mock_send.call_args.args[1])
        cursor.execute("SELECT 1 FROM account WHERE email='test3@domain-test.fr' AND password is not NULL AND status='P' AND activation_key is not NULL")
        assert cursor.fetchone()

@patch.object(MailService,'send')
def test_shouldRegisterRenew(mock_send, app, cursor):
        #register second time on existing pending : remain pending, activation code is renewed and another mail is sent
        cursor.execute(
            "INSERT INTO account(email,password,registred_date,status,activation_key) VALUES('test1@domain-test.fr',%s,%s,'P','1234')",(password,datetime.now()))

        assert app.test_client().post("/api/register",
                                      json={"email": "test1@domain-test.fr", "password": "aaaaaaaaaaaa"}).status_code == 200
        mock_send.assert_called_once()
        cursor.execute("SELECT 1 FROM account WHERE email='test1@domain-test.fr' AND status='P'")
        assert cursor.fetchone()
        cursor.execute("SELECT 1 FROM account WHERE email='test1@domain-test.fr' AND status='P' AND activation_key='1234'")
        assert not cursor.fetchone()

@patch.object(MailService,'send')
def test_shouldNotRegisterAgain(mock_send, app, cursor):
        #register second time on existing active
        cursor.execute(
            "INSERT INTO account(email,password,registred_date,status,activation_key) VALUES('test2@domain-test.fr',%s,%s,'A',NULL)",(password,datetime.now()))

        assert app.test_client().post("/api/register",
                                      json={"email": "test2@domain-test.fr", "password": "aaaaaaaaaaaa"}).status_code == 200
        mock_send.assert_not_called()


def test_shouldNotActivate(app, cursor):
        #bad input or auth failure
        cursor.execute(
            "INSERT INTO account(email,password,registred_date,status,activation_key) VALUES('test1@domain-test.fr',%s,%s,'P','1234')",(password,datetime.now()))

        assert app.test_client().post(
            "/api/activate").status_code == 400

        assert app.test_client().post(
            "/api/activate", json={"activation_code": "aaaa"}).status_code == 401

        assert app.test_client().post("/api/activate", json={"activation_code": "aaaa"},
                                      headers={"Authorization": _basic_auth_str("", "")}).status_code == 401

        assert app.test_client().post("/api/activate", json={"activation_code": "aaaa"},
                                      headers={"Authorization": _basic_auth_str("test1@domain-test.fr", "aaaa")}).status_code == 401

def test_shouldNotActivateBadCode(app, cursor):
        #bad activation code
        cursor.execute(
            "INSERT INTO account(email,password,registred_date,status,activation_key) VALUES('test1@domain-test.fr',%s,%s,'P','1234')",(password,datetime.now()))

        response = app.test_client().post("/api/activate", json={"activation_code": "aaaa"},
                                          headers={"Authorization": _basic_auth_str("test1@domain-test.fr", "aaaaaaaaaaaa")})
        assert response.status_code == 400
        assert response.data == b'invalid activation code'
        cursor.execute("SELECT 1 FROM account WHERE email='test1@domain-test.fr' AND status='A'")
        assert not cursor.fetchone()

def test_shouldNotActivateTimedOut(app, cursor):
        #activation code timed out
        cursor.execute(
            "INSERT INTO account(email,password,registred_date,status,activation_key) VALUES('test0@domain-test.fr',%s,%s,'P','1234')",(password,datetime.now()+timedelta(seconds=-61)))

        response = app.test_client().post("/api/activate", json={"activation_code": "1234"},
                                          headers={"Authorization": _basic_auth_str("test0@domain-test.fr", "aaaaaaaaaaaa")})
        assert response.status_code == 400
        assert response.data == b'activation code timed out, please register again'
        cursor.execute("SELECT 1 FROM account WHERE email='test0@domain-test.fr' AND status='A'")
        assert not cursor.fetchone()

def test_shouldActivate(app, cursor):
        #OK with pending status
        cursor.execute(
            "INSERT INTO account(email,password,registred_date,status,activation_key) VALUES('test1@domain-test.fr',%s,%s,'P','1234')",(password,datetime.now()))

        response = app.test_client().post("/api/activate", json={"activation_code": "1234"},
                                          headers={"Authorization": _basic_auth_str("test1@domain-test.fr", "aaaaaaaaaaaa")})
        assert response.status_code == 200
        cursor.execute("SELECT 1 FROM account WHERE email='test1@domain-test.fr' AND status='A'")
        assert cursor.fetchone()

def test_shouldNotActivateAgain(app, cursor):
        #OK but already activated
        cursor.execute(
            "INSERT INTO account(email,password,registred_date,status,activation_key) VALUES('test2@domain-test.fr',%s,%s,'A',NULL)",(password,datetime.now()))

        response = app.test_client().post("/api/activate", json={"activation_code": "1234"},
                                          headers={"Authorization": _basic_auth_str("test2@domain-test.fr", "aaaaaaaaaaaa")})
        assert response.status_code == 200
        assert b'Your account is already activated' in response.data
        cursor.execute("SELECT 1 FROM account WHERE email='test2@domain-test.fr' AND status='A'")
        assert cursor.fetchone()

