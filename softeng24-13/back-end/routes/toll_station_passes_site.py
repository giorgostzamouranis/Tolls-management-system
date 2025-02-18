from flask import Blueprint, Response, jsonify, request, render_template
from collections import OrderedDict
from datetime import datetime
import mysql.connector
import json
import io
import csv

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='kyriakoskat7',
        database='toll_management_database'
    )

toll_station_passes_site_bp = Blueprint('toll_station_passes', __name__)

@toll_station_passes_site_bp.route('/tollStationPasses', methods=['GET'])
def toll_station_passes_page():
    return render_template('toll_station_passes.html')

@toll_station_passes_site_bp.route('/api/tollStationPasses/<string:tollStationID>/<string:date_from>/<string:date_to>', methods=['GET'])
def toll_station_passes(tollStationID, date_from, date_to):
    try:
        # Validate date formats
        date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d')

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch the operator name for the toll station
        operator_query = """
        SELECT operator.op_name AS stationOperator
        FROM toll
        JOIN operator ON toll.op_id = operator.op_id
        WHERE toll.toll_id = %s;
        """
        cursor.execute(operator_query, (tollStationID,))
        operator_result = cursor.fetchone()
        if not operator_result:
            return Response(
                json.dumps({"error": "Toll station ID not found"}),
                status=404,
                mimetype='application/json'
            )

        station_operator = operator_result["stationOperator"]

        # Query for toll station passes
        passes_query = """
        SELECT 
            pass.pass_id AS passID, 
            pass.timestamp, 
            tag.tag_ref AS tagID, 
            operator.op_id AS tagProvider, 
            pass.charge AS passCharge, 
            CASE 
                WHEN tag.op_id = toll.op_id THEN 'home' 
                ELSE 'visitor' 
            END AS passType
        FROM pass
        JOIN toll ON pass.toll_id = toll.toll_id
        JOIN tag ON pass.tag_ref = tag.tag_ref
        JOIN operator ON tag.op_id = operator.op_id
        WHERE toll.toll_id = %s AND pass.timestamp BETWEEN %s AND %s
        ORDER BY pass.timestamp ASC;
        """
        cursor.execute(passes_query, (tollStationID, date_from, date_to))
        results = cursor.fetchall()

        # Construct the ordered JSON response (used if format is JSON)
        response_data = OrderedDict([
            ("stationID", tollStationID),
            ("stationOperator", station_operator),
            ("requestTimestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ("periodFrom", date_from),
            ("periodTo", date_to),
            ("nPasses", len(results)),
            ("passList", [])
        ])

        pass_list = []
        for idx, p in enumerate(results):
            pass_entry = OrderedDict([
                ("passIndex", idx + 1),
                ("passID", p["passID"]),
                ("timestamp", p["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(p["timestamp"], datetime) else str(p["timestamp"])),
                ("tagID", p["tagID"]),
                ("tagProvider", p["tagProvider"]),
                ("passType", p["passType"]),
                ("passCharge", float(p["passCharge"]))
            ])
            pass_list.append(pass_entry)
        response_data["passList"] = pass_list

        cursor.close()
        connection.close()

        # Check the requested format
        output_format = request.args.get('format', 'json').lower()
        if output_format == 'csv':
            # Create an in-memory CSV file
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header row (adjust headers as needed)
            writer.writerow(["passIndex", "passID", "timestamp", "tagID", "tagProvider", "passType", "passCharge"])
            
            # Write each pass row
            for p in pass_list:
                writer.writerow([
                    p["passIndex"],
                    p["passID"],
                    p["timestamp"],
                    p["tagID"],
                    p["tagProvider"],
                    p["passType"],
                    p["passCharge"]
                ])

            csv_output = output.getvalue()
            output.close()

            return Response(
                csv_output,
                mimetype='text/csv',
                headers={"Content-disposition": f"attachment; filename=toll_station_passes_{tollStationID}.csv"}
            )
        else:
            # Return JSON output
            return Response(
                json.dumps(response_data, indent=4),
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
