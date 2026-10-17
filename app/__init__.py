import os
from flask import Flask, render_template
from config import config_by_name
from app.extensions import db, login_manager, migrate, csrf, mail
from app.catalog import food_image
from app.utils import time_left


def create_app(config_name="default"):
    app = Flask(__name__, instance_relative_config=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Load configuration
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)

    # Register Jinja globals and filters
    from app.utils import (
        time_left,
        clean_phone,
        haversine_distance_km,
        estimate_travel_time_mins,
        calculate_urgency,
    )
    from app.catalog import food_image, get_packaging_label

    app.jinja_env.globals.update(
        food_image=food_image,
        get_packaging_label=get_packaging_label,
        haversine_distance_km=haversine_distance_km,
        estimate_travel_time_mins=estimate_travel_time_mins,
        calculate_urgency=calculate_urgency,
    )
    app.jinja_env.filters["time_left"] = time_left
    app.jinja_env.filters["clean_phone"] = clean_phone
    app.jinja_env.filters["packaging_label"] = get_packaging_label
    app.jinja_env.filters["urgency"] = calculate_urgency

    # Register blueprints
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.donor.routes import donor_bp
    from app.receiver.routes import receiver_bp
    from app.admin.routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(donor_bp, url_prefix="/donor")
    app.register_blueprint(receiver_bp, url_prefix="/receiver")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Error handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # Ensure SQLite tables and columns are up to date
    with app.app_context():
        try:
            db.create_all()
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            if "listings" in inspector.get_table_names():
                listing_cols = {col["name"] for col in inspector.get_columns("listings")}
                if "remaining_quantity" not in listing_cols:
                    db.session.execute(text("ALTER TABLE listings ADD COLUMN remaining_quantity INTEGER DEFAULT 0"))
                    db.session.execute(text("UPDATE listings SET remaining_quantity = quantity WHERE remaining_quantity = 0 OR remaining_quantity IS NULL"))
                if "allow_partial_claim" not in listing_cols:
                    db.session.execute(text("ALTER TABLE listings ADD COLUMN allow_partial_claim BOOLEAN DEFAULT 1"))
                if "latitude" not in listing_cols:
                    db.session.execute(text("ALTER TABLE listings ADD COLUMN latitude FLOAT"))
                if "longitude" not in listing_cols:
                    db.session.execute(text("ALTER TABLE listings ADD COLUMN longitude FLOAT"))
                if "locality" not in listing_cols:
                    db.session.execute(text("ALTER TABLE listings ADD COLUMN locality VARCHAR(100)"))

            if "users" in inspector.get_table_names():
                user_cols = {col["name"] for col in inspector.get_columns("users")}
                if "latitude" not in user_cols:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN latitude FLOAT"))
                if "longitude" not in user_cols:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN longitude FLOAT"))
                if "locality" not in user_cols:
                    db.session.execute(text("ALTER TABLE users ADD COLUMN locality VARCHAR(100)"))

            db.session.commit()
        except Exception:
            db.session.rollback()

    return app

