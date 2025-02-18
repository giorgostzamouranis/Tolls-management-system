import mysql.connector
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import session, abort
from sqlalchemy import create_engine

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role

# Fetch user from the database
def get_user_by_username(username):
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='kyriakoskat7',
        database='toll_management_database'
    )
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

# Hash a password
def hash_password(password):
    return generate_password_hash(password)

# Verify a password
def verify_password(hash, password):
    return check_password_hash(hash, password)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='kyriakoskat7',
        database='toll_management_database'
    )

# Fetch debts from the database
def get_debts():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT debtor_id, receiver_id, amount FROM debt ORDER BY debtor_id;"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# Fetch toll station data
def fetch_data():
    conn = get_db_connection()
    query = """
    SELECT toll_id, COUNT(*) as total_passes, SUM(charge) as total_charge
    FROM pass
    GROUP BY toll_id
    """
    engine = create_engine('mysql+mysqlconnector://root:kyriakoskat7@localhost/toll_management_database')
    df = pd.read_sql_query(query, engine)

    conn.close()
    return df

# Decorator to protect endpoints based on roles
def role_required(role):
    """
    Decorator to protect endpoints by user role.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if session.get('role') != role:
                abort(403)  # Forbidden
            return func(*args, **kwargs)
        return wrapper
    return decorator
