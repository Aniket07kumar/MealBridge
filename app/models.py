from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db, login_manager

# Status Constants
OPEN = "OPEN"
CLAIMED = "CLAIMED"
DISPATCHED = "DISPATCHED"
COLLECTED = "COLLECTED"
EXPIRED = "EXPIRED"

VALID_STATUSES = [OPEN, CLAIMED, DISPATCHED, COLLECTED, EXPIRED]
ROLE_DONOR = "donor"
ROLE_RECEIVER = "receiver"
ROLE_ADMIN = "admin"
ROLES = [ROLE_DONOR, ROLE_RECEIVER, ROLE_ADMIN]


def utc_now():
    """Return timezone-naive UTC datetime for consistent database storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(50), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default=ROLE_DONOR)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    # Hyperlocal Coordinates
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    locality = db.Column(db.String(100), nullable=True)

    # Relationships
    donated_listings = db.relationship(
        "Listing",
        back_populates="donor",
        foreign_keys="Listing.donor_id",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    claimed_listings = db.relationship(
        "Listing",
        back_populates="claimed_by",
        foreign_keys="Listing.claimed_by_id",
        lazy="dynamic",
    )
    claims_made = db.relationship(
        "ListingClaim",
        back_populates="receiver",
        foreign_keys="ListingClaim.receiver_id",
        lazy="dynamic",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Default is_approved: True for donors and admins, False for receivers
        if "is_approved" not in kwargs:
            if self.role in [ROLE_DONOR, ROLE_ADMIN]:
                self.is_approved = True
            else:
                self.is_approved = False

        # Auto-resolve default base coordinates from city if not provided
        if (self.latitude is None or self.longitude is None) and self.city:
            try:
                from app.catalog import geocode_address
                coords = geocode_address(self.city, self.locality)
                if coords:
                    self.latitude, self.longitude = coords
            except Exception:
                pass

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_donor(self):
        return self.role == ROLE_DONOR

    @property
    def is_receiver(self):
        return self.role == ROLE_RECEIVER

    @property
    def is_admin(self):
        return self.role == ROLE_ADMIN

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    food_key = db.Column(db.String(50), nullable=False)
    food_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # in plates (original posted)
    remaining_quantity = db.Column(db.Integer, nullable=False, default=0)  # available for pooled claim
    allow_partial_claim = db.Column(db.Boolean, nullable=False, default=True)
    is_veg = db.Column(db.Boolean, nullable=False, default=True)
    address = db.Column(db.String(255), nullable=False)
    locality = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=False, index=True)

    # Hyperlocal Geocoordinates
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    best_before = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default=OPEN, index=True)
    packaging_type = db.Column(db.String(50), nullable=False, default="packets")
    pickup_pin = db.Column(db.String(4), nullable=True)

    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    claimed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    claimed_at = db.Column(db.DateTime, nullable=True)
    dispatched_at = db.Column(db.DateTime, nullable=True)
    collected_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    donor = db.relationship("User", foreign_keys=[donor_id], back_populates="donated_listings")
    claimed_by = db.relationship("User", foreign_keys=[claimed_by_id], back_populates="claimed_listings")
    claims = db.relationship("ListingClaim", back_populates="listing", cascade="all, delete-orphan", lazy="select")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure remaining_quantity matches total quantity upon creation
        if self.remaining_quantity is None or ("remaining_quantity" not in kwargs and self.quantity is not None):
            self.remaining_quantity = self.quantity if self.quantity is not None else 0

        # Auto-resolve coordinates from address or city if not explicitly passed
        if (self.latitude is None or self.longitude is None) and self.city:
            try:
                from app.catalog import geocode_address
                coords = geocode_address(self.city, self.address or self.locality)
                if coords:
                    self.latitude, self.longitude = coords
            except Exception:
                pass

    @property
    def active_claims(self):
        """Return all non-cancelled claims on this listing."""
        return [c for c in self.claims if c.status != "CANCELLED"]

    @property
    def total_claimed_plates(self):
        """Sum of plates claimed across all active claims."""
        return sum(c.plates_claimed for c in self.active_claims)

    @property
    def is_partially_claimed(self):
        """True if some plates were claimed but more remain open."""
        return 0 < self.remaining_quantity < self.quantity

    @property
    def is_open(self):
        return self.status == OPEN

    @property
    def is_claimed(self):
        return self.status == CLAIMED

    @property
    def is_dispatched(self):
        return self.status == DISPATCHED

    @property
    def is_collected(self):
        return self.status == COLLECTED

    @property
    def has_expired(self):
        return utc_now() >= self.best_before

    def __repr__(self):
        return f"<Listing {self.id}: {self.food_name} ({self.remaining_quantity}/{self.quantity} plates) - {self.status}>"


class ListingClaim(db.Model):
    __tablename__ = "listing_claims"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plates_claimed = db.Column(db.Integer, nullable=False)
    pickup_pin = db.Column(db.String(4), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=CLAIMED, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    dispatched_at = db.Column(db.DateTime, nullable=True)
    collected_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    listing = db.relationship("Listing", back_populates="claims")
    receiver = db.relationship("User", foreign_keys=[receiver_id], back_populates="claims_made")

    @property
    def is_claimed(self):
        return self.status == CLAIMED

    @property
    def is_dispatched(self):
        return self.status == DISPATCHED

    @property
    def is_collected(self):
        return self.status == COLLECTED

    def __repr__(self):
        return f"<ListingClaim {self.id}: {self.plates_claimed} plates by User {self.receiver_id} - {self.status}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

