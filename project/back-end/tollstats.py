import mysql.connector
import matplotlib.pyplot as plt
import seaborn as sns



# Fist graph: Pie που δείχνει τα χρήματα που ξοδευτηκαν από tags του λειτουργου X σε άλλους λειτουργους.
# Παράμετροι: είσοδοσ του λειτουργού X (owner tag) και έξοδοσ bar plot χρημάτων
def plot_operator_expenditures(owner_operator, start_date, end_date):
    # Σύνδεση με τη βάση δεδομένων
    try:
        connection = mysql.connector.connect(
            host='localhost',         # Replace with your host
            user='root',              # Replace with your username
            password='kyriakoskat7',      # Replace with your password
            database='toll_management_database'
        )
    except mysql.connector.Error as err:
        print(f"Σφάλμα σύνδεσης: {err}")
        return

    cursor = connection.cursor()

    # Ορισμός των επιτρεπόμενων λειτουργών για εμφάνιση
    allowed_ops = ["aegeanmotorway", "egnatia", "gefyra", "kentrikiodos",
                   "moreas", "naodos", "neaodos", "olympiaodos"]
    # Αφαίρεση του owner_operator από τη λίστα (case-insensitive)
    allowed_ops = [op for op in allowed_ops if op.lower() != owner_operator.lower()]
    
    if not allowed_ops:
        print("Δεν υπάρχουν άλλοι επιτρεπόμενοι λειτουργοί για εμφάνιση.")
        cursor.close()
        connection.close()
        return

    # Δημιουργία των placeholders για το IN clause
    placeholders = ", ".join(["%s"] * len(allowed_ops))
    
    # Προσθέτουμε κριτήρια ημερομηνιών (start_date, end_date) στο WHERE
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

    # Οι παράμετροι: 
    # 1) owner_operator (για τα tags)
    # 2) owner_operator (ώστε να αποκλειστεί ο ίδιος από τα tolls)
    # 3) allowed_ops (λίστα των υπολοίπων λειτουργών)
    # 4) start_date, end_date (φίλτρο ημερομηνιών)
    params = [owner_operator, owner_operator] + allowed_ops + [start_date, end_date]

    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        # Debug print: εμφάνιση αποτελεσμάτων
        print("Query results:", results)
    except mysql.connector.Error as err:
        print(f"Σφάλμα κατά την εκτέλεση του ερωτήματος: {err}")
        cursor.close()
        connection.close()
        return

    # Δημιουργούμε ένα λεξικό με αρχικές τιμές 0 για κάθε επιτρεπόμενο λειτουργό
    expenditures = {op: 0 for op in allowed_ops}
    for op_name, total_charge in results:
        expenditures[op_name] = float(total_charge) if total_charge is not None else 0.0

    cursor.close()
    connection.close()

    # Προετοιμασία δεδομένων για το pie chart
    labels = allowed_ops
    sizes = [expenditures[op] for op in allowed_ops]
    
    # Συνάρτηση για να εμφανίζει το απόλυτο ποσό (σε ευρώ) μέσα σε κάθε φέτα
    def make_autopct(values):
        total = sum(values)
        def my_autopct(pct):
            absolute = pct/100 * total
            return f'{absolute:.2f} €'
        return my_autopct

    # Δημιουργία του pie chart
    plt.figure(figsize=(10, 6))
    plt.pie(sizes, labels=labels, autopct=make_autopct(sizes), startangle=90)
    plt.title(
        f'Money spent from tags of "{owner_operator}" '
        f'to other operators\n({start_date} έως {end_date})'
    )
    plt.axis('equal')  # Εξασφαλίζει ότι το pie chart έχει κυκλική μορφή.
    plt.tight_layout()
    plt.show()












