from flask import Flask, render_template, request, redirect
import razorpay
from dotenv import load_dotenv
import os

app=Flask(__name__)

load_dotenv()
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

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


if __name__=="__main__":
    app.run(debug=True)

