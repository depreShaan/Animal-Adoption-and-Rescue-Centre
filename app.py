from flask import Flask, request, url_for, render_template, redirect, session
from pymongo import MongoClient 
from bson.objectid import ObjectId

# Flask app object 
app = Flask(__name__) 

# Set up MongoDB connection 
client = MongoClient('localhost', 27017) 
# This is a mongodb database and orders
db = client.flask_database['470'] 
print("Connected")
cart_collections = db.orders
product_collections = db.products


# Add data to MongoDB route 
@app.route('/') 
def display_products():
    products = product_collections.find()

    return render_template('shop.html', products=products)

  
@app.route('/add_to_cart', methods = ['POST', 'GET'])
def add_to_cart():
        if request.method == 'POST':
            product_id = request.form.get('product_id')
            product_id = ObjectId(product_id)
            quantity = request.form.get('quantity')
        if product_id and quantity:
            # Insert the order into the cart collection
            cart_collections.insert_one({'product_id': product_id, 'quantity': int(quantity)})
            return redirect(url_for('display_products'))
  
if __name__ == '__main__': 
    app.run(debug=True) 
