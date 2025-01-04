from flask import Flask, request, url_for, render_template, redirect, session, flash, g
from pymongo import MongoClient 
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt
import gridfs
import os

# Flask app object 
app = Flask(__name__) 

app.secret_key = 'CSE470'  
bcrypt = Bcrypt(app)

# Set up MongoDB connection 
client = MongoClient('localhost', 27017) 
# This is a mongodb database and orders
db = client.flask_database['470'] 
print("Connected")
cart_collections = db.orders
product_collections = db.products
user_collections = db.users

@app.before_request
def before_request():
    g.user = session.get('username', None)
    g.user_type = session.get('user_type', None)

@app.route('/seed_products')   
def seed_products():
    users = [
        {"username": "meherubahasinalif", "password": "22341011", "type": "rescuer"},
        {"username": "admin", "password": "22341011", "type": "admin"}

    ]
    user_collections.insert_many(users)
    return "Seeded!"

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usertype = request.form['user-type']
        username = request.form['username']
        password = request.form['password']
        firstname = request.form['first-name']
        lastname = request.form['last-name']
        present = request.form['present-address']
        permanent = request.form['permanent-address']
        nid = request.form['nid-number']
        phone = request.form['phone-number']
        # hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Save the user in the database
        user_collections.insert_one({
            "username": username,
            "password": password,
            "type": usertype,
            "first": firstname,
            "last": lastname,
            "present": present,
            "permanent": permanent,
            "nid": nid,
            "phone": phone
        })
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = user_collections.find_one({"username": username})

        if user:
            print(user['_id'])
            session['user_id'] = str(user['_id'])
            session['user_type'] = user['type']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    products = list(product_collections.find())
    users = list(user_collections.find())

    if 'user_id' not in session:
        print('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    if g.user_type == 'admin':
        return render_template('admin_dashboard_shop.html', username=session['username'], products=products, users=users)
    else:
        return render_template('dashboard.html', username=session['username'], products=products)

@app.route('/display_products') 
def display_products():

    cart_items = list(cart_collections.find())
    products = list(product_collections.find())
    cart_details = []
    total = 0
    for item in cart_items:
        product = product_collections.find_one({"_id": ObjectId(item['product_id'])})
        if product:
            cart_details.append({
                "id":  ObjectId(item['_id']),
                "name": product["name"],
                "quantity": item["quantity"],
                "price": product["price"],
                "total": product["price"] * int(item["quantity"])
            })
        total += product["price"] * int(item["quantity"])
    
    return render_template('shop.html', products=products, cart_items=cart_details, total=total)

  
@app.route('/add_to_cart', methods = ['POST', 'GET'])
def add_to_cart():
        if request.method == 'POST':
            user_id = request.form.get('user_id')
            product_id = request.form.get('product_id')
            product_id = ObjectId(product_id)
            quantity = request.form.get('quantity')
        if product_id and quantity:
            # Insert the order into the cart collection
            cart_collections.insert_one({'product_id': product_id, 'quantity': int(quantity), 'bought_by': user_id})
            return redirect(url_for('display_products'))
        
        
@app.route('/update_cart', methods = ['POST', 'GET'])
def update_cart():
    if g.user_type == 'admin':
        product_id = request.form.get('update_id')
        product_id = ObjectId(product_id)
        product_collections.delete_one({'_id': product_id})
        return redirect(url_for('dashboard'))
    else:
        if request.method == 'POST':
            item_id = request.form.get('update_id')
            item_id = ObjectId(item_id)
        if item_id:
            cart_collections.delete_one({'_id': item_id})
            
        return redirect(url_for('display_products'))
        
        
@app.route('/checkout', methods=['POST', 'GET'])
def checkout():
    if request.method == 'POST':
        cart_items = list(cart_collections.find({'brought_by': session['username']}))
        total = 0
        for item in cart_items:
            product = product_collections.find_one({"_id": ObjectId(item['product_id'])})
            cart_collections.delete_one({'_id': ObjectId(item._id)})
            total += product["price"] * int(item["quantity"])
        return render_template('checkout.html', total=total)
    else:
        return redirect(url_for('display_products'))
    
@app.route('/thankyou', methods=['POST', 'GET'])
def thankyou():
    return render_template('thankyou.html')

@app.route('/upload_invetory', methods=['POST', 'GET'])
def upload_inventory():
    name = request.form.get('name')
    price = request.form.get('price')
    product_collections.insert_one({'name': name, 'price': price})
    return redirect(url_for('dashboard'))
    
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

if __name__ == '__main__': 
    app.run(debug=True) 
