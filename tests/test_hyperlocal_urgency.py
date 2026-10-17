from datetime import datetime, timezone, timedelta
from app.models import Listing, User, OPEN, utc_now
from app.extensions import db
from app.utils import haversine_distance_km, estimate_travel_time_mins, calculate_urgency
from app.catalog import geocode_address


def test_haversine_distance_and_travel_time():
    """Verify Haversine formula and travel time estimations."""
    # Same point: zero distance
    assert haversine_distance_km(12.9716, 77.5946, 12.9716, 77.5946) == 0.0

    # Koramangala to Indiranagar (~5 km)
    dist = haversine_distance_km(12.9352, 77.6245, 12.9784, 77.6408)
    assert dist is not None
    assert 4.5 <= dist <= 5.8

    # Missing coordinates return None
    assert haversine_distance_km(None, 77.6245, 12.9784, 77.6408) is None
    assert haversine_distance_km(12.9352, None, 12.9784, 77.6408) is None

    # Travel time: formula is max(5, int(round(km * 3.0 + 4)))
    time_0km = estimate_travel_time_mins(0.0)
    assert time_0km == 5  # minimum handling buffer

    # 10km: round(10 * 3.0 + 4) = round(34) = 34
    time_10km = estimate_travel_time_mins(10.0)
    assert time_10km == 34

    # 2km: round(2 * 3.0 + 4) = round(10) = 10
    time_2km = estimate_travel_time_mins(2.0)
    assert time_2km == 10

    # None input returns None
    assert estimate_travel_time_mins(None) is None


def test_calculate_urgency_tiers():
    """Verify urgency level/score tiers using injected now_dt."""
    now = datetime(2026, 1, 1, 12, 0, 0)  # fixed naive UTC for determinism

    # 1. Fresh food (5 hours left, 2 km away) → FRESH or MODERATE level
    fresh_result = calculate_urgency(now + timedelta(hours=5), distance_km=2.0, now_dt=now)
    assert fresh_result["level"] in ("FRESH", "MODERATE")
    assert "score" in fresh_result
    assert fresh_result["score"] < 70

    # 2. Critical (45 minutes left) → CRITICAL
    crit_result = calculate_urgency(now + timedelta(minutes=45), distance_km=2.0, now_dt=now)
    assert crit_result["level"] == "CRITICAL"
    assert crit_result["score"] >= 80

    # 3. HIGH urgency (90 minutes left)
    high_result = calculate_urgency(now + timedelta(minutes=90), distance_km=2.0, now_dt=now)
    assert high_result["level"] == "HIGH"
    assert 70 <= high_result["score"] < 100

    # 4. Expired food (past best_before)
    expired_result = calculate_urgency(now - timedelta(minutes=10), distance_km=2.0, now_dt=now)
    assert expired_result["level"] == "EXPIRED"
    assert expired_result["score"] == 100

    # 5. Distance boost: same expiry, close listing gets higher score than distant one
    close_score = calculate_urgency(now + timedelta(hours=2), distance_km=1.0, now_dt=now)["score"]
    far_score = calculate_urgency(now + timedelta(hours=2), distance_km=25.0, now_dt=now)["score"]
    assert close_score > far_score


def test_geocode_locality_fallback():
    """Known localities resolve to approximate coordinates; unknowns fall back to city centroid."""
    # Known locality in Bengaluru
    lat, lng = geocode_address("Bengaluru", "Indiranagar 100ft road")
    assert lat is not None and lng is not None
    assert 12.95 <= lat <= 13.00

    # City centroid fallback for unknown street
    lat_city, lng_city = geocode_address("Bengaluru", "Nonexistent random street 999")
    assert lat_city == 12.9716 and lng_city == 77.5946


