# backend/app.py
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

from backend.scrapers import get_scraper
from urllib.parse import urlparse
import json
import datetime as dt
from backend.models import UserListing
import backend.scrapers.dummy
import backend.scrapers.autotrader
import backend.scrapers.kijiji

# 1. import the extension objects from backend.extensions
from backend.extensions import db, migrate

# 2. import your helper functions AFTER extensions
from backend.queries import (
    get_average_price,
    get_reference_listings,
    get_user_listings,
    get_average_price_cents,
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

    @app.route("/api/submit-url", methods=["POST"])
    def submit_url():
        data = request.get_json(force=True)
        url  = data.get("url")
        if not url:
            return jsonify({"error": "url is required"}), 400

        scraper = get_scraper(url)
        if scraper is None:
            return jsonify({"error": "Unsupported domain"}), 400

        try:
            scraped = scraper.scrape(url)
        except Exception as e:
            return jsonify({"error": f"scrape failed: {e}"}), 502

        universal = [
            "make", "model", "year",
            "price", "mileage_km",
            "city", "province", "listing_date",
        ]
        missing = [f for f in universal if not scraped.get(f)]

        listing = UserListing(
            source_url    = url,
            source_site   = urlparse(url).netloc,
            scraped_at    = dt.datetime.now(dt.timezone.utc),
            missing_fields = json.dumps(missing),
            raw_data       = json.dumps(scraped),
            status         = "pending",
            **{k: scraped.get(k) for k in universal + ["trim"]}
        )

        # upsert
        existing = UserListing.query.filter_by(source_url=url).first()
        if existing:
            for k, v in listing.__dict__.items():
                if k not in ("_sa_instance_state", "id") and v is not None:
                    setattr(existing, k, v)
            listing = existing
        else:
            db.session.add(listing)

        db.session.commit()

        return jsonify({
            "listing": listing.to_dict(),
            "next_step": "manual" if missing else "scoring",
        }), 201

    @app.route("/api/complete-listing", methods=["POST"])
    def complete_listing():
        data = request.get_json(force=True)
        listing_id = data.get("id")
        if not listing_id:
            return jsonify({"error": "id is required"}), 400

        listing: UserListing | None = UserListing.query.get(listing_id)
        if not listing:
            return jsonify({"error": "Listing not found"}), 404

        # --- patch supplied fields ---
        patchable = [
            "price", "mileage_km", "city", "province",
            "listing_date", "make", "model", "year", "trim"
        ]
        for field in patchable:
            if field in data and data[field] is not None:
                value = data[field]

                # Convert ISO string → date object
                if field == "listing_date" and isinstance(value, str):
                    try:
                        value = dt.date.fromisoformat(value)   # expects "YYYY-MM-DD"
                    except ValueError:
                        return jsonify({"error": "listing_date must be YYYY-MM-DD"}), 400
                setattr(listing, field, value)

        # recompute missing list
        universal = ["make","model","year","price","mileage_km","city","province","listing_date"]
        missing   = [f for f in universal if not getattr(listing, f)]
        listing.missing_fields = json.dumps(missing)
        listing.status = "completed" if not missing else "pending"

        # --- deal score ---
        avg = get_average_price_cents(listing.make, listing.model, listing.year)
        score = None
        if avg and listing.price:
            ratio = listing.price / avg
            if   ratio <= 0.90: score = "Great"
            elif ratio <= 1.05: score = "Good"
            elif ratio <= 1.20: score = "Fair"
            else:               score = "Bad"
        listing.deal_score = score

        db.session.commit()

        return jsonify({
            "listing": listing.to_dict(),
            "deal_score": score,
            "next_step": "done" if not missing else "manual"
        }), 200
    # ---------------------------
    return app

# Dev entry-point
if __name__ == "__main__":
    create_app().run(debug=True)