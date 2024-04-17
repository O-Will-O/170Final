from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy import create_engine, text
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)
app.secret_key = 'secret_key'



# connection string is in the format mysql://user:password@server/database
conn_str = "mysql://root:Ilikegames05!@localhost/170final"
engine = create_engine(conn_str, echo=True)
conn = engine.connect()

def checkinput(phone, ssn):
    phone_pattern = r'^\d{10}$'
    ssn_pattern = r'^\d{9}$'
    yn = True
    errorIn = []

    if not re.match(phone_pattern, phone):
        yn = False
        errorIn.append("Phone")

    if not re.match(ssn_pattern, ssn):
        yn = False
        errorIn.append("SSN")

    return yn, errorIn
    
def CanAccess():
    username = session["Username"]
    if username == "Admin":
        return None
    if username != "Admin":
        return flash("Access Denied", "error"), redirect(url_for('index'))

def Checkexist(username):
     username = str(username)
     account = conn.execute(text("SELECT username FROM users WHERE username = :username"), {'username': username})
     result = account.fetchone()
     if result:
         return True
     else:
        return False

def CheckIfReviewed(username):
    account = conn.execute(text("Select username from to_be_reviewed where username = :username "), {'username': username})
    if not account:
        users = conn.execute(text("Select username from users where username = :username "), {'username': username})
        if users:
            return session.pop('WaitingForApproval', None), redirect(url_for('index'))
        else:
            return flash('Account review has been denied', 'error'), redirect(url_for('signup'))
    return redirect(url_for('wait'))

@app.route("/")
def index():
    if 'loggedin' in session and session['Username'] != "Admin":
        return render_template("index.html")
    elif 'loggedin' in session and session['Username'] == "Admin":
        return redirect(url_for('admin_home'))
    elif 'WaitingForApproval' in session:
        CheckIfReviewed(session["Username"])
    else:
        return redirect(url_for('login'))

@app.route("/waiting")
def wait():
    return render_template("waiting.html")


@app.route('/admin_home')
def admin_home():
    if 'loggedin' in session and session['Username'] == "Admin":
        return render_template('admin_home.html', msg=session.get('msg'))
    return redirect(url_for('index')), flash("Access Denied", "error") 

@app.route('/accountReview', methods=['GET', 'POST'])
def accountReview():
    if request.method == 'GET':
        CanAccess()
        accountNum = conn.execute(text('SELECT username, first_name, last_name, SSN, address, phone_num, email FROM to_be_reviewed;')).all()
        return render_template("accountReview.html", accounts=accountNum)
    
    elif request.method == 'POST':
        username = request.form['username']
        account = conn.execute(text('SELECT * FROM to_be_reviewed where username = :username;'), {"username": username}).fetchone()
        firstname = account[1] 
        lastname = account[2] 
        ssn = float(account[3])
        address = account[4]
        phone = float(account[5]) 
        email = account[7] 
        conn.execute(
            text('INSERT INTO users (username, first_name, last_name, SSN, address, phone_num, email) VALUES (:username, :first_name, :last_name, :SSN, :address, :phone, :email);'),
            {'username': username, 'first_name': firstname, 'last_name': lastname, 'SSN': ssn, 'address': address, 'phone': phone, 'email': email}
        )
        conn.commit()
        accountNum = conn.execute(text('SELECT bank_account_num FROM users where username = :username;'), {"username": username}).fetchone()
        conn.execute(text('Insert Into accounts () values (:accountNum, :amount)'), {"accountNum": accountNum}, {"amount": 0.00})
        conn.commit()
        conn.execute(text('Delete from to_be_reviewed where username = :username'), {'username' : username})
        conn.commit()
        return render_template('accountReview.html')

    


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        account = conn.execute(text("SELECT * FROM users WHERE username = :username AND password = :password"), request.form)
        user_data = account.fetchone()
        if not account:
            toBeR = conn.execute(text("Select username from to_be_reviewed where username = :username "), {'username': user_data[0]})
            toBeUse = toBeR.fetchone()
            if username == toBeUse[0] and password == toBeUse[6]:
                session['loggedin'] = True
                session['Username'] = toBeUse[0]
                session["Name"] = f"{toBeUse[1]} {toBeUse[2]}"
                session["WaitingForApproval"] = True
                return redirect(url_for('wait'))
        elif account:
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
    session.pop('WaitingForApproval', None)
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

        yn, errorIn = checkinput(phone, ssn)
        if not yn:
            for error in errorIn:
                flash(f'Invalid {error} format. Please check and try again.', 'error')
        elif Checkexist(username):
            flash('This Account Already Exists!', 'error')
        else:
            conn.execute(text(
            "INSERT INTO to_be_reviewed (username, password, email, first_name, last_name, SSN, phone_number, address) "
            "VALUES (:username, :password, :email, :firstname, :lastname, :ssn, :phone, :address)"),
            {
                'username': username,
                'password': password,
                'email': email,
                'firstname': firstname,
                'lastname': lastname,
                'ssn': ssn,
                'phone': phone,
                'address': address
            }) 

            conn.commit()
            session['loggedin'] = True
            session['Username'] = username
            session["Name"] = f"{firstname} {lastname}"
            session["WaitingForApproval"] = True
            return redirect(url_for('waiting'))
        return render_template('signup.html', msg=msg)

