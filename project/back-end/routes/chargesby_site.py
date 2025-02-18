from collections import OrderedDict
from flask import Response, Blueprint, jsonify, request, render_template
from datetime import datetime
import mysql.connector
import json
import csv
from io import StringIO

charges_by_site_bp = Blueprint('charges_by_site_bp', __name__)

# Database connection function
def connect_to_db():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='kyriakoskat7',  # Replace with your actual password
            database='toll_management_database'
        )
    except mysql.connector.Error as err:
        raise Exception(f"Database connection failed: {err}")

# Endpoint to render the Charges By webpage
@charges_by_site_bp.route('/chargesBy', methods=['GET'])
def charges_by_page():
    return render_template('charges_by.html')

# API Endpoint for /chargesBy/:tollOpID/:date_from/:date_to
@charges_by_site_bp.route('/api/chargesBy/<string:tollOpID>/<string:date_from>/<string:date_to>', methods=['GET'])
def charges_by(tollOpID, date_from, date_to):
    try:
        # Validate date formats
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            if date_from_obj > date_to_obj:
                return jsonify({"error": "date_from must be earlier than or equal to date_to."}), 400
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Connect to the database
        connection = connect_to_db()
        cursor = connection.cursor(dictionary=True)

        # Query for passes and cost per visiting operator
        query = """
        SELECT 
            tag_operator.op_id AS visitingOpID,
            COUNT(pass.pass_id) AS nPasses,
            SUM(pass.charge) AS passesCost
        FROM pass
        JOIN toll ON pass.toll_id = toll.toll_id
        JOIN operator AS toll_operator ON toll.op_id = toll_operator.op_id
        JOIN tag ON pass.tag_ref = tag.tag_ref
        JOIN operator AS tag_operator ON tag.op_id = tag_operator.op_id
        WHERE toll_operator.op_id = %s 
          AND toll_operator.op_id != tag_operator.op_id
          AND pass.timestamp BETWEEN %s AND %s
        GROUP BY tag_operator.op_id
        ORDER BY tag_operator.op_id;
        """
        cursor.execute(query, (tollOpID, date_from, date_to))
        results = cursor.fetchall()

        # Check response format
        response_format = request.args.get('format', 'json').lower()

        if response_format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['visitingOpID', 'nPasses', 'passesCost'])
            for row in results:
                writer.writerow([row['visitingOpID'], row['nPasses'], float(row['passesCost'])])

            response = Response(output.getvalue(), mimetype='text/csv')
            response.headers["Content-Disposition"] = "attachment; filename=charges_by.csv"
            return response

        # Build JSON response
        response = OrderedDict([
            ("tollOpID", tollOpID),
            ("requestTimestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ("periodFrom", date_from),
            ("periodTo", date_to),
            ("vOpList", [])
        ])

        for row in results:
            response["vOpList"].append(OrderedDict([
                ("visitingOpID", row["visitingOpID"]),
                ("nPasses", row["nPasses"]),
                ("passesCost", float(row["passesCost"]))
            ]))

        cursor.close()
        connection.close()

        return Response(
            json.dumps(response, ensure_ascii=False, indent=2),
            content_type="application/json"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
