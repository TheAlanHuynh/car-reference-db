from flask import Flask, request, jsonify
from flask_cors import CORS
from db import get_average_price

app = Flask(__name__)
CORS(app)  # Allow requests from React frontend

@app.route("/")
def home():
    return "Car Reference API is running."

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

if __name__ == "__main__":
    app.run(debug=True)