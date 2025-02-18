from flask import Flask, Blueprint, Response, jsonify, render_template
import mysql.connector
from collections import OrderedDict
from datetime import datetime
import json

passes_cost_cli_bp = Blueprint('passes_cost_cli_bp', __name__)

# Function to connect to the database
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='kyriakoskat7',
        database='toll_management_database'
    )

# Endpoint για το API /passesCost/:tollOpID/:tagOpID/:date_from/:date_to
@passes_cost_cli_bp.route('/passesCost/<string:tollOpID>/<string:tagOpID>/<string:date_from>/<string:date_to>', methods=['GET'])
def passes_cost(tollOpID, tagOpID, date_from, date_to):
    try:
        # Validate date formats
        datetime.strptime(date_from, '%Y-%m-%d')
        datetime.strptime(date_to, '%Y-%m-%d')

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Updated Query
        query = """
        SELECT 
            COUNT(pass.pass_id) AS nPasses, 
            SUM(pass.charge) AS passesCost
        FROM pass
        JOIN toll ON pass.toll_id = toll.toll_id
        JOIN operator AS toll_operator ON toll.op_id = toll_operator.op_id
        JOIN tag ON pass.tag_ref = tag.tag_ref
        JOIN operator AS tag_operator ON tag.op_id = tag_operator.op_id
        WHERE 
            toll_operator.op_id = %s 
            AND tag_operator.op_id = %s
            AND DATE(pass.timestamp) BETWEEN %s AND %s;
        """
        cursor.execute(query, (tollOpID, tagOpID, date_from, date_to))
        result = cursor.fetchone()

        # Ensure proper ordering of the response
        response = OrderedDict([
            ("tollOpID", tollOpID),
            ("tagOpID", tagOpID),
            ("requestTimestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ("periodFrom", date_from),
            ("periodTo", date_to),
            ("nPasses", result["nPasses"] if result["nPasses"] is not None else 0),
            ("passesCost", float(result["passesCost"]) if result["passesCost"] is not None else 0.0)
        ])

        cursor.close()
        connection.close()

        # Return response with proper ordering
        return Response(
            json.dumps(response, indent=4),
            status=200,
            mimetype='application/json'
        )

    except ValueError:
        return Response(
            json.dumps({"error": "Invalid date format. Use YYYY-MM-DD."}),
            status=400,
            mimetype='application/json'
        )
    except mysql.connector.Error as db_err:
        return Response(
            json.dumps({"error": f"Database error: {db_err}"}),
            status=500,
            mimetype='application/json'
        )
    except Exception as e:
        return Response(
            json.dumps({"error": f"Internal server error: {e}"}),
            status=500,
            mimetype='application/json'
        )
