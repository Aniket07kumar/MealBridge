from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Listing, User, OPEN, CLAIMED, DISPATCHED, COLLECTED, ROLE_RECEIVER, utc_now
from app.utils import role_required

receiver_bp = Blueprint("receiver", __name__)


@receiver_bp.route("/pending")
@login_required
def pending():
    if current_user.role != ROLE_RECEIVER:
        return redirect(url_for("main.dashboard"))
    if current_user.is_approved:
        return redirect(url_for("receiver.feed"))
    return render_template("receiver/pending.html")


@receiver_bp.route("/feed")
@role_required(ROLE_RECEIVER)
def feed():
    now = utc_now()

    # Geolocation / Proximity query params
    receiver_lat = request.args.get("lat", type=float)
    receiver_lng = request.args.get("lng", type=float)
    radius_filter = request.args.get("radius", "all")
    sort_by = request.args.get("sort_by", "urgency")
    diet_filter = request.args.get("diet", "all")

    # If receiver coords not passed, fallback to user profile coords or city centroid
    if receiver_lat is None or receiver_lng is None:
        if current_user.latitude and current_user.longitude:
            receiver_lat = current_user.latitude
            receiver_lng = current_user.longitude
        else:
            from app.catalog import CITY_CENTROIDS
            centroid = CITY_CENTROIDS.get(current_user.city, (12.9716, 77.5946))
            receiver_lat, receiver_lng = centroid

    # Query active listings in current receiver's city with unexpired time and remaining plates
    query = Listing.query.filter(
        Listing.city == current_user.city,
        Listing.status == OPEN,
        Listing.best_before > now,
    )

    if diet_filter == "veg":
        query = query.filter(Listing.is_veg == True)
    elif diet_filter == "nonveg":
        query = query.filter(Listing.is_veg == False)

    raw_listings = query.all()

    # Filter out listings with no remaining plates and compute distance & urgency
    from app.utils import haversine_distance_km, estimate_travel_time_mins, calculate_urgency
    decorated_listings = []
    for l in raw_listings:
        # If remaining_quantity is 0 or less, skip from open feed
        if l.remaining_quantity is not None and l.remaining_quantity <= 0:
            continue

        dist = haversine_distance_km(receiver_lat, receiver_lng, l.latitude, l.longitude)
        travel_time = estimate_travel_time_mins(dist)
        urgency = calculate_urgency(l.best_before, dist)

        l.distance_km = dist
        l.travel_time_mins = travel_time
        l.urgency = urgency

        # Apply radius filter
        if radius_filter in ("5", "10", "25"):
            max_r = float(radius_filter)
            if dist is not None and dist > max_r:
                continue

        decorated_listings.append(l)

    # Sort listings
    if sort_by == "distance":
        decorated_listings.sort(
            key=lambda x: (x.distance_km if x.distance_km is not None else 9999, -x.urgency["score"])
        )
    elif sort_by == "newest":
        decorated_listings.sort(key=lambda x: x.created_at, reverse=True)
    elif sort_by == "time_left":
        decorated_listings.sort(key=lambda x: x.best_before)
    else:  # default 'urgency'
        decorated_listings.sort(key=lambda x: x.urgency["score"], reverse=True)

    context = {
        "listings": decorated_listings,
        "viewer_role": ROLE_RECEIVER,
        "current_lat": receiver_lat,
        "current_lng": receiver_lng,
        "radius_filter": radius_filter,
        "sort_by": sort_by,
        "diet_filter": diet_filter,
    }

    # HTMX polling/partial request: return just the listings container
    if request.headers.get("HX-Request"):
        return render_template("receiver/_feed_listings.html", **context)

    return render_template("receiver/feed.html", **context)


@receiver_bp.route("/claim/<int:id>", methods=["POST"])
@role_required(ROLE_RECEIVER)
def claim(id):
    now = utc_now()
    listing = db.session.get(Listing, id)
    if not listing:
        abort(404)

    # Validate matching city and non-expired status
    if listing.city != current_user.city:
        flash("This food listing was already claimed by another NGO or has expired.", "warning")
        return redirect(url_for("receiver.feed"))

    if listing.best_before <= now:
        flash("This food listing was already claimed by another NGO or has expired.", "warning")
        return redirect(url_for("receiver.feed"))

    # Must be in OPEN state and have remaining plates
    if listing.status != OPEN or (listing.remaining_quantity is not None and listing.remaining_quantity <= 0):
        flash("This food listing was already claimed by another NGO or has expired.", "warning")
        return redirect(url_for("receiver.feed"))

    # Determine plates to claim with robust edge-case validation
    raw_plates = request.form.get("plates")
    avail = listing.remaining_quantity if listing.remaining_quantity is not None else listing.quantity

    if raw_plates is not None and str(raw_plates).strip() != "":
        try:
            requested_plates = int(raw_plates)
        except (ValueError, TypeError):
            flash("Invalid number of plates requested.", "warning")
            return redirect(url_for("receiver.feed"))

        if requested_plates <= 0:
            flash("Please request at least 1 plate.", "warning")
            return redirect(url_for("receiver.feed"))

        if not listing.allow_partial_claim and requested_plates < avail:
            flash(
                "This donor requires this meal to be collected in full as a single batch. Please claim all available plates.",
                "warning",
            )
            return redirect(url_for("receiver.feed"))

        if requested_plates > avail:
            flash(
                f"Only {avail} plates are currently available for this listing. Please adjust your request.",
                "warning",
            )
            return redirect(url_for("receiver.feed"))

        claim_plates = requested_plates
    else:
        # No specific portion requested (e.g. claim all button)
        claim_plates = avail

    if claim_plates <= 0:
        flash("This food listing was already claimed by another NGO or has expired.", "warning")
        return redirect(url_for("receiver.feed"))

    import random
    handover_pin = f"{random.randint(1000, 9999)}"

    # Record Claim
    from app.models import ListingClaim
    new_claim = ListingClaim(
        listing_id=listing.id,
        receiver_id=current_user.id,
        plates_claimed=claim_plates,
        pickup_pin=handover_pin,
        status=CLAIMED,
        created_at=now,
    )
    db.session.add(new_claim)

    listing.remaining_quantity = avail - claim_plates
    if listing.remaining_quantity <= 0:
        listing.remaining_quantity = 0
        listing.status = CLAIMED
    else:
        # Partial allocation: stays OPEN on feed for other NGOs to claim remaining plates!
        listing.status = OPEN

    # Backward compatibility fields for single claims or primary claim
    if not listing.claimed_by_id:
        listing.claimed_by_id = current_user.id
        listing.claimed_at = now
        listing.pickup_pin = handover_pin

    db.session.commit()

    # Send notification email to the donor
    from app.notifications import notify_donor_listing_claimed
    notify_donor_listing_claimed(listing)

    if listing.remaining_quantity > 0:
        flash(
            f"Successfully claimed {claim_plates} plates! ({listing.remaining_quantity} plates remain available for other NGOs). "
            f"Please check your Handover PIN on your Claims page.",
            "success",
        )
    else:
        flash(
            f"Food listing claimed successfully! Please contact the donor using their phone number to coordinate pickup.",
            "success",
        )
    return redirect(url_for("receiver.my_claims"))


