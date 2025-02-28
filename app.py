from flask import Flask, render_template, request, redirect, url_for, jsonify
import pickle
import numpy as np
import razorpay
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)

load_dotenv()
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load trained model
with open("bangalore_house_price_model.pkl", "rb") as f:
    model = pickle.load(f)

class Product(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    p_name = db.Column(db.String(20), nullable=False)
    p_price = db.Column(db.Integer, nullable=False)
    p_quantity = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/order")
def place_order():
    return render_template("checkout.html", key_id=RAZORPAY_KEY_ID)

@app.route("/order",  methods=['POST'])
def create_order():
    amount = 500
    currency = "INR"

    order_data = {
        "amount": amount,
        "currency" : currency
    }

    razorpay_order = razorpay_client.order.create(data=order_data)
    return {"order_id": razorpay_order["id"], "amount": amount}

@app.route("/product")
def purchase():
    return render_template("product.html")

@app.route("/contact")
def contactus():
    return render_template("contact.html")

@app.route("/verify", methods=['POST'])
def verify_signature():
    payment_id = request.form.get("razorpay_payment_id")
    order_id = request.form.get("razorpay_order_id")
    signature = request.form.get("razorpay_signature")

    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_payment_id":payment_id,
            "razorpay_order_id":order_id,
            "razorpay_signature":signature
        })
        return redirect("/success")
    except razorpay.errors.SignatureVerificationError:
        return "Signature verification failed", 400


@app.route("/success")
def payment_success():
    return render_template("success.html")


@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form["p_name"]
        price = request.form["p_price"]
        quantity = request.form["p_quantity"]
        
        new_product = Product(p_name=name, p_price=price, p_quantity=quantity)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for("view_products"))
    
    return render_template("add_product.html")

@app.route("/products")
def view_products():
    products = Product.query.all()
    return render_template("product.html", products=products)

# ✅ Update (Edit a Product)
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    product = Product.query.get(id)
    
    if request.method == "POST":
        product.p_name = request.form["p_name"]
        product.p_price = request.form["p_price"]
        product.p_quantity = request.form["p_quantity"]
        
        db.session.commit()
        return redirect(url_for("view_products"))

    return render_template("edit_product.html", product=product)

# ✅ Delete (Remove a Product)
@app.route("/delete/<int:id>")
def delete_product(id):
    product = Product.query.get(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("view_products"))



@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        total_sqft = float(data['total_sqft'])
        bhk = int(data['bhk'])
        bath = int(data['bath'])

        input_data = np.array([[total_sqft, bhk, bath]])
        predicted_price = model.predict(input_data)[0]

        return jsonify({'predicted_price': f"{predicted_price:.2f} Lakhs INR"})

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__=="__main__":
    app.run(debug=True)