# Second grpah: Διάγραμμα που δέιχνει για έναν σταθμό διοδίων Χ  τις διελύεσεις (δικών μασ tags και μη) ανά ώρα.
# Παράμετροι: είσοδοσ του σταθμου διοδίων X  και έξοδοσ plot διελεύσεων απο τον σταθμο αυτο στην παροδο του χρονου.
#Γραφημα: Αξονασ y διελευεσεισ, αξονασ x 24 ώρα ΑΜ / ωρα PM (άρα 24 ωρες)

def plot_toll_traffic(toll_station_name, month_name, year):
    """
    Δημιουργεί ένα γραμμικό διάγραμμα των διελεύσεων (passes) για έναν συγκεκριμένο σταθμό διοδίων (toll_station_name),
    φιλτραρισμένο για τον μήνα (month_name) και το έτος (year).
    
    :param toll_station_name: Το όνομα του σταθμού διοδίων.
    :param month_name: Όνομα του μήνα στα Αγγλικά (π.χ. "January").
    :param year: Έτος σε ακέραια μορφή (π.χ. 2023).
    """

    # Σύνδεση με τη βάση δεδομένων
    try:
        connection = mysql.connector.connect(
            host='localhost',         # Replace with your host
            user='root',              # Replace with your username
            password='kyriakoskat7',      # Replace with your password
            database='toll_management_database'
        )
    except mysql.connector.Error as err:
        print(f"Σφάλμα σύνδεσης: {err}")
        return

    cursor = connection.cursor()

    # Ερώτημα για ανάκτηση των timestamps των διελεύσεων, φιλτραρισμένο για έναν μήνα (με βάση το όνομα) και συγκεκριμένο έτος
    query = """
    SELECT p.`timestamp`
    FROM pass p
    JOIN toll t ON p.toll_id = t.toll_id
    WHERE t.toll_name = %s
      AND MONTHNAME(p.`timestamp`) = %s
      AND YEAR(p.`timestamp`) = %s;
    """
    try:
        cursor.execute(query, (toll_station_name, month_name, year))
        results = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Σφάλμα κατά την εκτέλεση του ερωτήματος: {err}")
        cursor.close()
        connection.close()
        return

    # Δημιουργία λεξικού με τις ώρες (0-23) ως κλειδιά και πλήθος διελεύσεων ως τιμές
    hourly_counts = {hour: 0 for hour in range(24)}
    
    for (ts,) in results:
        hour = ts.hour  # Παίρνουμε την ώρα από το timestamp
        hourly_counts[hour] += 1

    # Προετοιμασία δεδομένων για το γράφημα
    hours = list(hourly_counts.keys())
    counts = list(hourly_counts.values())

    # Συνάρτηση μετατροπής της ώρας σε μορφή AM/PM (προαιρετική, για ευανάγνωστες ετικέτες)
    def hour_to_ampm(hour):
        if hour == 0:
            return "12 AM"
        elif hour < 12:
            return f"{hour} AM"
        elif hour == 12:
            return "12 PM"
        else:
            return f"{hour - 12} PM"

    x_labels = [hour_to_ampm(hour) for hour in hours]

    # Δημιουργία του γραμμικού διαγράμματος με τις επιθυμητές μορφοποιήσεις
    plt.figure(figsize=(10, 6))
    plt.plot(hours, counts, marker='o', linestyle='-', color='skyblue')
    plt.xlabel('Hour of the day')
    plt.ylabel('Number of passes')
    plt.title(f'Traffic at the toll station: {toll_station_name}\n({month_name} {year})')
    plt.xticks(hours, x_labels, rotation=45)  # Περιστροφή 45 μοιρών για καλύτερο spacing
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()


    # Κλείσιμο σύνδεσης
    cursor.close()
    connection.close()











