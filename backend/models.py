from backend.extensions import db

# --- existing reference table ---------------------------------
class VehicleListing(db.Model):
    __tablename__ = "vehicle_listings"

    id           = db.Column(db.Integer, primary_key=True)
    make         = db.Column(db.Text,  nullable=False)
    model        = db.Column(db.Text,  nullable=False)
    year         = db.Column(db.Integer, nullable=False)
    price    = db.Column(db.Integer)   # stored in cents
    mileage_km   = db.Column(db.Integer)
    created_at   = db.Column(db.DateTime)
    
    condition     = db.Column(db.Text)
    cylinders     = db.Column(db.Text)
    fuel          = db.Column(db.Text)
    title_status  = db.Column(db.Text)
    transmission  = db.Column(db.Text)
    drive         = db.Column(db.Text)
    type          = db.Column(db.Text)
    paint_color   = db.Column(db.Text)
    state         = db.Column(db.String(2))

# --- NEW user-submitted listings ------------------------------
class UserListing(db.Model):
    __tablename__ = "user_listings"

    id           = db.Column(db.Integer, primary_key=True)
    source_url   = db.Column(db.Text, unique=True, nullable=False)
    source_site  = db.Column(db.Text)
    make         = db.Column(db.Text)
    model        = db.Column(db.Text)
    year         = db.Column(db.Integer)
    trim         = db.Column(db.Text)
    price    = db.Column(db.Integer)         # cents
    mileage_km   = db.Column(db.Integer)
    city         = db.Column(db.Text)
    province     = db.Column(db.String(2))
    listing_date = db.Column(db.Date)
    scraped_at   = db.Column(db.DateTime, server_default=db.func.now())
    missing_fields = db.Column(db.Text)          # JSON list
    raw_data     = db.Column(db.Text)            # JSON blob
    status       = db.Column(db.Text, default="pending")
    deal_score   = db.Column(db.Text)            # nullable

    # convenience for JSON responses
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}