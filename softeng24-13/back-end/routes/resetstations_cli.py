from flask import Blueprint, jsonify
import pandas as pd
import mysql.connector

resetstations_cli_bp = Blueprint('resetstations_cli', __name__)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='kyriakoskat7',
        database='toll_management_database'
    )

@resetstations_cli_bp.route('/admin/resetstations', methods=['POST'])
def resetstations_cli():
    try:
        tollstations_path = 'tollstations2024.csv'

        # Load CSV data
        try:
            toll_data = pd.read_csv(tollstations_path)
        except FileNotFoundError:
            return jsonify({"status": "failed", "info": f"File {tollstations_path} not found"}), 400
        except pd.errors.EmptyDataError:
            return jsonify({"status": "failed", "info": "Tollstations CSV is empty"}), 400

        # Validate required columns
        required_columns_toll = {'OpID', 'Operator', 'Email', 'TollID', 'Name', 'Road', 'Lat', 'Long', 'PM', 'Price1', 'Price2', 'Price3', 'Price4'}
        if not required_columns_toll.issubset(toll_data.columns):
            return jsonify({"status": "failed", "info": "Missing columns in tollstations CSV"}), 400

        # Database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Fill Operator Table
        operators = toll_data[['OpID', 'Operator', 'Email']].drop_duplicates()
        operator_query = """
        INSERT IGNORE INTO operator (op_id, op_name, email)
        VALUES (%s, %s, %s)
        """
        for _, row in operators.iterrows():
            cursor.execute(operator_query, (row['OpID'], row['Operator'], row['Email']))

        # Fill Toll Table
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

        # Commit changes
        connection.commit()
        return jsonify({"status": "OK"}), 200

    except mysql.connector.Error as db_err:
        return jsonify({"status": "failed", "info": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"status": "failed", "info": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