#Third grpah: Heatmap που δέιχνει για έναν σταθμό διοδίων Χ τις διελύεσεις (δικών μασ tags και μη) ανά μέρα για εναν συγκεκριμενο μηνα.
# Παράμετροι: είσοδοσ του σταθμου διοδίων X  και μηνα 
def plot_toll_traffic_heatmap(toll_station_name, month_name, year):
    """
    Δημιουργεί heatmap της κίνησης ενός σταθμού διοδίων κατά τις ημέρες της εβδομάδας (γραμμές)
    και τις ώρες της ημέρας (στήλες), φιλτραρισμένο για συγκεκριμένο μήνα και έτος.
    
    :param toll_station_name: Το όνομα του σταθμού διοδίων.
    :param month_name: Το όνομα του μήνα στα Αγγλικά (π.χ. "January").
    :param year: Το έτος σε ακέραιο (π.χ. 2023).
    """
    try:
        connection = mysql.connector.connect(
            host='localhost',         # Replace with your host
            user='root',              # Replace with your username
            password='kyriakoskat7',      # Replace with your password
            database='toll_management_database'
        )
        cursor = connection.cursor()
        
        # Προσθέτουμε και το έτος στην WHERE συνθήκη
        query = """
        SELECT p.`timestamp`
        FROM pass p
        JOIN toll t ON p.toll_id = t.toll_id
        WHERE t.toll_name = %s
          AND MONTHNAME(p.`timestamp`) = %s
          AND YEAR(p.`timestamp`) = %s;
        """
        cursor.execute(query, (toll_station_name, month_name, year))
        results = cursor.fetchall()
        
    except mysql.connector.Error as err:
        print(f"Σφάλμα σύνδεσης ή εκτέλεσης ερωτήματος: {err}")
        return
    finally:
        cursor.close()
        connection.close()

    # Δημιουργούμε τον πίνακα 7 (μέρες) x 24 (ώρες) για το heatmap
    heatmap_data = [[0] * 24 for _ in range(7)]
    for (ts,) in results:
        day_of_week = ts.weekday()  # 0=Δευτέρα, 6=Κυριακή
        hour = ts.hour
        heatmap_data[day_of_week][hour] += 1

    plt.figure(figsize=(12, 6))
    sns.heatmap(
        heatmap_data,
        fmt="d",
        cmap="Oranges",
        xticklabels=[f"{h}:00" for h in range(24)],
        yticklabels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )
    plt.xlabel("Hour of the day")
    plt.ylabel("Day of the week")
    plt.title(f"Traffic Heatmap at '{toll_station_name}' in {month_name} {year}")
    plt.tight_layout()
    plt.show()









