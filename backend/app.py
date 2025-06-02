from flask import Flask, request, jsonify
from flask_cors import CORS
from db import get_average_price, get_reference_listings, get_user_listings  # new functions you'll write

app = Flask(__name__)
CORS(app)  # Allow requests from React frontend

# --------------------------------------------------
# Reference Queries Category
# --------------------------------------------------
# Home Page - Route
@app.route("/")
def home():
    return "Car Reference API is running."

# Average Price - Route
@app.route("/api/avg-price", methods=["GET"])
def avg_price():
    # Get parameters from query string
    make = request.args.get("make")
    model = request.args.get("model")
    year = request.args.get("year")

    # Validate required fields
    if not all([make, model, year]):
        return jsonify({"error": "Missing required parameters: make, model, year"}), 400

    try:
        year = int(year)
    except ValueError:
        return jsonify({"error": "Year must be a number"}), 400

    # Call the database query
    result = get_average_price(make, model, year)
    return jsonify(result)

# Reference Listing Queries
@app.route("/api/reference-listings", methods=["GET"])
def reference_listings():
    limit = request.args.get("limit", default=100, type=int)
    listings = get_reference_listings(limit)
    return jsonify(listings)

# User Lisiting Queries
@ app.route("/api/user-listings", methods=["GET"])
def user_listings():
    limit = request.args.get("limit", default=100, type=int)
    listings = get_user_listings(limit)
    return jsonify(listings)

if __name__ == "__main__":
    app.run(debug=True)