@receiver_bp.route("/my-claims")
@role_required(ROLE_RECEIVER)
def my_claims():
    from app.models import ListingClaim

    # Retrieve all claims made by current receiver, newest first
    claims = (
        ListingClaim.query.filter_by(receiver_id=current_user.id)
        .order_by(ListingClaim.created_at.desc())
        .all()
    )

    # Attach claim context to listings for seamless card rendering
    claimed_listings = []
    seen_listing_ids = set()
    for c in claims:
        l = c.listing
        l.current_user_claim = c
        l.claimed_plates = c.plates_claimed
        l.user_pickup_pin = c.pickup_pin
        l.claim_status = c.status
        claimed_listings.append(l)
        seen_listing_ids.add(l.id)

    # Also support legacy listings claimed directly without a ListingClaim record
    legacy_listings = (
        Listing.query.filter_by(claimed_by_id=current_user.id)
        .order_by(Listing.claimed_at.desc())
        .all()
    )
    for l in legacy_listings:
        if l.id not in seen_listing_ids:
            l.current_user_claim = None
            l.claimed_plates = l.quantity
            l.user_pickup_pin = l.pickup_pin
            l.claim_status = l.status
            claimed_listings.append(l)

    return render_template(
        "receiver/my_claims.html",
        listings=claimed_listings,
        viewer_role=ROLE_RECEIVER,
    )


@receiver_bp.route("/collect/<int:id>", methods=["POST"])
@role_required(ROLE_RECEIVER)
def collect(id):
    from app.models import ListingClaim
    # Check if current user has an active claim on this listing
    user_claim = (
        ListingClaim.query.filter_by(listing_id=id, receiver_id=current_user.id)
        .order_by(ListingClaim.id.desc())
        .first()
    )
    if user_claim:
        return collect_claim(user_claim.id)

    listing = db.session.get(Listing, id)
    if not listing:
        abort(404)

    # Only the claimer can mark as collected
    if listing.claimed_by_id != current_user.id:
        abort(403)

    # Must be in DISPATCHED state
    if listing.status != DISPATCHED:
        flash(
            "Listing cannot be collected yet. The donor must mark it 'Dispatched' before you can confirm collection.",
            "warning",
        )
        return redirect(url_for("receiver.my_claims"))

    listing.status = COLLECTED
    listing.collected_at = utc_now()
    db.session.commit()

    from app.notifications import notify_donor_food_collected
    notify_donor_food_collected(listing)

    flash(
        f"Thank you! You marked '{listing.food_name}' as Collected. The donation loop is complete!",
        "success",
    )
    return redirect(url_for("receiver.my_claims"))


@receiver_bp.route("/collect-claim/<int:claim_id>", methods=["POST"])
@role_required(ROLE_RECEIVER)
def collect_claim(claim_id):
    from app.models import ListingClaim
    claim = db.session.get(ListingClaim, claim_id)
    if not claim:
        abort(404)

    if claim.receiver_id != current_user.id:
        abort(403)

    if claim.status != DISPATCHED:
        flash(
            "Listing cannot be collected yet. The donor must mark it 'Dispatched' before you can confirm collection.",
            "warning",
        )
        return redirect(url_for("receiver.my_claims"))

    claim.status = COLLECTED
    claim.collected_at = utc_now()

    # Check if all active claims on the listing are now collected and no plates remain open
    listing = claim.listing
    all_collected = all(c.status == COLLECTED for c in listing.active_claims)
    if all_collected and listing.remaining_quantity == 0:
        listing.status = COLLECTED
        listing.collected_at = utc_now()

    db.session.commit()

    from app.notifications import notify_donor_food_collected
    notify_donor_food_collected(listing)

    flash(
        f"Thank you! You marked your claim for {claim.plates_claimed} plates of '{listing.food_name}' as Collected. The donation loop is complete!",
        "success",
    )
    return redirect(url_for("receiver.my_claims"))

