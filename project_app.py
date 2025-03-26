from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'


def create_db():
    
    conn = sqlite3.connect('cars.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS car (
                    Car_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT,
                    description TEXT(30),
                    price_per_day REAL,
                    category TEXT,
                    contact_number INTEGER
                )''')
    conn.commit()
    conn.close()

    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT
                )''')
    conn.commit()
    conn.close()

create_db()


def get_db_connection():
    conn = sqlite3.connect('users.db')  
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            if action == 'login':
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()

                if user and user['password'] == password:
                    session['logged_in'] = True
                    session['username'] = username
                    conn.close()
                    return redirect(url_for('home'))
                else:
                    conn.close()
                    return render_template('login.html', message="User not found. Please sign up.")

            elif action == 'signup':
                try:
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                    conn.commit()
                    conn.close()
                    return redirect(url_for('login'))
                except sqlite3.IntegrityError:
                    conn.close()
                    return render_template('login.html', message="Username already exists. Please choose a different one.")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "There was an error connecting to the database. Please try again later."

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
def home():
    return "Hello, Render!"
    if 'logged_in' not in session:
        
        conn = sqlite3.connect('cars.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM car")
        cars = cursor.fetchall()
        conn.close()
        return render_template('index.html', cars=cars, is_logged_in=False)  

   
    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM car")
    cars = cursor.fetchall()
    conn.close()
    return render_template('index.html', cars=cars, is_logged_in=True) 


@app.route('/add_car', methods=['POST'])
def add_car():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    model = request.form['model']
    description = request.form['description']
    price_per_day = request.form['price']
    category = request.form['category']
    contact_number = request.form['contact']

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO car (model, description, price_per_day, category, contact_number) VALUES (?, ?, ?, ?, ?)", 
                   (model, description, price_per_day, category, contact_number))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

@app.route('/search', methods=['GET'])
def search():
    search_query = request.args.get('query', '')
    sort_order = request.args.get('sort', 'asc')  

    
    if sort_order == 'desc':
        order_by = 'price_per_day DESC'
    else:
        order_by = 'price_per_day ASC'
    
    
    with sqlite3.connect('cars.db') as conn:
        results = conn.execute(
            f'SELECT * FROM car WHERE model LIKE ? OR category LIKE ? ORDER BY {order_by}',
            (f'%{search_query}%', f'%{search_query}%')
        ).fetchall()
    
   
    return render_template('index.html', cars=results, is_logged_in=session.get('logged_in', False))


@app.route('/delete/<int:id>')
def delete_car(id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM car WHERE Car_ID=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/view_json/<int:id>')
def view_json(id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('cars.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM car WHERE Car_ID=?", (id,))
    car = cursor.fetchone()
    conn.close()

    if car:
        car_data = {
            "Car_ID": car[0],
            "Model": car[1],
            "Description": car[2],
            "Price_per_day": car[3],
            "Category": car[4],
            "Contact_number": car[5]
        }
        return jsonify(car_data)
    else:
        return "Car not found", 404

if __name__ == '__main__':
    app.run(port=6001, debug=True)
