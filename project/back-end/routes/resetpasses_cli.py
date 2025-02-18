from flask import Blueprint, Response, jsonify, request, render_template
from collections import OrderedDict
from datetime import datetime
import mysql.connector
import json

resetpasses_cli_bp = Blueprint('resetpasses_cli', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='kyriakoskat7',
        database='toll_management_database'
    )

@resetpasses_cli_bp.route('/admin/resetpasses', methods=['POST'])
def resetpasses_cli():
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        

        # Disable foreign key checks (if necessary)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        # Perform deletion
        cursor.execute("DELETE FROM pass")
    

        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        # Commit changes
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "OK"}), 200

    except mysql.connector.Error as db_err:
        return jsonify({"status": "failed", "info": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"status": "failed", "info": str(e)}), 500

