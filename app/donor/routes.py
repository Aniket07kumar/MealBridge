from datetime import timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import current_user
from app.extensions import db
from app.models import (
    Listing,
    User,
    OPEN,
    CLAIMED,
    DISPATCHED,
    COLLECTED,
    EXPIRED,
    ROLE_DONOR,
    ROLE_ADMIN,
    utc_now,
)
from app.catalog import FOODS, get_food
from app.donor.forms import ListingForm
from app.utils import role_required

donor_bp = Blueprint("donor", __name__)


@donor_bp.route("/dashboard")
@role_required(ROLE_DONOR)
def dashboard():
    now = utc_now()

    # Automatically transition any past unclaimed open listings to EXPIRED
    Listing.query.filter(
        Listing.donor_id == current_user.id,
        Listing.status == OPEN,
        Listing.best_before <= now,
    ).update({Listing.status: EXPIRED}, synchronize_session=False)
    db.session.commit()

    # Retrieve listings created by current donor, newest first
    listings = (
        Listing.query.filter_by(donor_id=current_user.id)
        .order_by(Listing.created_at.desc())
        .all()
    )

    # Calculate quick donor stats accurately supporting partial/pooled claims
    active_count = sum(1 for l in listings if l.status in (OPEN, CLAIMED, DISPATCHED))
    collected_count = sum(
        1 for l in listings
        if l.status == COLLECTED or (l.claims and any(c.status == COLLECTED for c in l.claims))
    )
    plates_rescued = 0
    for l in listings:
        if l.claims:
            plates_rescued += sum(c.plates_claimed for c in l.claims if c.status == COLLECTED)
        elif l.status == COLLECTED:
            plates_rescued += l.quantity

    # Support HTMX polling/partial update
    if request.headers.get("HX-Request"):
        return render_template(
            "donor/_dashboard_listings.html",
            listings=listings,
            viewer_role=ROLE_DONOR,
            active_count=active_count,
            collected_count=collected_count,
            plates_rescued=plates_rescued,
        )

    return render_template(
        "donor/dashboard.html",
        listings=listings,
        viewer_role=ROLE_DONOR,
        active_count=active_count,
        collected_count=collected_count,
        plates_rescued=plates_rescued,
    )


@donor_bp.route("/new", methods=["GET", "POST"])
@role_required(ROLE_DONOR)
def new_listing():
    form = ListingForm()

    # Pre-fill form if re-posting an existing listing
    repost_id = request.args.get("repost_id", type=int)
    if request.method == "GET":
        if repost_id:
            original = db.session.get(Listing, repost_id)
            if original and original.donor_id == current_user.id:
                form.food_key.data = original.food_key
                form.quantity.data = original.quantity
                form.packaging_type.data = original.packaging_type
                form.is_veg.data = original.is_veg
                form.allow_partial_claim.data = original.allow_partial_claim
                form.city.data = original.city
                form.locality.data = original.locality
                form.address.data = original.address
                flash(
                    f"Details pre-filled from your previous donation of '{original.food_name}'! "
                    "Adjust quantity or best-before time if needed and post.",
                    "info",
                )
        elif current_user.city:
            form.city.data = current_user.city
            form.locality.data = current_user.locality

    if form.validate_on_submit():
        food_meta = get_food(form.food_key.data)
        hours = form.best_before_hours.data
        now = utc_now()
        best_before_dt = now + timedelta(hours=hours)

        # Geocode latitude and longitude from form inputs or address text
        lat_val = None
        lng_val = None
        if form.latitude.data and form.longitude.data:
            try:
                lat_val = float(form.latitude.data)
                lng_val = float(form.longitude.data)
            except (ValueError, TypeError):
                pass

        if lat_val is None or lng_val is None:
            from app.catalog import geocode_address
            lat_val, lng_val = geocode_address(form.city.data, form.locality.data or form.address.data)

        listing = Listing(
            food_key=form.food_key.data,
            food_name=food_meta["name"],
            quantity=form.quantity.data,
            remaining_quantity=form.quantity.data,
            allow_partial_claim=form.allow_partial_claim.data,
            packaging_type=form.packaging_type.data,
            is_veg=form.is_veg.data,
            address=form.address.data.strip(),
            locality=form.locality.data.strip() if form.locality.data else None,
            city=form.city.data,
            latitude=lat_val,
            longitude=lng_val,
            best_before=best_before_dt,
            status=OPEN,
            donor_id=current_user.id,
            created_at=now,
        )
        db.session.add(listing)
        db.session.commit()

        flash(
            f"Successfully posted {listing.quantity} plates of {listing.food_name}! "
            f"Nearby approved NGOs in {listing.city} can now claim it.",
            "success",
        )
        return redirect(url_for("donor.dashboard"))

    return render_template("donor/new_listing.html", form=form, catalog=FOODS)


