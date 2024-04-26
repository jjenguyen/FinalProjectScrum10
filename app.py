from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_very_secret_key'  # Replace with a real secret key

#cost matrix for flights
def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

# Function to establish database connection
def get_db_connection():
    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        admin_user = conn.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        
        if admin_user:
            session['admin_logged_in'] = True  # Set the session flag
            return redirect(url_for('logged_in'))  # Redirect to the logged-in page
        else:
            error = "Invalid login credentials. Please try again."  # Set the error message

    return render_template('admin.html', error=error)

@app.route('/logged_in')
def logged_in():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin'))

    seating_chart = get_seating_chart_with_details()
    total_sales = calculate_total_sales()

    return render_template('logged_in.html', seating_chart=seating_chart, total_sales=total_sales)


def get_seating_chart_with_details():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Retrieve all reservations
    cursor.execute("""
        SELECT seatRow, seatColumn, passengerName, eTicketNumber
        FROM reservations
        ORDER BY seatRow, seatColumn
    """)
    
    reservations = cursor.fetchall()
    conn.close()
    
    # Initialize seating chart matrix with all seats open
    seating_chart = [[{'status': 'O', 'details': ''} for _ in range(4)] for _ in range(12)]
    
    # Iterate through all reservations and update the seating chart
    for reservation in reservations:
        # Adjust because your database stores rows and columns starting at index 0
        row_index = reservation['seatRow']
        col_index = reservation['seatColumn']
        details = f"{reservation['passengerName']} - {reservation['eTicketNumber']}"
        
        # Make sure the indexes are within the range before updating the seating_chart
        if 0 <= row_index < len(seating_chart) and 0 <= col_index < len(seating_chart[row_index]):
            seating_chart[row_index][col_index] = {'status': 'X', 'details': details}
        else:
            print(f"Index out of range: Row {row_index} Column {col_index}")
    
    return seating_chart





def get_seating_chart_for_reservations():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Retrieve all reservations
    cursor.execute("""
        SELECT seatRow, seatColumn
        FROM reservations
    """)
    
    reserved_seats = {f"{row['seatRow']}-{row['seatColumn']}": True for row in cursor.fetchall()}
    conn.close()
    
    # Initialize seating chart matrix with all seats open
    seating_chart = [['O' for _ in range(4)] for _ in range(12)]
    
    # Iterate through all reservations and update the seating chart
    for row_index in range(12):
        for col_index in range(4):
            if f"{row_index}-{col_index}" in reserved_seats:
                seating_chart[row_index][col_index] = 'X'
    
    return seating_chart




@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    error = None
    success_message = None
    # Fetch the current seating chart details to display
    seating_chart = get_seating_chart()

    if request.method == 'POST':
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        seat_row = int(request.form['seatRow'])
        seat_column = int(request.form['seatColumn'])

        conn = get_db_connection()
        # Check if the seat is already reserved
        existing_reservation = conn.execute(
            "SELECT * FROM reservations WHERE seatRow = ? AND seatColumn = ?", 
            (seat_row, seat_column)
        ).fetchone()

        if existing_reservation:
            error = f"Seat {seat_row}-{seat_column} is already taken. Please select another seat."
        else:
            # Seat is available, add new reservation
            reservation_code = f"{first_name[0]}{last_name[0]}{seat_row}{seat_column}"
            conn.execute(
                "INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)",
                (f"{first_name} {last_name}", seat_row, seat_column, reservation_code)
            )
            conn.commit()
            success_message = f"Seat {seat_row}-{seat_column} successfully reserved."
            # Update the seating chart after the new reservation
            seating_chart = get_seating_chart()

        conn.close()

    return render_template(
        'reserve.html',
        seating_chart=seating_chart,
        error=error,
        success_message=success_message
    )

def get_seating_chart():
    conn = get_db_connection()
    reservations = conn.execute("SELECT seatRow, seatColumn FROM reservations").fetchall()
    conn.close()

    seating_chart = [['O' for _ in range(4)] for _ in range(12)]
    for reservation in reservations:
        # Adjust index for 0-based array access
        row_index = reservation['seatRow'] - 1
        col_index = reservation['seatColumn'] - 1
        seating_chart[row_index][col_index] = 'X'

    return seating_chart


# Ensure get_seating_chart_with_details() and any other required methods are defined appropriately



def calculate_total_sales():
    conn = get_db_connection()
    reservations = conn.execute("SELECT * FROM reservations").fetchall()
    conn.close()

    total_sales = 0
    cost_matrix = get_cost_matrix()
    for reservation in reservations:
        total_sales += cost_matrix[reservation['seatRow'] - 1][reservation['seatColumn'] - 1]
    return total_sales

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)  # Clear the session
    return redirect(url_for('home'))

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the 'seats' table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seats'")
    table_exists = cursor.fetchone()
    
    # If the table doesn't exist, create it
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

# Call create_tables at the beginning of your app to ensure tables are created
create_tables()



if __name__ == '__main__':
    app.run(debug=True)

