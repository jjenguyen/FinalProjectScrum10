from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'secret_key'

#cost matrix for flights
def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

# Function to establish database connection
def get_db_connection():
    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row
    return conn

#route to render the home page
@app.route('/')
def home():
    return render_template('home.html')

#route to handle admin login requests and display the login page
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        admin_user = conn.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        
        if not username or not password:
            error = "You must fill out all input fields."
        elif admin_user:
            session['admin_logged_in'] = True 
            return redirect(url_for('logged_in'))
        else:
            error = "Invalid login credentials. Please try again."

    return render_template('admin.html', error=error)

#route for the admin page once logged in, showing the seating chart and total sales
@app.route('/logged_in')
def logged_in():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))

    seating_chart = get_seating_chart_with_details()
    total_sales = calculate_total_sales()

    return render_template('logged_in.html', seating_chart=seating_chart, total_sales=total_sales)

#retrieves the seating chart details for the admin, including passenger info
def get_seating_chart_with_details():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    #retrieve all reservations
    cursor.execute("""
        SELECT seatRow, seatColumn, passengerName, eTicketNumber
        FROM reservations
        ORDER BY seatRow, seatColumn
    """)
    
    reservations = cursor.fetchall()
    conn.close()
    
    #initialize seating chart matrix with all seats open
    seating_chart = [[{'status': 'O', 'details': ''} for _ in range(4)] for _ in range(12)]
    
    #iterate through all reservations and update the seating chart
    for reservation in reservations:
        #adjust because our database stores rows and columns starting at index 0
        row_index = reservation['seatRow']
        col_index = reservation['seatColumn']
        details = f"Name: {reservation['passengerName']}, Ticket: {reservation['eTicketNumber']}"
        
        #makes sure the indexes are within the range before updating the seating_chart
        if 0 <= row_index < len(seating_chart) and 0 <= col_index < len(seating_chart[row_index]):
            seating_chart[row_index][col_index] = {'status': 'X', 'details': details}
    
    return seating_chart

#retrieves the seating chart for making reservations, showing only taken/open seats
def get_seating_chart_for_reservations():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    #retrieve all reservations
    cursor.execute("""
        SELECT seatRow, seatColumn
        FROM reservations
    """)
    
    reserved_seats = {f"{row['seatRow']}-{row['seatColumn']}": True for row in cursor.fetchall()}
    conn.close()
    
    #initialize seating chart matrix with all seats open
    seating_chart = [['O' for _ in range(4)] for _ in range(12)]
    
    #iterate through all reservations and update the seating chart
    for row_index in range(12):
        for col_index in range(4):
            if f"{row_index}-{col_index}" in reserved_seats:
                seating_chart[row_index][col_index] = 'X'
    
    return seating_chart

#route for handling seat reservations and displaying the reservation page
@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    error = None
    success_message = None
    #fetches the current seating chart details to display
    seating_chart = get_seating_chart()

    if request.method == 'POST':
        if 'firstName' not in request.form or not request.form['firstName'] or 'lastName' not in request.form or not request.form['lastName'] or 'seatRow' not in request.form or not request.form['seatRow'] or 'seatColumn' not in request.form or not request.form['seatColumn']:
            error = "You must fill out all input fields."
        else:
            first_name = request.form['firstName']
            last_name = request.form['lastName']
            seat_row = request.form['seatRow']
            seat_column = request.form['seatColumn']

            seat_row = int(seat_row) - 1
            seat_column = int(seat_column) - 1

            if seat_row < 0 or seat_row >= 12 or seat_column < 0 or seat_column >= 4:
                error = "Invalid seat selection. Please choose a valid seat."
            else:
                conn = get_db_connection()
                #checks if the seat is already reserved
                existing_reservation = conn.execute(
                    "SELECT * FROM reservations WHERE seatRow = ? AND seatColumn = ?", 
                    (seat_row, seat_column)
                ).fetchone()

                if existing_reservation:
                    error = f"Seat {seat_row + 1}-{seat_column + 1} is already taken. Please select another seat."
                else:
                    # generate reservation code with alternating characters from the first name and "INFOTC4320"
                    class_name = "INFOTC4320"
                    name_length = len(first_name)
                    class_name_length = len(class_name)

                    reservation_code_list = []

                    count = 0

                    # add alternating characters until the end of the shorter string
                    for x in range(max(name_length, class_name_length)):
                        if x < name_length:
                            reservation_code_list.append(first_name[x])
                        if x < class_name_length:
                            reservation_code_list.append(class_name[x])

                    # convert the list into a string to get the reservation code
                    reservation_code = ''.join(reservation_code_list)

                    conn.execute(
                        "INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)",
                        (f"{first_name} {last_name}", seat_row, seat_column, reservation_code)
                    )
                    conn.commit()

                    success_message = f"Congratulations {first_name}! Row: {seat_row + 1}, Seat: {seat_column + 1} is now reserved for you. Enjoy your trip! Your eTicket number is: {reservation_code}"

                    # fetch updated seating chart
                    seating_chart = get_seating_chart_for_reservations()

                conn.close()

    return render_template(
        'reserve.html',
        seating_chart=seating_chart,
        error=error,
        success_message=success_message
    )

#helper function to retrieve the basic seating chart with 'X' for taken and 'O' for open
def get_seating_chart():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT seatRow, seatColumn FROM reservations")
    reservations = cursor.fetchall()
    conn.close()

    #initializes seating chart matrix with all seats open
    seating_chart = [['O' for _ in range(4)] for _ in range(12)]

    for reservation in reservations:
        row_index = reservation['seatRow']
        col_index = reservation['seatColumn']
        
        if 0 <= row_index < 12 and 0 <= col_index < 4:
            seating_chart[row_index][col_index] = 'X'
        else:
            print(f"Index out of range: Row {row_index} Column {col_index}")

    return seating_chart

#helper function to calculate the total sales from reservations
def calculate_total_sales():
    conn = get_db_connection()
    reservations = conn.execute("SELECT * FROM reservations").fetchall()
    conn.close()

    total_sales = 0
    cost_matrix = get_cost_matrix()
    for reservation in reservations:
        total_sales += cost_matrix[reservation['seatRow'] - 1][reservation['seatColumn'] - 1]
    return total_sales

#route to handle admin logout
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)  #clears the session
    return redirect(url_for('home'))

#helper function to create the database tables if they don't exist
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    #check if the 'seats' table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seats'")
    table_exists = cursor.fetchone()
    
    #if the table doesn't exist, create it
    if not table_exists:
        cursor.execute("""
            CREATE TABLE seats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seat_row INTEGER NOT NULL,
                seat_column INTEGER NOT NULL,
                status TEXT DEFAULT 'O'
            )
        """)
        conn.commit()
    
    conn.close()

#call create_tables at the beginning of your app to ensure tables are created
create_tables()

if __name__ == '__main__':
    app.run(debug=True)
