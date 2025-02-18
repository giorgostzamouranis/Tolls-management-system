import pandas as pd
import mysql.connector


def compute_setoff():
    # Connect to the database
    connection = mysql.connector.connect(
        host='localhost',         # Replace with your host
        user='root',              # Replace with your username
        password='kyriakoskat7',      # Replace with your password
        database='toll_management_database'  # Replace with your database name
    )
    cursor = connection.cursor()

    query = """
        INSERT INTO debt (debtor_id, receiver_id, amount)
        SELECT 
            tag_op.op_id AS debtor_id,
            toll_op.op_id AS receiver_id,
            SUM(pass.charge) AS amount
        FROM 
            pass
        JOIN 
            toll ON pass.toll_id = toll.toll_id
        JOIN 
            tag ON pass.tag_ref = tag.tag_ref
        JOIN 
            operator AS tag_op ON tag.op_id = tag_op.op_id
        JOIN 
            operator AS toll_op ON toll.op_id = toll_op.op_id
        WHERE 
            tag_op.op_id != toll_op.op_id  -- Only consider inter-operator transactions
        GROUP BY 
            tag_op.op_id, toll_op.op_id;
        """
    cursor.execute(query)

    # Step 1: Calculate Net Balances into a Temporary Table
    create_temp_table_query = """
    CREATE TEMPORARY TABLE net_balances AS
    SELECT 
        d1.debtor_id AS debtor_id,
        d1.receiver_id AS receiver_id,
        (d1.amount - IFNULL(d2.amount, 0)) AS net_amount
    FROM 
        debt d1
    LEFT JOIN 
        debt d2 ON d1.debtor_id = d2.receiver_id AND d1.receiver_id = d2.debtor_id
    WHERE 
        (d1.amount - IFNULL(d2.amount, 0)) != 0;
    """
    cursor.execute(create_temp_table_query)

    # Step 2: Clear the Current Debt Table
    clear_debt_table_query = "DELETE FROM debt;"
    cursor.execute(clear_debt_table_query)

    # Step 3: Insert Aggregated Balances
    insert_simplified_query = """
    INSERT INTO debt (debtor_id, receiver_id, amount)
    SELECT 
        debtor_id,
        receiver_id,
        SUM(ABS(net_amount)) AS amount
    FROM (
        SELECT 
            CASE 
                WHEN net_amount > 0 THEN debtor_id
                ELSE receiver_id
            END AS debtor_id,
            CASE 
                WHEN net_amount > 0 THEN receiver_id
                ELSE debtor_id
            END AS receiver_id,
            ABS(net_amount) AS net_amount
        FROM net_balances
        WHERE net_amount != 0
    ) AS simplified
    GROUP BY debtor_id, receiver_id;
    """
    cursor.execute(insert_simplified_query)

    # Commit the transaction
    connection.commit()

    # Close the connection
    cursor.close()
    connection.close()

    print("Setoff completed successfully!")

# Call the function to populate the debt table
compute_setoff()