# Fourth graph: Bar plot διαγραμμα που δειχνει τα συνολικα εσοδα για τον λειτουργο Χ για καθε μερα του μηνα και του ετους που θα επιλεξει
#Παραμετροι: εισοδοσ λειτουργος Χ και εξοδος plot εσοδων ανα μηνα
# Γραφημα: αξονασ y έσοδα σε ευρω, αξονας x μερα
def plot_money_spent(operator_name, year, month_name):
    # Σύνδεση με τη βάση δεδομένων
    try:
        connection = mysql.connector.connect(
            host='localhost',         # Replace with your host
            user='root',              # Replace with your username
            password='kyriakoskat7',      # Replace with your password
            database='toll_management_database'
        )
    except mysql.connector.Error as err:
        print(f"Σφάλμα σύνδεσης: {err}")
        return

    cursor = connection.cursor()

    # Ανάκτηση op_id για τον συγκεκριμένο operator
    query_operator = "SELECT op_id FROM operator WHERE op_name = %s"
    try:
        cursor.execute(query_operator, (operator_name,))
        result = cursor.fetchone()
        if result is None:
            print(f"Δεν βρέθηκε operator με όνομα {operator_name}")
            cursor.close()
            connection.close()
            return
        operator_id = result[0]
    except mysql.connector.Error as err:
        print(f"Σφάλμα κατά την ανάκτηση του operator id: {err}")
        cursor.close()
        connection.close()
        return

    # Ερώτημα: Ανά ημέρα (DAY(p.timestamp)) ομαδοποιούμε και παίρνουμε τη SUM(p.charge),
    # φιλτράροντας με YEAR(...) και MONTHNAME(...).
    query = """
    SELECT DAY(p.`timestamp`) AS day_in_month, SUM(p.charge) AS total_spent
    FROM pass p
    JOIN tag t ON p.tag_ref = t.tag_ref
    WHERE t.op_id = %s
      AND YEAR(p.`timestamp`) = %s
      AND MONTHNAME(p.`timestamp`) = %s
    GROUP BY DAY(p.`timestamp`)
    ORDER BY day_in_month
    """

    try:
        cursor.execute(query, (operator_id, year, month_name))
        results = cursor.fetchall()  # [(day1, sum1), (day2, sum2), ...]
    except mysql.connector.Error as err:
        print(f"Σφάλμα κατά την εκτέλεση του ερωτήματος: {err}")
        cursor.close()
        connection.close()
        return

    # Κλείσιμο cursor/σύνδεσης
    cursor.close()
    connection.close()

    # Δημιουργούμε ένα λεξικό day -> 0 αρχικά, ώστε αν κάποιες ημέρες δεν έχουν διελεύσεις να φαίνονται ως 0
    daily_spent = {day: 0.0 for day in range(1, 32)}  # 1..31 (max ημέρες μήνα)
    for day_in_month, total_spent in results:
        daily_spent[day_in_month] = float(total_spent)

    # Προετοιμασία λιστών για το διάγραμμα
    days = sorted(daily_spent.keys())
    spent_values = [daily_spent[d] for d in days]

    # Δημιουργία του ραβδογράμματος
    plt.figure(figsize=(10, 6))
    bars = plt.bar(days, spent_values, color='skyblue')
    plt.xlabel('Day of the Month')
    plt.ylabel('Revenue (€)')
    plt.title(f'Revenue for Operator "{operator_name}" in {month_name} {year}')

    # Προσθήκη τιμών πάνω από κάθε μπάρα
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f'{height:.2f}',
                ha='center',
                va='bottom'
            )

    plt.xticks(days, days)  # Ετικέτες άξονα X
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()








# Fifth graph: Bar plot διαγραμμα που δειχνει τα συνολικα εσοδα για δεδομενο τυπο οχηματος
def plot_revenues_by_vehicle_type(operator_name):
    # Σύνδεση με τη βάση δεδομένων
    try:
        connection = mysql.connector.connect(
            host='localhost',         # Replace with your host
            user='root',              # Replace with your username
            password='kyriakoskat7',      # Replace with your password
            database='toll_management_database'
            )
    except mysql.connector.Error as err:
        print(f"Σφάλμα σύνδεσης: {err}")
        return

    cursor = connection.cursor()

    # Το query συγκρίνει το charge της διελεύσεως με τις τιμές price1, price2, price3, price4 του διοδίου.
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

    try:
        cursor.execute(query, (operator_name,))
        results = cursor.fetchall()
        # Debug: εμφάνιση αποτελεσμάτων
        print("Query results:", results)
    except mysql.connector.Error as err:
        print(f"Σφάλμα κατά την εκτέλεση του ερωτήματος: {err}")
        cursor.close()
        connection.close()
        return

    cursor.close()
    connection.close()

    # Ορισμός λεξικού με τις αναμενόμενες κατηγορίες
    revenue_dict = {"Price 1": 0, "Price 2": 0, "Price 3": 0, "Price 4": 0}
    

    for price_type, total_revenue in results:
        if price_type in revenue_dict:
            revenue_dict[price_type] = float(total_revenue) if total_revenue is not None else 0.0
        

    # Προετοιμασία δεδομένων για το bar plot
    categories = list(revenue_dict.keys())
    revenues = [revenue_dict[cat] for cat in categories]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(categories, revenues, color='skyblue')
    plt.xlabel('Vehicle Type (Price Category)')
    plt.ylabel('Revenue (€)')
    plt.title(f'Total Revenue by Vehicle Type for Operator: {operator_name}')

    # Εμφάνιση της ακριβούς τιμής πάνω από κάθε μπάρα
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2,
            height,
            f'{height:.2f}',
            ha='center',
            va='bottom'
        )

    plt.tight_layout()
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.show()









