import pandas as pd
import mysql.connector

# Load CSV data
csv_path = 'tollstations2024.csv'
data = pd.read_csv(csv_path)

passes_data_path = 'passes-sample.csv'  
passes_data = pd.read_csv(passes_data_path)

# Connect to the database
connection = mysql.connector.connect(
    host='localhost',         # Replace with your host
    user='root',              # Replace with your username
    password='kyriakoskat7',      # Replace with your password
    database='toll_management_database'  # Replace with your database name
)
cursor = connection.cursor()

#Fill Operator
operators = data[['OpID', 'Operator', 'Email']].drop_duplicates()
insert_query = """
INSERT IGNORE INTO operator (op_id, op_name, email)
VALUES (%s, %s, %s)
"""
for _, row in operators.iterrows():
    cursor.execute(insert_query, (row['OpID'], row['Operator'], row['Email']))


#Fill Tags   
tags = passes_data[['tagRef', 'tagHomeID']].drop_duplicates()
tag_insert_query = """
INSERT IGNORE INTO tag (tag_ref, tag_home, op_id)
VALUES (%s, %s, %s)
"""
for _, row in tags.iterrows():
    cursor.execute(tag_insert_query, (row['tagRef'], row['tagHomeID'], row['tagHomeID']))



#Fill Toll
insert_query = """
INSERT INTO toll (
    toll_id, toll_name, op_id, road, latitude, longitude, PM, price1, price2, price3, price4
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
for _, row in data.iterrows():
    cursor.execute(insert_query, (
        row['TollID'], row['Name'], row['OpID'], row['Road'], 
        row['Lat'], row['Long'], row['PM'], row['Price1'],  
        row['Price2'], row['Price3'], row['Price4']
    ))

#Fill Pass
pass_insert_query = """
INSERT INTO pass (toll_id, tag_ref, charge, `timestamp`)
VALUES (%s, %s, %s, %s)
"""

# Loop through the rows in the DataFrame and execute the query
for _, row in passes_data.iterrows():
    cursor.execute(pass_insert_query, (
        row['tollID'],       # Extract toll_id
        row['tagRef'],       # Extract tag_ref
        row['charge'],       # Extract charge
        row['timestamp']     # Extract timestamp from the first row in the Excel
    ))

# Commit changes and close the connection
connection.commit()
cursor.close()
connection.close()

print("Database populated successfully!")