def test_feed_radius_filtering(client, auth, app):
    """Radius filter: 5 km sees only nearby listings, 25 km sees all in city."""
    with app.app_context():
        donor = User.query.filter_by(email="donor@test.com").first()
        donor_id = donor.id

        # Listing 1: Indiranagar (~0.1 km from test receiver GPS)
        l1 = Listing(
            food_key="biryani",
            food_name="Indiranagar Biryani",
            quantity=30,
            is_veg=False,
            address="Indiranagar 12th Main",
            locality="Indiranagar",
            city="Bengaluru",
            latitude=12.9784,
            longitude=77.6408,
            best_before=utc_now() + timedelta(hours=4),
            status=OPEN,
            donor_id=donor_id,
        )

        # Listing 2: Whitefield (~12 km away)
        l2 = Listing(
            food_key="dal_rice",
            food_name="Whitefield Dal Khichdi",
            quantity=50,
            is_veg=True,
            address="ITPL Main Road",
            locality="Whitefield",
            city="Bengaluru",
            latitude=12.9698,
            longitude=77.7500,
            best_before=utc_now() + timedelta(hours=4),
            status=OPEN,
            donor_id=donor_id,
        )

        db.session.add_all([l1, l2])
        db.session.commit()

    auth.login("receiver1@test.com", "test1234")

    # 5 km: only nearby listing visible
    res_5km = client.get("/receiver/feed?lat=12.9780&lng=77.6400&radius=5")
    assert res_5km.status_code == 200
    assert b"Indiranagar Biryani" in res_5km.data
    assert b"Whitefield Dal Khichdi" not in res_5km.data

    # 25 km: both visible
    res_25km = client.get("/receiver/feed?lat=12.9780&lng=77.6400&radius=25")
    assert res_25km.status_code == 200
    assert b"Indiranagar Biryani" in res_25km.data
    assert b"Whitefield Dal Khichdi" in res_25km.data


def test_feed_sorting_urgency_vs_distance(client, auth, app):
    """Urgency sort puts expiring-soon first; distance sort puts nearest first."""
    with app.app_context():
        donor = User.query.filter_by(email="donor@test.com").first()
        donor_id = donor.id

        # Listing A: nearby (1 km), fresh (5 hours)
        l_near = Listing(
            food_key="rice_sambar",
            food_name="Near Fresh Meals",
            quantity=20,
            is_veg=True,
            address="Near Location",
            city="Bengaluru",
            latitude=12.9750,
            longitude=77.6410,
            best_before=utc_now() + timedelta(hours=5),
            status=OPEN,
            donor_id=donor_id,
        )

        # Listing B: far (8 km), critical (40 mins)
        l_far_urgent = Listing(
            food_key="biryani",
            food_name="Far Urgent Meals",
            quantity=20,
            is_veg=False,
            address="Far Location",
            city="Bengaluru",
            latitude=12.9200,
            longitude=77.6100,
            best_before=utc_now() + timedelta(minutes=40),
            status=OPEN,
            donor_id=donor_id,
        )

        db.session.add_all([l_near, l_far_urgent])
        db.session.commit()

    auth.login("receiver1@test.com", "test1234")

    # Urgency sort: critical (expiring) first
    res_urgency = client.get("/receiver/feed?lat=12.9780&lng=77.6400&sort_by=urgency")
    assert res_urgency.status_code == 200
    idx_urgent = res_urgency.data.find(b"Far Urgent Meals")
    idx_fresh = res_urgency.data.find(b"Near Fresh Meals")
    assert idx_urgent < idx_fresh, "Critical meal should appear before fresh meal in urgency sort"

    # Distance sort: nearest first
    res_dist = client.get("/receiver/feed?lat=12.9780&lng=77.6400&sort_by=distance")
    assert res_dist.status_code == 200
    idx_near = res_dist.data.find(b"Near Fresh Meals")
    idx_far = res_dist.data.find(b"Far Urgent Meals")
    assert idx_near < idx_far, "Near meal should appear before far meal in distance sort"


def test_feed_dietary_filtering(client, auth, app):
    """Diet filters: veg-only hides non-veg and vice versa."""
    with app.app_context():
        donor = User.query.filter_by(email="donor@test.com").first()
        donor_id = donor.id

        l_veg = Listing(
            food_key="paneer_curry",
            food_name="Paneer Butter Masala",
            quantity=25,
            is_veg=True,
            address="MG Road",
            city="Bengaluru",
            best_before=utc_now() + timedelta(hours=3),
            status=OPEN,
            donor_id=donor_id,
        )
        l_nonveg = Listing(
            food_key="biryani",
            food_name="Chicken Dum Biryani",
            quantity=25,
            is_veg=False,
            address="Brigade Road",
            city="Bengaluru",
            best_before=utc_now() + timedelta(hours=3),
            status=OPEN,
            donor_id=donor_id,
        )
        db.session.add_all([l_veg, l_nonveg])
        db.session.commit()

    auth.login("receiver1@test.com", "test1234")

    res_veg = client.get("/receiver/feed?diet=veg")
    assert res_veg.status_code == 200
    assert b"Paneer Butter Masala" in res_veg.data
    assert b"Chicken Dum Biryani" not in res_veg.data

    res_nonveg = client.get("/receiver/feed?diet=nonveg")
    assert res_nonveg.status_code == 200
    assert b"Chicken Dum Biryani" in res_nonveg.data
    assert b"Paneer Butter Masala" not in res_nonveg.data
