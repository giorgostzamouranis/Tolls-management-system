from flask import Blueprint, Response, jsonify, request, render_template
from collections import OrderedDict
from datetime import datetime
import mysql.connector
import json
import csv
from io import StringIO

pass_analysis_cli_bp = Blueprint('pass_analysis_cli', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='kyriakoskat7',
        database='toll_management_database'
    )


@pass_analysis_cli_bp.route('/passAnalysis/<stationOpID>/<tagOpID>/<date_from>/<date_to>', methods=['GET'])
def pass_analysis_cli(stationOpID, tagOpID, date_from, date_to):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            p.pass_id AS passID,
            p.toll_id AS stationID,
            p.timestamp,
            p.tag_ref AS tagID,
            p.charge AS passCharge
        FROM pass p
        INNER JOIN toll t ON p.toll_id = t.toll_id
        INNER JOIN tag tg ON p.tag_ref = tg.tag_ref
        WHERE 
            t.op_id = %s AND
            tg.tag_home = %s AND
            DATE(p.timestamp) BETWEEN %s AND %s
        ORDER BY p.timestamp
        """
        cursor.execute(query, (stationOpID, tagOpID, date_from, date_to))
        passes = cursor.fetchall()

        response_format = request.args.get('format', 'json')

        if response_format == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['passID', 'stationID', 'timestamp', 'tagID', 'passCharge'])
            for row in passes:
                writer.writerow([row['passID'], row['stationID'], row['timestamp'], row['tagID'], row['passCharge']])
            
            response = Response(output.getvalue(), mimetype='text/csv')
            response.headers["Content-Disposition"] = "attachment; filename=pass_analysis.csv"
            return response

        response = OrderedDict([
            ("stationOpID", stationOpID),
            ("tagOpID", tagOpID),
            ("requestTimestamp", datetime.now().isoformat()),
            ("periodFrom", date_from),
            ("periodTo", date_to),
            ("nPasses", len(passes)),
            ("passList", [])
        ])
        for idx, p in enumerate(passes):
            response["passList"].append(OrderedDict([
                ("passIndex", idx + 1),
                ("passID", p["passID"]),
                ("stationID", p["stationID"]),
                ("timestamp", p["timestamp"].strftime("%Y-%m-%d %H:%M:%S")),
                ("tagID", p["tagID"]),
                ("passCharge", float(p["passCharge"]))
            ]))

        cursor.close()
        conn.close()

        return Response(json.dumps(response, indent=4), mimetype="application/json")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