@donor_bp.route("/dispatch/<int:id>", methods=["POST"])
@role_required(ROLE_DONOR)
def dispatch(id):
    listing = db.session.get(Listing, id)
    if not listing:
        abort(404)

    # Check ownership
    if listing.donor_id != current_user.id:
        abort(403)

    # Can dispatch if status is CLAIMED or if any active claims are CLAIMED
    has_claimed_claims = any(c.status == CLAIMED for c in listing.active_claims)
    if listing.status != CLAIMED and not has_claimed_claims:
        flash("Only claimed food listings can be marked as Dispatched.", "warning")
        return redirect(url_for("donor.dashboard"))

    entered_pin = request.form.get("pin", "").strip()

    # Check if entered PIN matches a specific claim
    for claim in listing.active_claims:
        if claim.status == CLAIMED and claim.pickup_pin == entered_pin:
            return dispatch_claim(claim.id)

    # Legacy PIN check on listing itself
    if listing.pickup_pin:
        if not entered_pin or entered_pin != listing.pickup_pin:
            flash(
                "Invalid Handover PIN! Please ask the collecting NGO team for their 4-digit PIN "
                "shown on their MealBridge Claims screen.",
                "danger",
            )
            return redirect(url_for("donor.dashboard"))

    listing.status = DISPATCHED
    listing.dispatched_at = utc_now()
    for claim in listing.active_claims:
        if claim.status == CLAIMED:
            claim.status = DISPATCHED
            claim.dispatched_at = utc_now()

    db.session.commit()

    from app.notifications import notify_receiver_food_dispatched
    notify_receiver_food_dispatched(listing)

    flash(
        f"PIN verified! Marked '{listing.food_name}' as Dispatched! The receiver can now confirm collection upon receipt.",
        "success",
    )
    return redirect(url_for("donor.dashboard"))


@donor_bp.route("/dispatch-claim/<int:claim_id>", methods=["POST"])
@role_required(ROLE_DONOR)
def dispatch_claim(claim_id):
    from app.models import ListingClaim
    claim = db.session.get(ListingClaim, claim_id)
    if not claim:
        abort(404)

    listing = claim.listing
    if listing.donor_id != current_user.id:
        abort(403)

    if claim.status != CLAIMED:
        flash("Only claimed food allocations can be marked as Dispatched.", "warning")
        return redirect(url_for("donor.dashboard"))

    entered_pin = request.form.get("pin", "").strip()
    if not entered_pin or entered_pin != claim.pickup_pin:
        flash(
            f"Invalid Handover PIN for {claim.receiver.name}! Please ask their collecting team for the 4-digit PIN.",
            "danger",
        )
        return redirect(url_for("donor.dashboard"))

    claim.status = DISPATCHED
    claim.dispatched_at = utc_now()

    # If all claims for this listing are now dispatched/collected and remaining is 0:
    if all(c.status in (DISPATCHED, COLLECTED) for c in listing.active_claims) and listing.remaining_quantity == 0:
        listing.status = DISPATCHED
        listing.dispatched_at = utc_now()

    db.session.commit()

    from app.notifications import notify_receiver_food_dispatched
    notify_receiver_food_dispatched(listing)

    flash(
        f"PIN verified! Marked {claim.plates_claimed} plates for '{claim.receiver.name}' as Dispatched!",
        "success",
    )
    return redirect(url_for("donor.dashboard"))



@donor_bp.route("/receipt/<int:id>")
@role_required(ROLE_DONOR, ROLE_ADMIN)
def receipt(id):
    listing = db.session.get(Listing, id)
    if not listing:
        abort(404)

    # Only donor owner or admin can view receipt
    if current_user.role == ROLE_DONOR and listing.donor_id != current_user.id:
        abort(403)

    if listing.status != COLLECTED:
        flash(
            "An official donation receipt is generated once the meal is successfully marked Collected.",
            "warning",
        )
        return redirect(url_for("donor.dashboard"))

    return render_template("donor/receipt.html", listing=listing)
