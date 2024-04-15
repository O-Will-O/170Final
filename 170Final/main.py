from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import create_engine, text
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)
app.secret_key = 'secret_key'


def validate_email(email):
    # Regular expression for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email)


def validate_phone(phone):
    # Regular expression for phone number validation
    phone_pattern = r'^\d{10}$'
    return re.match(phone_pattern, phone)


# connection string is in the format mysql://user:password@server/database
conn_str = "mysql://root:Ilikegames05!@localhost/170final"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()


#           csasasdiha

@app.route("/")
def index():
    if 'loggedin' in session and session['Username'] != "Admin":
        return render_template('index.html', msg=session.get('msg'))
    return redirect(url_for('login'))


@app.route('/admin_home')
def admin_home():
    if 'loggedin' in session and session['Username'] == "Admin":
        return render_template('admin_home.html', msg=session.get('msg'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        account = conn.execute(text("SELECT * FROM users WHERE username = :username AND password = :password"),
                               request.form)
        user_data = account.fetchone()
        if username == user_data[0] == "Admin":
            session['loggedin'] = True
            session['Username'] = "Admin"
            return redirect(url_for('admin_home'))
        elif username == user_data[0] and password == user_data[6]:
            session['loggedin'] = True
            session['Username'] = user_data[0]
            session["Name"] = f"{user_data[1]} {user_data[2]}"
            msg = 'Login success!'
            return redirect(url_for('index'))
        else:
            msg = 'Wrong username or password'
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('Username', None)
    session.pop('Name', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        firstname = request.form['first_name']
        lastname = request.form['last_name']
        ssn = request.form['SSN']
        phone = request.form['phone_number']
        address = request.form['address']


        conn.execute(text(
            f"insert Into users () values ({username}, {password}, {email}, {firstname}, {lastname}, {ssn}, {phone}, {address});"),
                     request.form)
        conn.commit()
        return redirect(url_for('signup_success'))

    return render_template('signup.html')


if __name__ == '__main__':
    app.run(debug=True)