# Sixth graph: Bar plot διαγραμμα που δειχνει τους 3 δρομους με τις περισσοτερεσ διελευσεισ που ανηκουν σε εναν operator για εναν συγκεκριμενο διαστημα

def plot_top3_roads_by_passes(operator_name, start_date, end_date):
    """
    Δημιουργεί ένα ραβδόγραμμα (bar chart) που δείχνει τους 3 δρόμους με τις περισσότερες διελεύσεις
    για έναν συγκεκριμένο operator, φιλτραρισμένο ανάμεσα σε δύο ημερομηνίες (inclusive).
    
    :param operator_name: Το όνομα του λειτουργού (operator) που μας ενδιαφέρει.
    :param start_date: Η αρχική ημερομηνία σε μορφή "YYYY-MM-DD".
    :param end_date: Η τελική ημερομηνία σε μορφή "YYYY-MM-DD".
    """
    # Σύνδεση με τη βάση δεδομένων
    try:
        connection = mysql.connector.connect(
            host='localhost',         # Replace with your host
            user='root',              # Replace with your username
            password='kyriakoskat7',      # Replace with your password
            database='toll_management_database'
        )
    except mysql.connector.Error as err:
        print(f"Σφάλμα σύνδεσης: {err}")
        return

    cursor = connection.cursor()

    # Το query:
    # Ενώνουμε τον πίνακα pass με τον πίνακα toll και με τον operator.
    # Φιλτράρουμε τα διοδία ώστε να ληφθούν υπόψη μόνο εκείνα που ανήκουν
    # στον operator με όνομα operator_name και επιπλέον φιλτράρουμε
    # τις διελεύσεις με βάση τις pass.timestamp >= start_date και <= end_date.
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

    try:
        cursor.execute(query, (operator_name, start_date, end_date))
        results = cursor.fetchall()  # Λίστα πλειάδων: [(road1, count1), (road2, count2), (road3, count3)]
        print("Query results:", results)
    except mysql.connector.Error as err:
        print(f"Σφάλμα κατά την εκτέλεση του ερωτήματος: {err}")
        cursor.close()
        connection.close()
        return

    cursor.close()
    connection.close()

    # Επεξεργασία αποτελεσμάτων: δημιουργούμε λίστες με τα ονόματα των δρόμων και τον αριθμό διελεύσεων
    roads = [row[0] for row in results]
    passes_count = [row[1] for row in results]

    # Δημιουργία του ραβδογραφήματος
    plt.figure(figsize=(10, 6))
    bars = plt.bar(roads, passes_count, color='skyblue')
    plt.xlabel("Road")
    plt.ylabel("Number of Passes")
    plt.title(f"Top 3 Roads with Most Passes for Operator: {operator_name}\n"
              f"(From {start_date} to {end_date})")

    # Προσθήκη των ακριβών τιμών πάνω από κάθε μπάρα
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f'{height}',
            ha='center',
            va='bottom'
        )

    plt.tight_layout()
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    plt.show()






# Παράδειγμα χρήσης της συνάρτησης
if __name__ == "__main__":
    plot_operator_expenditures(
        owner_operator="aegeanmotorway",
        start_date="2022-01-01",
        end_date="2022-01-25"
    )


    plot_toll_traffic("Σταθμός Διοδίων Κλειδίου Μετωπικά (Προς Αθήνα)","January","2022")

    plot_toll_traffic_heatmap("Σταθμός Διοδίων Κλειδίου Μετωπικά (Προς Αθήνα)", "January", "2022")

    plot_money_spent("egnatia", 2022, "January")

    plot_revenues_by_vehicle_type("olympiaodos")

    plot_top3_roads_by_passes(
        operator_name="egnatia",
        start_date="2022-01-01",
        end_date="2022-01-25"
    )

