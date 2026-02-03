"""
Database helper module for executing raw SQL queries with MySQL.
"""

import mysql.connector
from mysql.connector import Error
from flask import current_app


def get_db_connection():
    """
    Create and return a database connection using Flask app config.
    """
    try:
        connection = mysql.connector.connect(
            host=current_app.config.get('DB_HOST', 'localhost'),
            database=current_app.config.get('DB_NAME', 'skillenthub'),
            user=current_app.config.get('DB_USER', 'root'),
            password=current_app.config.get('DB_PASSWORD', '')
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def execute_query(query, params=(), fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a raw SQL query with optional parameters.
    
    Args:
        query (str): The SQL query to execute.
        params (tuple): Parameters to substitute in the query.
        fetch_one (bool): If True, fetch and return a single row.
        fetch_all (bool): If True, fetch and return all rows.
        commit (bool): If True, commit the transaction (for INSERT/UPDATE/DELETE).
    
    Returns:
        - Single row dict if fetch_one=True
        - List of row dicts if fetch_all=True
        - lastrowid if commit=True (for INSERT)
        - None otherwise
    """
    connection = get_db_connection()
    if connection is None:
        return None
    
    cursor = None
    result = None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        elif commit:
            connection.commit()
            result = cursor.lastrowid
        
    except Error as e:
        print(f"Error executing query: {e}")
        if commit:
            connection.rollback()
        result = None
    
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
    
    return result
