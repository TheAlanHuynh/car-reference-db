# backend/app.py
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# 1. import the extension objects from backend.extensions
from backend.extensions import db, migrate

# 2. import your helper functions AFTER extensions
from backend.queries import (
    get_average_price,
    get_reference_listings,
    get_user_listings,
)

def create_app():
    app = Flask(__name__)
    CORS(app)

    # ---- database config ----
    BASE_DIR = Path(__file__).resolve().parent.parent        # project root
    DB_PATH  = BASE_DIR / "db" / "car_reference.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # -------------------------

    # 3. initialise extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # 4. import models so SQLAlchemy “sees” them
    from backend import models   # noqa: F401

    # ---------- routes ----------
    @app.route("/")
    def home():
        return "Car Reference API is running."

    @app.route("/api/avg-price", methods=["GET"])
    def avg_price():
        make  = request.args.get("make")
        model = request.args.get("model")
        year  = request.args.get("year")
        if not all([make, model, year]):
            return jsonify({"error": "Missing make, model or year"}), 400
        try:
            year = int(year)
        except ValueError:
            return jsonify({"error": "Year must be a number"}), 400
        return jsonify(get_average_price(make, model, year))

    @app.route("/api/reference-listings", methods=["GET"])
    def reference_listings():
        limit = request.args.get("limit", default=100, type=int)
        make  = request.args.get("make")
        model = request.args.get("model")
        year  = request.args.get("year", type=int)
        return jsonify(get_reference_listings(limit, make, model, year))

    @app.route("/api/user-listings", methods=["GET"])
    def user_listings():
        limit = request.args.get("limit", default=100, type=int)
        return jsonify(get_user_listings(limit))

    # ---------------------------
    return app


# Dev entry-point
if __name__ == "__main__":
    create_app().run(debug=True)