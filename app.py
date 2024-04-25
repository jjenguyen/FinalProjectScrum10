from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# function to establish database connection
def get_db_connection():
    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('home.html')

# admin login page
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # error check empty user inputs
        if not username:
            return render_template('admin.html', error="You must enter a username.")
        elif not password:
            return render_template('admin.html', error="You must enter a password.")
        else:
            # fetch data from database for existing admin creds
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
            admin = cursor.fetchone()
            conn.close()
            
            if admin:
                return redirect(url_for('logged_in'))
            else:
                # error check invalid admin creds
                return render_template('admin.html', error="Invalid username/password combination. Please try again.")
    else:
        return render_template('admin.html')

# reserve a seat page
@app.route('/reserve')
def reserve():
    return render_template('reserve.html')

# admin page after successful log in (once admin logs in, they get directed to this page)
@app.route('/logged_in')
def logged_in():
    # need to add logic to fetch seating chart and total sales from the database
    return render_template('logged_in.html')

if __name__ == '__main__':
    app.run(debug=True)