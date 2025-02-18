from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from common import get_db_connection
import pandas as pd
import mysql.connector

BASE_URL = "http://127.0.0.1:9115"

# Define the admin blueprint
admin_bp = Blueprint('admin', __name__)



@admin_bp.route('/admin/usermod', methods=['POST'])
def usermod():
    """
    Create a new user or update the password of an existing user.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "info": "username and password are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the user already exists
        query = "SELECT COUNT(*) FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        exists = cursor.fetchone()[0]

        if exists:
            # Update password
            update_query = "UPDATE users SET password = %s WHERE username = %s"
            cursor.execute(update_query, (password, username))
        else:
            # Create new user
            insert_query = "INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')"
            cursor.execute(insert_query, (username, password))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"}), 200

    except Exception as e:
        return jsonify({"status": "error", "info": str(e)}), 500


@admin_bp.route('/admin/users', methods=['GET'])
def list_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()

        cursor.close()
        conn.close()

        if not users:
            print("No users found in the database.")  # Debug log
            return jsonify([]), 200

        return jsonify(users), 200

    except Exception as e:
        print(f"Error in /admin/users: {e}")  # Debug log
        return jsonify({"error": f"Failed to fetch users: {str(e)}"}), 500





@admin_bp.route('/admin/resetstations', methods=['POST'])
def reset_stations():
    try:
        # Only use the tollstations file for resetting the toll (and operator) tables.
        tollstations_path = 'tollstations2024.csv'
        toll_data = pd.read_csv(tollstations_path)

        connection = get_db_connection()
        cursor = connection.cursor()

        # Fill Operator Table using data from tollstations2024.csv
        operators = toll_data[['OpID', 'Operator', 'Email']].drop_duplicates()
        operator_query = """
        INSERT IGNORE INTO operator (op_id, op_name, email)
        VALUES (%s, %s, %s)
        """
        for _, row in operators.iterrows():
            cursor.execute(operator_query, (row['OpID'], row['Operator'], row['Email']))

        # Fill Toll Table using data from tollstations2024.csv
        toll_query = """
        INSERT IGNORE INTO toll (
            toll_id, toll_name, op_id, road, latitude, longitude, PM, price1, price2, price3, price4
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for _, row in toll_data.iterrows():
            cursor.execute(toll_query, (
                row['TollID'], row['Name'], row['OpID'], row['Road'],
                row['Lat'], row['Long'], row['PM'], row['Price1'],
                row['Price2'], row['Price3'], row['Price4']
            ))

        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({"status": "OK"}), 200

    except Exception as e:
        return jsonify({"status": "failed", "info": str(e)}), 500




@admin_bp.route('/admin/addpasses', methods=['POST'])
def add_passes():
    try:
        if 'file' not in request.files:
            return jsonify({"status": "failed", "info": "No file part in the request"}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({"status": "failed", "info": "No file selected"}), 400

        # Expecting the CSV to have these columns:
        # For passes: tollID, tagRef, charge, timestamp
        # For tags: tagRef, tagHomeID
        df = pd.read_csv(file)
        required_columns = ['tollID', 'tagRef', 'tagHomeID', 'charge', 'timestamp']
        if not all(column in df.columns for column in required_columns):
            return jsonify({"status": "failed", 
                            "info": "Invalid CSV format, required columns: tollID, tagRef, tagHomeID, charge, timestamp"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert into the pass table
        pass_insert_query = """
        INSERT INTO pass (toll_id, tag_ref, charge, `timestamp`)
        VALUES (%s, %s, %s, %s)
        """
        for _, row in df.iterrows():
            cursor.execute(pass_insert_query, (
                row['tollID'], row['tagRef'], row['charge'], row['timestamp']
            ))

        # Insert into the tag table.
        # We extract unique tag rows using tagRef and tagHomeID.
        tags = df[['tagRef', 'tagHomeID']].drop_duplicates()
        tag_insert_query = """
        INSERT IGNORE INTO tag (tag_ref, tag_home, op_id)
        VALUES (%s, %s, %s)
        """
        for _, row in tags.iterrows():
            # Here op_id is being set to tagHomeID; adjust if your schema differs.
            cursor.execute(tag_insert_query, (
                row['tagRef'], row['tagHomeID'], row['tagHomeID']
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "OK"}), 200

    except FileNotFoundError:
        return jsonify({"status": "failed", "info": "CSV file not found"}), 500

    except Exception as e:
        return jsonify({"status": "failed", "info": str(e)}), 500
