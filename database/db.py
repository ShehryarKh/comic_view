"""
db module. Wrapper to make SQL queries.
"""

import app

import pymysql.cursors

import os
import hashlib


class DBException(Exception):
    """
    Thrown when a database error occurs.
    """
    pass


class DBQueryException(DBException):
    """
    Thrown when a database error occurs.
    """

    def __init__(self, code, message):
        self.code = code
        self.message = message


class DBKeyDoesNotExistException(DBQueryException):
    """
    Thrown when a database error occurs.
    """
    pass


class DBItemAlreadyExistsException(DBQueryException):
    """
    Thrown when a database error occurs.
    """
    pass


class DBItemExpiredException(DBQueryException):
    """
    Thrown when a database error occurs.
    """
    pass


class DBPolicyForbiddenException(DBQueryException):
    """
    Thrown when a database error occurs.
    """
    pass


def identifier():
    """
    Creates a unique crytographically secure 160 bit random number in
    hexidecimal format.

    Params:
        None

    Returns:
        (string): A random number in hexidecimal format.

    Raises:
        None
    """
    random = os.urandom(64)
    hash = hashlib.sha256()
    hash.update(random)
    identifier = hash.hexdigest()
    return identifier


def connection():
    """
    Creates a database connection.

    Params:
        None

    Returns:
        (DictCursor): A pymysql cursor object.

    Raises:
        None
    """
    try:
        connection = pymysql.connect(
            host=app.config['DB_HOST'],
            port=app.config.get('DB_PORT') or 3306,
            db=app.config['DB_NAME'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            charset='utf8',
            cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        raise raise_exception(e)
    return connection


def close(connection):
    """
    Closes connection.

    Params:
        connection (PySQL Connection): A connection created by above method.

    Returns:
        None

    Raises:
        DBException - A database error occured.
        DBKeyDoesNotExistException - A specified key in querydoes not exist.
        DBItemAlreadyExistsException - An item with specified key alread exists
        DBItemExpiredException - Debatable whether this should exists at all.
        DBPolicyForbiddenException - A user-made policy forbids this action.
    """

    if connection and connection.open:
        connection.close()


def commit(connection):
    """
    Commits and closes connection.

    Params:
        connection (PySQL Connection): A connection created by above method.

    Returns:
        None

    Raises:
        DBException - A database error occured.
        DBKeyDoesNotExistException - A specified key in querydoes not exist.
        DBItemAlreadyExistsException - An item with specified key alread exists
        DBItemExpiredException - Debatable whether this should exists at all.
        DBPolicyForbiddenException - A user-made policy forbids this action.
    """

    if connection and connection.open:
        connection.commit()
        close(connection)


def read(sql, params, many=False):
    """
    Makes a read query from database.

    Params:
        sql (string): The SQL query.
        params (tulip): The parameters to be inserted into the query.
        many (bool, optional): A flag to indicate a query that spans
                               more than one row.
        Defaults to False.

    Returns:
        (array): in the case of a many query
        (dictionary): in the case of a single row query

    Raises:
        DBException - A database error occured.
    """
    a_connection = connection()

    try:
        with a_connection.cursor() as cursor:
            cursor.execute(sql, params)

            if many:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()

    except Exception as e:
        close(a_connection)
        raise raise_exception(e)

    return result


def write(sql, params):
    """
    Makes a read query from database.

    Params:
        sql (string): The SQL query.
        params (tulip): The parameters to be inserted into the query.

    Returns:
        (int): The id of the row just inserted.

    Raises:
        DBException - A database error occured.
        DBKeyDoesNotExistException - A specified key in querydoes not exist.
        DBItemAlreadyExistsException - An item with specified key alread exists
        DBItemExpiredException - Debatable whether this should exists at all.
        DBPolicyForbiddenException - A user-made policy forbids this action.
    """
    result = None
    a_connection = connection()

    try:
        with a_connection.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.lastrowid

        a_connection.commit()

    except Exception as e:

        if connection:
            a_connection.rollback()
            close(a_connection)

        raise raise_exception(e)

    return result


def call(a_connection, procedure, params, many=False):
    """
    Calls stored procedure from database.

    Params:
        connection (PySQL Connection): A connection created by above method.
        procedure (string): The stored procedure.
        params (tulip): The parameters to be inserted into the query.
        many (bool, optional): A flag to indicate a query that spans
                               more than one row.
        Defaults to False.

    Returns:
        (array): in the case of a many query
        (dictionary): in the case of a single row query

    Raises:
        DBException - A non-specified database error occured. Used in prod.
        DBKeyDoesNotExistException - A specified key in querydoes not exist.
        DBItemAlreadyExistsException - An item with specified key alread exists
        DBItemExpiredException - Debatable whether this should exists at all.
        DBPolicyForbiddenException - A user-made policy forbids this action.
    """
    try:
        with a_connection.cursor() as cursor:

            if params:
                cursor.callproc(procedure, params)
            else:
                cursor.callproc(procedure)

            if many:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()

    except Exception as e:
        a_connection.rollback()
        close(a_connection)
        raise raise_exception(e)

    return result


def raise_exception(e):
    """
    Exception helper. Raises the given exception when testing,
    otherwise raises a DBException.

    Params:
        e (Exception): An Exception object.

    Returns:
        None

    Raises:
        Exception - When testing.
        DBException - When not testing.
        DBKeyDoesNotExistException - A specified key in querydoes not exist.
        DBItemAlreadyExistsException - An item with specified key alread exists
        DBItemExpiredException - Debatable whether this should exists at all.
        DBPolicyForbiddenException - A user-made policy forbids this action.
    """
    args = e.args
    code = args[0]
    message = args[1]

    # Codes in to 10xxx range are ones we throw in our procedures.
    if code == 10001:
        raise DBKeyDoesNotExistException(code, message)
    elif code == 10002:
        raise DBItemAlreadyExistsException(code, message)
    elif code == 10003:
        raise DBItemExpiredException(code, message)
    elif code == 10004:
        raise DBPolicyForbiddenException(code, message)

    testing = app.config['TESTING']
    debug = app.config['DEBUG']

    if testing or debug:
        raise e
    else:
        raise DBException
