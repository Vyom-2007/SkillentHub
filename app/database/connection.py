"""
Database connection module.
Provides helper functions for MySQL database operations using pymysql.
"""
import pymysql
from flask import current_app, g


def get_db_connection():
    """
    Get a database connection for the current request.
    Uses Flask's g object to store connection per request.
    
    Returns:
        pymysql connection object
    """
    if 'db' not in g:
        g.db = pymysql.connect(
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            database=current_app.config['DB_NAME'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    else:
        # Ping to ensure connection is alive
        try:
            g.db.ping(reconnect=True)
        except pymysql.Error:
            # If ping fails, reconnect
            g.db = pymysql.connect(
                host=current_app.config['DB_HOST'],
                port=current_app.config['DB_PORT'],
                user=current_app.config['DB_USER'],
                password=current_app.config['DB_PASSWORD'],
                database=current_app.config['DB_NAME'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
    return g.db


def close_db_connection(e=None):
    """
    Close the database connection at the end of the request.
    Should be registered with app.teardown_appcontext.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Execute a SQL query and optionally fetch results.
    
    Args:
        query: SQL query string with %s placeholders
        params: Tuple of parameters to substitute
        fetch_one: If True, fetch and return one row
        fetch_all: If True, fetch and return all rows
    
    Returns:
        - If fetch_one: Single row dict or None
        - If fetch_all: List of row dicts
        - Otherwise: Number of affected rows
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            print(f"DEBUG EXECUTE: {query} params={params}")
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount
    except pymysql.Error as e:
        current_app.logger.error(f"Database error: {e}")
        raise


def execute_insert(query, params=None):
    """
    Execute an INSERT query and return the last inserted ID.
    
    Args:
        query: INSERT SQL query string
        params: Tuple of parameters
    
    Returns:
        Last inserted row ID
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.lastrowid
    except pymysql.Error as e:
        current_app.logger.error(f"Database insert error: {e}")
        raise


def execute_update(query, params=None):
    """
    Execute an UPDATE or DELETE query and return affected rows.
    
    Args:
        query: UPDATE/DELETE SQL query string
        params: Tuple of parameters
    
    Returns:
        Number of affected rows
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount
    except pymysql.Error as e:
        current_app.logger.error(f"Database update error: {e}")
        raise


def init_app(app):
    """
    Initialize database connection management with Flask app.
    Registers teardown function to close connections.
    """
    app.teardown_appcontext(close_db_connection)
