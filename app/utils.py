from functools import wraps
from datetime import datetime, timezone
from flask import abort, redirect, url_for, flash
from flask_login import current_user
from app.models import utc_now, ROLE_RECEIVER


def role_required(*roles):
    """
    Decorator restricting route access to specific user roles.
    Redirects unapproved receivers to the pending page.
    """
    def decorator(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            if current_user.role not in roles:
                abort(403)

            # If user is a receiver and not approved yet, redirect to pending approval page
            # (unless they are already accessing the pending approval route or logging out)
            if current_user.role == ROLE_RECEIVER and not current_user.is_approved:
                # We let them access the pending page, but not protected receiver actions like feed/claim
                from flask import request
                if request.endpoint != "receiver.pending" and request.endpoint != "auth.logout":
                    flash("Your NGO account is currently awaiting administrative approval.", "info")
                    return redirect(url_for("receiver.pending"))

            return fn(*args, **kwargs)
        return decorated_view
    return decorator


def time_left(dt):
    """
    Calculate and format remaining time until best_before datetime.
    Returns strings like '2h 15m', '45m', '< 1m', or 'Expired'.
    """
    if not dt:
        return ""

    now = utc_now()
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

    diff = dt - now
    total_seconds = int(diff.total_seconds())

    if total_seconds <= 0:
        return "Expired"

    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours > 24:
        days = hours // 24
        return f"{days}d {hours % 24}h"
    elif hours > 0:
        return f"{hours}h {minutes:02d}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return "< 1m"


def clean_phone(phone_str):
    """
    Sanitize a phone string to raw digits for wa.me WhatsApp links.
    e.g. '+91 98888 11111' -> '919888811111'
    """
    if not phone_str:
        return ""
    import re
    return re.sub(r"[^\d]", "", str(phone_str))


def haversine_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two geographic points
    using the Haversine formula (returned in km, rounded to 1 decimal).
    """
    if None in (lat1, lon1, lat2, lon2):
        return None

    import math
    try:
        lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    except (ValueError, TypeError):
        return None

    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 1)


def estimate_travel_time_mins(distance_km):
    """
    Estimate urban transit time in minutes (~20 km/h average with pickup buffer).
    """
    if distance_km is None:
        return None
    return max(5, int(round(distance_km * 3.0 + 4)))


def calculate_urgency(best_before, distance_km=None, now_dt=None):
    """
    Compute real-time food urgency metrics:
      - score: 0 to 100 ranking score (higher = needs faster pickup)
      - level: 'CRITICAL', 'HIGH', 'MODERATE', 'FRESH', or 'EXPIRED'
      - label: human badge string
      - css_class: badge styling class
    """
    if not best_before:
        return {
            "score": 0,
            "level": "FRESH",
            "label": "🌿 Fresh",
            "css_class": "badge-urgency-fresh",
        }

    now = now_dt or utc_now()
    if best_before.tzinfo is not None:
        best_before = best_before.astimezone(timezone.utc).replace(tzinfo=None)
    if now.tzinfo is not None:
        now = now.astimezone(timezone.utc).replace(tzinfo=None)

    minutes_left = (best_before - now).total_seconds() / 60.0

    if minutes_left <= 0:
        return {
            "score": 100,
            "level": "EXPIRED",
            "label": "⚠️ Expired",
            "css_class": "badge-urgency-expired",
        }
    elif minutes_left <= 60:
        base_score = 90.0 + min(10.0, (60.0 - minutes_left) / 6.0)
        level = "CRITICAL"
        label = f"🚨 Critical (< 1h left: {int(minutes_left)}m)"
        css_class = "badge-urgency-critical"
    elif minutes_left <= 120:
        base_score = 70.0 + (120.0 - minutes_left) / 3.0
        level = "HIGH"
        hrs = int(minutes_left // 60)
        mins = int(minutes_left % 60)
        label = f"⚡ Urgent (< 2h left: {hrs}h {mins}m)"
        css_class = "badge-urgency-high"
    elif minutes_left <= 240:
        base_score = 40.0 + (240.0 - minutes_left) / 4.0
        level = "MODERATE"
        hrs = round(minutes_left / 60.0, 1)
        label = f"⏱️ Moderate (~{hrs}h left)"
        css_class = "badge-urgency-moderate"
    else:
        base_score = max(10.0, 40.0 - (minutes_left - 240.0) / 30.0)
        level = "FRESH"
        hrs = int(round(minutes_left / 60.0))
        label = f"🌿 Fresh (~{hrs}h left)"
        css_class = "badge-urgency-fresh"

    # Proximity boost: closer items get an urgency boost so nearby NGOs act quickly
    if distance_km is not None:
        if distance_km <= 3.0:
            base_score = min(100.0, base_score + 8.0)
        elif distance_km <= 7.0:
            base_score = min(100.0, base_score + 4.0)
        elif distance_km > 20.0:
            base_score = max(1.0, base_score - 10.0)

    return {
        "score": round(base_score, 1),
        "level": level,
        "label": label,
        "css_class": css_class,
    }


