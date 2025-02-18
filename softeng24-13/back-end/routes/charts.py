# routes/charts.py
from flask import Blueprint, render_template, request
import mysql.connector
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for plotting
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime

charts_bp = Blueprint('charts', __name__, template_folder='templates')

def get_image_from_plot():
    """
    Saves the current Matplotlib figure to a PNG in memory,
    encodes it as Base64, and returns the string.
    """
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return image_base64

# ------------------------------
# 1. Operator Expenditures Pie Chart
# ------------------------------
@charts_bp.route('/operator_expenditures', methods=['GET', 'POST'])
def operator_expenditures():
    image = None
    error = None
    operators = []

    # Connect to the database and fetch operator names in alphabetical order.
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='kyriakoskat7',  # Replace with your actual password
            database='toll_management_database'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT op_name FROM operator ORDER BY op_name")
        operators = [row[0] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        error = f"Database connection error: {err}"
        return render_template('operator_expenditures.html', error=error, operators=operators)

    if request.method == 'POST':
        owner_operator = request.form.get('owner_operator')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        # Build the allowed operators list: all operators except the selected one.
        allowed_ops = [op for op in operators if op.lower() != owner_operator.lower()]
        if not allowed_ops:
            error = "No other allowed operators for display."
            cursor.close()
            connection.close()
            return render_template('operator_expenditures.html', error=error, operators=operators)

        # Create placeholders for the allowed operators list
        placeholders = ", ".join(["%s"] * len(allowed_ops))
        query = f"""
        SELECT toll_operator.op_name, SUM(pass.charge) AS total_charge
        FROM pass
        JOIN toll ON pass.toll_id = toll.toll_id
        JOIN operator AS toll_operator ON toll.op_id = toll_operator.op_id
        JOIN tag ON pass.tag_ref = tag.tag_ref
        JOIN operator AS tag_operator ON tag.op_id = tag_operator.op_id
        WHERE tag_operator.op_name = %s
          AND toll_operator.op_name <> %s
          AND toll_operator.op_name IN ({placeholders})
          AND pass.timestamp >= %s
          AND pass.timestamp <= %s
        GROUP BY toll_operator.op_name
        """
        params = [owner_operator, owner_operator] + allowed_ops + [start_date, end_date]
        try:
            cursor.execute(query, params)
            results = cursor.fetchall()
        except mysql.connector.Error as err:
            error = f"Query error: {err}"
            cursor.close()
            connection.close()
            return render_template('operator_expenditures.html', error=error, operators=operators)

        # Build a dictionary of expenditures for each allowed operator
        expenditures = {op: 0 for op in allowed_ops}
        for op_name, total_charge in results:
            expenditures[op_name] = float(total_charge) if total_charge is not None else 0.0

        cursor.close()
        connection.close()

        labels = allowed_ops
        sizes = [expenditures[op] for op in allowed_ops]

        # Helper to display absolute amounts on the pie slices
        def make_autopct(values):
            total = sum(values)
            def my_autopct(pct):
                absolute = pct / 100 * total
                return f'{absolute:.2f} €'
            return my_autopct

        plt.figure(figsize=(10, 6))
        plt.pie(sizes, labels=labels, autopct=make_autopct(sizes), startangle=90)
        plt.title(f'Money spent from tags of "{owner_operator}"\n to other operators\n({start_date} έως {end_date})')
        plt.axis('equal')
        plt.tight_layout()
        image = get_image_from_plot()
    else:
        # For GET requests, close the connection.
        cursor.close()
        connection.close()

    return render_template('operator_expenditures.html', image=image, error=error, operators=operators)

# ------------------------------
# 2. Toll Traffic (Line Chart)
# ------------------------------
@charts_bp.route('/toll_traffic', methods=['GET', 'POST'])
def toll_traffic():
    image = None
    error = None
    toll_stations = []
    
    # Connect to the database and fetch distinct toll station names in alphabetical order
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='kyriakoskat7',  # Replace with your actual password
            database='toll_management_database'
        )
        cursor = connection.cursor()
        # Here we add ORDER BY toll_name to sort the names alphabetically
        cursor.execute("SELECT DISTINCT toll_name FROM toll ORDER BY toll_name")
        toll_stations = [row[0] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        error = f"Database connection error: {err}"
        return render_template('toll_traffic.html', error=error, toll_stations=toll_stations)
    
    if request.method == 'POST':
        toll_station_name = request.form.get('toll_station_name')
        month_name = request.form.get('month_name')
        year = request.form.get('year')
        
        # Convert month and year into a date range
        try:
            start_date = datetime.strptime(f"{month_name} {year}", "%B %Y")
            if start_date.month == 12:
                end_date = datetime(start_date.year + 1, 1, 1)
            else:
                end_date = datetime(start_date.year, start_date.month + 1, 1)
        except ValueError as ve:
            error = f"Date conversion error: {ve}"
            cursor.close()
            connection.close()
            return render_template('toll_traffic.html', error=error, toll_stations=toll_stations)
        
        try:
            query = """
                SELECT p.`timestamp`
                FROM pass p
                JOIN toll t ON p.toll_id = t.toll_id
                WHERE t.toll_name = %s
                  AND p.timestamp >= %s
                  AND p.timestamp < %s;
            """
            cursor.execute(query, (toll_station_name, start_date, end_date))
            results = cursor.fetchall()
        except mysql.connector.Error as err:
            error = f"Query error: {err}"
            cursor.close()
            connection.close()
            return render_template('toll_traffic.html', error=error, toll_stations=toll_stations)
        
        hourly_counts = {hour: 0 for hour in range(24)}
        for (ts,) in results:
            hour = ts.hour
            hourly_counts[hour] += 1
        
        hours = list(hourly_counts.keys())
        counts = list(hourly_counts.values())
        
        plt.figure(figsize=(10, 6))
        plt.plot(hours, counts, marker='o', linestyle='-', color='skyblue')
        plt.xlabel('Hour of the Day')
        plt.ylabel('Number of Passes')
        plt.title(f'Toll Traffic at {toll_station_name} ({month_name} {year})')
        plt.xticks(hours)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        image = get_image_from_plot()
    
    cursor.close()
    connection.close()
    return render_template('toll_traffic.html', image=image, error=error, toll_stations=toll_stations)

# ------------------------------
# 3. Toll Traffic Heatmap
# ------------------------------
@charts_bp.route('/toll_traffic_heatmap', methods=['GET', 'POST'])
def toll_traffic_heatmap():
    image = None
    error = None
    toll_stations = []
    
    # Connect to the database and fetch distinct toll station names in alphabetical order
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='kyriakoskat7',  # Replace with your actual password
            database='toll_management_database'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT toll_name FROM toll ORDER BY toll_name")
        toll_stations = [row[0] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        error = f"Database connection error: {err}"
        return render_template('toll_traffic_heatmap.html', error=error, toll_stations=toll_stations)
    
    if request.method == 'POST':
        toll_station_name = request.form.get('toll_station_name')
        month_name = request.form.get('month_name')
        year = request.form.get('year')
        
        # Convert month and year into a date range
        try:
            start_date = datetime.strptime(f"{month_name} {year}", "%B %Y")
            if start_date.month == 12:
                end_date = datetime(start_date.year + 1, 1, 1)
            else:
                end_date = datetime(start_date.year, start_date.month + 1, 1)
        except ValueError as ve:
            error = f"Date conversion error: {ve}"
            cursor.close()
            connection.close()
            return render_template('toll_traffic_heatmap.html', error=error, toll_stations=toll_stations)
        
        # Query toll traffic data using a date range
        try:
            query = """
                SELECT p.`timestamp`
                FROM pass p
                JOIN toll t ON p.toll_id = t.toll_id
                WHERE t.toll_name = %s
                  AND p.timestamp >= %s
                  AND p.timestamp < %s;
            """
            cursor.execute(query, (toll_station_name, start_date, end_date))
            results = cursor.fetchall()
        except mysql.connector.Error as err:
            error = f"Query error: {err}"
            cursor.close()
            connection.close()
            return render_template('toll_traffic_heatmap.html', error=error, toll_stations=toll_stations)
        
        # Create a 7x24 heatmap (days of the week by hour of day)
        heatmap_data = [[0 for _ in range(24)] for _ in range(7)]
        for (ts,) in results:
            day_of_week = ts.weekday()  # Monday=0, Sunday=6
            hour = ts.hour
            heatmap_data[day_of_week][hour] += 1
        
        plt.figure(figsize=(12, 6))
        sns.heatmap(heatmap_data, fmt="d", cmap="Oranges",
                    xticklabels=[f"{h}:00" for h in range(24)],
                    yticklabels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        plt.xlabel("Hour of the day")
        plt.ylabel("Day of the week")
        plt.title(f"Traffic Heatmap at {toll_station_name} ({month_name} {year})")
        plt.tight_layout()
        image = get_image_from_plot()
    
    cursor.close()
    connection.close()
    return render_template('toll_traffic_heatmap.html', image=image, error=error, toll_stations=toll_stations)

# ------------------------------
# 4. Daily Money Spent Bar Chart
# ------------------------------
@charts_bp.route('/money_spent', methods=['GET', 'POST'])
def money_spent():
    image = None
    error = None
    operators = []

    # Connect to the database and fetch operator names in alphabetical order
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='kyriakoskat7',  # Replace with your actual password
            database='toll_management_database'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT op_name FROM operator ORDER BY op_name")
        operators = [row[0] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        error = f"Database connection error: {err}"
        return render_template('money_spent.html', error=error, operators=operators)

    if request.method == 'POST':
        operator_name = request.form.get('operator_name')
        month_name = request.form.get('month_name')
        year = request.form.get('year')

        # Retrieve operator ID for the chosen operator
        try:
            cursor.execute("SELECT op_id FROM operator WHERE op_name = %s", (operator_name,))
            result = cursor.fetchone()
            if not result:
                error = f"No operator found with name {operator_name}"
                cursor.close()
                connection.close()
                return render_template('money_spent.html', error=error, operators=operators)
            operator_id = result[0]
        except mysql.connector.Error as err:
            error = f"Query error: {err}"
            cursor.close()
            connection.close()
            return render_template('money_spent.html', error=error, operators=operators)

        # Query daily money spent data
        query = """
            SELECT DAY(p.`timestamp`) AS day_in_month, SUM(p.charge) AS total_spent
            FROM pass p
            JOIN tag t ON p.tag_ref = t.tag_ref
            WHERE t.op_id = %s
              AND YEAR(p.`timestamp`) = %s
              AND MONTHNAME(p.`timestamp`) = %s
            GROUP BY DAY(p.`timestamp`)
            ORDER BY day_in_month;
        """
        try:
            cursor.execute(query, (operator_id, year, month_name))
            results = cursor.fetchall()
        except mysql.connector.Error as err:
            error = f"Query error: {err}"
            cursor.close()
            connection.close()
            return render_template('money_spent.html', error=error, operators=operators)

        # Build a dictionary for days 1-31 (initialize to 0) and update with query results
        daily_spent = {day: 0.0 for day in range(1, 32)}
        for day, total in results:
            daily_spent[day] = float(total)

        cursor.close()
        connection.close()

        days = sorted(daily_spent.keys())
        spent_values = [daily_spent[d] for d in days]

        plt.figure(figsize=(10, 6))
        bars = plt.bar(days, spent_values, color='skyblue')
        plt.xlabel('Day of the Month')
        plt.ylabel('Revenue (€)')
        plt.title(f'Revenue for Operator "{operator_name}" in {month_name} {year}')
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width()/2, height, f'{height:.2f}', ha='center', va='bottom')
        plt.xticks(days)
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        image = get_image_from_plot()

    cursor.close()
    connection.close()
    return render_template('money_spent.html', image=image, error=error, operators=operators)
# ------------------------------
# 5. Revenues by Vehicle Type Bar Chart
# ------------------------------
@charts_bp.route('/revenues_by_vehicle_type', methods=['GET', 'POST'])
def revenues_by_vehicle_type():
    image = None
    error = None
    operators = []
    
    # Connect to the database and fetch operator names in alphabetical order
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='kyriakoskat7',  # Replace with your actual password
            database='toll_management_database'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT op_name FROM operator ORDER BY op_name")
        operators = [row[0] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        error = f"Database connection error: {err}"
        return render_template('revenues_by_vehicle_type.html', error=error, operators=operators)
    
    if request.method == 'POST':
        operator_name = request.form.get('operator_name')
        
        try:
            query = """
                SELECT 
                  CASE 
                    WHEN p.charge = t.price1 THEN 'Price 1'
                    WHEN p.charge = t.price2 THEN 'Price 2'
                    WHEN p.charge = t.price3 THEN 'Price 3'
                    WHEN p.charge = t.price4 THEN 'Price 4'
                    ELSE 'Other'
                  END AS price_type,
                  SUM(p.charge) AS total_revenue
                FROM pass p
                JOIN toll t ON p.toll_id = t.toll_id
                JOIN operator o ON t.op_id = o.op_id
                WHERE o.op_name = %s
                GROUP BY price_type;
            """
            cursor.execute(query, (operator_name,))
            results = cursor.fetchall()
        except mysql.connector.Error as err:
            error = f"Query error: {err}"
            cursor.close()
            connection.close()
            return render_template('revenues_by_vehicle_type.html', error=error, operators=operators)
        
        # Build a dictionary for the expected categories
        revenue_dict = {"Price 1": 0, "Price 2": 0, "Price 3": 0, "Price 4": 0}
        for price_type, total_revenue in results:
            if price_type in revenue_dict:
                revenue_dict[price_type] = float(total_revenue) if total_revenue is not None else 0.0
        
        categories = list(revenue_dict.keys())
        revenues = [revenue_dict[cat] for cat in categories]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(categories, revenues, color='skyblue')
        plt.xlabel('Vehicle Type (Price Category)')
        plt.ylabel('Revenue (€)')
        plt.title(f'Total Revenue by Vehicle Type for Operator: {operator_name}')
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, height, f'{height:.2f}', ha='center', va='bottom')
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        image = get_image_from_plot()
    
    cursor.close()
    connection.close()
    return render_template('revenues_by_vehicle_type.html', image=image, error=error, operators=operators)
# ------------------------------
# 6. Top 3 Roads by Passes Bar Chart
# ------------------------------
@charts_bp.route('/top3_roads_by_passes', methods=['GET', 'POST'])
def top3_roads_by_passes():
    image = None
    error = None
    operators = []

    # Connect to the database and fetch operator names in alphabetical order
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='kyriakoskat7',  # Replace with your actual password
            database='toll_management_database'
        )
        cursor = connection.cursor()
        cursor.execute("SELECT op_name FROM operator ORDER BY op_name")
        operators = [row[0] for row in cursor.fetchall()]
    except mysql.connector.Error as err:
        error = f"Database connection error: {err}"
        return render_template('top3_roads_by_passes.html', error=error, operators=operators)
    
    if request.method == 'POST':
        operator_name = request.form.get('operator_name')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        try:
            query = """
                SELECT t.road, COUNT(*) AS total_passes
                FROM pass p
                JOIN toll t ON p.toll_id = t.toll_id
                JOIN operator o ON t.op_id = o.op_id
                WHERE o.op_name = %s
                  AND p.timestamp >= %s
                  AND p.timestamp <= %s
                GROUP BY t.road
                ORDER BY total_passes DESC
                LIMIT 3;
            """
            cursor.execute(query, (operator_name, start_date, end_date))
            results = cursor.fetchall()
        except mysql.connector.Error as err:
            error = f"Query error: {err}"
            cursor.close()
            connection.close()
            return render_template('top3_roads_by_passes.html', error=error, operators=operators)
        
        roads = [row[0] for row in results]
        passes_count = [row[1] for row in results]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(roads, passes_count, color='skyblue')
        plt.xlabel("Road")
        plt.ylabel("Number of Passes")
        plt.title(f"Top 3 Roads with Most Passes for Operator: {operator_name}\n(From {start_date} to {end_date})")
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, height, f'{height}', ha='center', va='bottom')
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        image = get_image_from_plot()
    
    cursor.close()
    connection.close()
    return render_template('top3_roads_by_passes.html', image=image, error=error, operators=operators)