@app.route('/my_account', methods=['GET'])
def account_info():
    username = str(session['Username'])
    account = conn.execute(text("SELECT * FROM users natural join accounts WHERE username = :username"), {'username': username})
    user_data = account.fetchone()
    return render_template("my_account.html", user_data=user_data)


@app.route('/add_money', methods=['POST', 'GET'])
def add_money():
    if request.method == 'POST':
        account_number = request.form['account_number']
        card_number = request.form['card_number']
        expiry_date = request.form['expiry_date']
        ccv = request.form['ccv']
        amount = float(request.form['amount'])

        result = conn.execute(text("SELECT * FROM accounts WHERE bank_account_num = :account_number"), {'account_number': account_number})
        account = result.fetchone()

        if account:
            new_balance = float(account[1]) + amount
            conn.execute(text("UPDATE accounts SET amount = :new_balance WHERE bank_account_num = :account_number"), {'new_balance': new_balance, 'account_number': account_number})
            conn.commit()
            return redirect(url_for('account_info')), flash(f"Added {amount} to account {account_number}. New balance: {new_balance}", "info")
        else:
           return flash("Account not found.", 'error')

    return render_template("add_money.html")



@app.route('/send_money', methods=['POST', 'GET'])
def send_money():
    if request.method == 'POST':
        sender_account_number = request.form['sender_account_number']
        receiver_account_number = request.form['receiver_account_number']
        card_number = request.form['card_number']
        amount = float(request.form['amount'])

        sender_account = conn.execute(text("SELECT * FROM accounts WHERE bank_account_num = :account_number"), {'account_number': sender_account_number}).fetchone()
        
        receiver_account = conn.execute(text("SELECT * FROM accounts WHERE bank_account_num = :account_number"), {'account_number': receiver_account_number}).fetchone()
        
        if not sender_account:
            flash("Sender account not found.", 'error')
            return redirect(url_for('send_money'))
        if not receiver_account:
           flash("Receiver account not found.", 'error')
           return redirect(url_for('send_money'))
    
        if float(sender_account[1]) < amount:
           flash("Insufficient balance.", 'error')
           return redirect(url_for('send_money'))

        if sender_account_number == receiver_account_number:
           flash("Cannot send money to the same account!", 'error')
           return redirect(url_for('send_money'))

        new_sender_balance = float(sender_account[1]) - amount
        new_receiver_balance = float(receiver_account[1]) + amount

        conn.execute(text("UPDATE accounts SET amount = :new_sender_balance WHERE bank_account_num = :account_number"), {'new_sender_balance': new_sender_balance, 'account_number': sender_account_number})
        conn.execute(text("UPDATE accounts SET amount = :new_receiver_balance WHERE bank_account_num = :account_number"), {'new_receiver_balance': new_receiver_balance, 'account_number': receiver_account_number})
        
        return  redirect(url_for('account_info')), flash(f"Transferred {amount} from account {sender_account_number} to account {receiver_account_number}. Senders new balance: {new_sender_balance}. Receivers new balance: {new_receiver_balance}", "info")
    return render_template("send_money.html")

if __name__ == '__main__':
    app.run(debug=True)
