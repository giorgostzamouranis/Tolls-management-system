from flask import Blueprint, Response, jsonify, request, render_template
from collections import OrderedDict
from datetime import datetime
import mysql.connector
import json

healthcheck_cli_bp = Blueprint('healthcheck_cli', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='kyriakoskat7',
        database='toll_management_database'
    )

@healthcheck_cli_bp.route('/admin/healthcheck', methods = ['GET'])
def healthcheck_cli():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Queries for system statistics
        cursor.execute("SELECT COUNT(*) FROM toll")
        n_stations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tag")
        n_tags = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pass")
        n_passes = cursor.fetchone()[0]

        # Response data
        response = {
            "status": "OK",
            "dbconnection": f"Connected to {conn.server_host}:{conn.server_port}/{conn.database}",
            "n_stations": n_stations,
            "n_tags": n_tags,
            "n_passes": n_passes,
        }
        cursor.close()
        conn.close()
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"status": "FAILED", "error": str(e)}), 500
