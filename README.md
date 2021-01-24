Registration Demo
=================

Install and Test
----------------

Start the stack ::

    $ docker-compose up

Register::

    $ curl -H "Content-Type: application/json" localhost:8000/api/register -d "{\"email\":\"toto@domain.fr\",\"password\":\"aaaaaaaaaaaa\"}"

Check the mail in docker-compose output ::
    "body": "{\"to\": \"toto@domain.fr\", \"from\": \"noreply@registration-demo.io\", \"body\": \"Hello, here is your activation code OLjC. Please go to /api/activate\"}",

Activate your account, given 1234 is your activation code ::

    $ curl -H "Content-Type: application/json" -u "toto@domain.fr":aaaaaaaaaaaa localhost:8000/api/activate -d "{\"activation_code\":\"OLjC\"}"


Install DEV
-----------


Create a virtualenv and activate it::

    $ python3 -m venv venv
    $ . venv/bin/activate

Install dependencies::

    $ pip install -e .


Run DEV
-------

::

    $ docker-compose up database
    $ export FLASK_APP=main FLASK_ENV=development PGHOST=localhost PGUSER=demo PGPASSWORD=demo PGDATABASE=registration PGPORT=5432
    $ flask run


Open http://127.0.0.1:5000 in a browser.


Test DEV
--------

::

    $ pip install '.[test]'
    $ pytest

Please wait until the docker images are downloading !

Run with coverage report::

    $ coverage run -m pytest
    $ coverage report
    $ coverage html  # open htmlcov/index.html in a browser
