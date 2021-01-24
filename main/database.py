from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor
from flask import g


class DatabaseConnection():
    """
    create a simple pool
    store db connection in Flask request context to keep transaction open across
    """

    __pool = None

    @classmethod
    def initialize(cls, dsn=""):
        print("initializing database connection pool")
        cls.__pool = SimpleConnectionPool(
            minconn=2, maxconn=5, dsn=dsn, cursor_factory=DictCursor)

    @classmethod
    def close_all_connections(cls):
        print("closing all connections")
        cls.__pool.closeall()

    @classmethod
    def get(cls):
        if 'db' not in g:
            g.db = DatabaseConnection.__pool.getconn()

        return g.db

    @classmethod
    def close(cls, exception):
        db = g.pop('db', None)

        if db is not None:

            if exception is not None:
                print("connection rollback")
                db.rollback()
            else:
                print("connection commit")
                db.commit()

            print("connection release")
            DatabaseConnection.__pool.putconn(db)
