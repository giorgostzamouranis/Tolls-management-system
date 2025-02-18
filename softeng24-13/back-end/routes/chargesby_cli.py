from collections import OrderedDict
from flask import Response, Blueprint
from datetime import datetime
import mysql.connector
import json

charges_by_cli_bp = Blueprint('charges_by_cli_bp', __name__)

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

# Endpoint for the API /chargesBy/:tollOpID/:date_from/:date_to
@charges_by_cli_bp.route('/chargesBy/<string:tollOpID>/<string:date_from>/<string:date_to>', methods=['GET'])
def charges_by(tollOpID, date_from, date_to):
    try:
        # Validate date formats
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            if date_from_obj > date_to_obj:
                return Response(
                    json.dumps(
                        OrderedDict([("error", "date_from must be earlier than or equal to date_to.")]),
                        ensure_ascii=False,
                        indent=2
                    ),
                    content_type="application/json",
                    status=400
                )
        except ValueError:
            return Response(
                json.dumps(
                    OrderedDict([("error", "Invalid date format. Use YYYY-MM-DD.")]),
                    ensure_ascii=False,
                    indent=2
                ),
                content_type="application/json",
                status=400
            )

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

        # Build the ordered response
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

        # Close database connections
        cursor.close()
        connection.close()

        # Return ordered JSON response
        return Response(
            json.dumps(response, ensure_ascii=False, indent=2),
            content_type="application/json"
        )

    except mysql.connector.Error as db_err:
        # Log and return database-related errors
        error_message = f"Database error: {db_err}"
        print(error_message)
        return Response(
            json.dumps(
                OrderedDict([("error", error_message)]),
                ensure_ascii=False,
                indent=2
            ),
            content_type="application/json",
            status=500
        )
    except Exception as e:
        # Log and return unexpected errors
        error_message = f"Unexpected error: {e}"
        print(error_message)
        return Response(
            json.dumps(
                OrderedDict([("error", error_message)]),
                ensure_ascii=False,
                indent=2
            ),
            content_type="application/json",
            status=500
        )
