from datetime import timedelta
from app.models import Listing, User, ListingClaim, OPEN, CLAIMED, DISPATCHED, COLLECTED, utc_now
from app.extensions import db


def test_partial_split_flow(client, auth, app):
    """
    Full pooled-claiming flow:
    - Receiver 1 claims 40/100 plates → listing stays OPEN with 60 remaining
    - Receiver 2 claims remaining 60 → listing moves to CLAIMED
    - Feed no longer shows listing once remaining=0
    """
    with app.app_context():
        donor_id = User.query.filter_by(email="donor@test.com").first().id
        listing = Listing(
            food_key="biryani",
            food_name="Bulk Veg Biryani Pot",
            quantity=100,
            remaining_quantity=100,
            allow_partial_claim=True,
            is_veg=True,
            address="Koramangala 5th Block",
            city="Bengaluru",
            best_before=utc_now() + timedelta(hours=4),
            status=OPEN,
            donor_id=donor_id,
        )
        db.session.add(listing)
        db.session.commit()
        listing_id = listing.id

    # --- Step 1: Receiver 1 claims 40 plates ---
    auth.login("receiver1@test.com", "test1234")
    res1 = client.post(f"/receiver/claim/{listing_id}", data={"plates": 40}, follow_redirects=True)
    assert res1.status_code == 200
    # Flash contains "Successfully claimed 40 plates!"
    assert b"Successfully claimed 40 plates!" in res1.data

    with app.app_context():
        l = db.session.get(Listing, listing_id)
        assert l.status == OPEN           # Still OPEN for second NGO
        assert l.remaining_quantity == 60
        assert len(l.claims) == 1
        c1 = l.claims[0]
        assert c1.plates_claimed == 40
        assert c1.status == CLAIMED
        assert len(c1.pickup_pin) == 4
        pin1 = c1.pickup_pin
        claim1_id = c1.id

    # Receiver 1's my-claims page must show their claim details (40 plates + PIN)
    res_mc = client.get("/receiver/my-claims")
    assert res_mc.status_code == 200
    assert b"40 plates" in res_mc.data
    assert pin1.encode() in res_mc.data
    auth.logout()

    # --- Step 2: Receiver 2 claims remaining 60 plates ---
    auth.login("receiver2@test.com", "test1234")
    res2 = client.post(f"/receiver/claim/{listing_id}", data={"plates": 60}, follow_redirects=True)
    assert res2.status_code == 200
    # All 60 remaining plates claimed → listing is now CLAIMED
    assert b"claimed successfully" in res2.data

    with app.app_context():
        l = db.session.get(Listing, listing_id)
        assert l.status == CLAIMED
        assert l.remaining_quantity == 0
        assert len(l.claims) == 2
        c2_list = [c for c in l.claims if c.id != claim1_id]
        assert len(c2_list) == 1
        c2 = c2_list[0]
        assert c2.plates_claimed == 60
        assert c2.status == CLAIMED

    auth.logout()

    # --- Step 3: Feed must NOT show the listing (remaining=0) ---
    auth.login("receiver1@test.com", "test1234")
    feed_res = client.get("/receiver/feed")
    assert feed_res.status_code == 200
    assert b"Bulk Veg Biryani Pot" not in feed_res.data
    auth.logout()


def test_partial_claim_edge_cases(client, auth, app):
    """
    Edge-case validation in the claim route:
    - Negative plates → error
    - Zero plates → error
    - Invalid text → error
    - Exceeding available → error
    - allow_partial_claim=False rejects partial claims
    """
    with app.app_context():
        donor_id = User.query.filter_by(email="donor@test.com").first().id
        listing = Listing(
            food_key="chapati",
            food_name="Fresh Rotis",
            quantity=50,
            remaining_quantity=50,
            allow_partial_claim=True,
            is_veg=True,
            address="Indiranagar",
            city="Bengaluru",
            best_before=utc_now() + timedelta(hours=3),
            status=OPEN,
            donor_id=donor_id,
        )
        db.session.add(listing)
        db.session.commit()
        listing_id = listing.id

    auth.login("receiver1@test.com", "test1234")

    # Negative plates
    res_neg = client.post(f"/receiver/claim/{listing_id}", data={"plates": -5}, follow_redirects=True)
    assert res_neg.status_code == 200
    assert b"Please request at least 1 plate." in res_neg.data

    # Zero plates
    res_zero = client.post(f"/receiver/claim/{listing_id}", data={"plates": 0}, follow_redirects=True)
    assert res_zero.status_code == 200
    assert b"Please request at least 1 plate." in res_zero.data

    # Invalid text
    res_invalid = client.post(f"/receiver/claim/{listing_id}", data={"plates": "abc"}, follow_redirects=True)
    assert res_invalid.status_code == 200
    assert b"Invalid number of plates requested." in res_invalid.data

    # Exceeds available (80 > 50)
    res_exceed = client.post(f"/receiver/claim/{listing_id}", data={"plates": 80}, follow_redirects=True)
    assert res_exceed.status_code == 200
    assert b"Only 50 plates are currently available" in res_exceed.data

    # Strict listing (allow_partial_claim=False) rejects partial
    with app.app_context():
        donor_id2 = User.query.filter_by(email="donor@test.com").first().id
        l_strict = Listing(
            food_key="curd_rice",
            food_name="Strict Full Batch",
            quantity=40,
            remaining_quantity=40,
            allow_partial_claim=False,
            is_veg=True,
            address="Indiranagar",
            city="Bengaluru",
            best_before=utc_now() + timedelta(hours=3),
            status=OPEN,
            donor_id=donor_id2,
        )
        db.session.add(l_strict)
        db.session.commit()
        strict_id = l_strict.id

    res_strict_partial = client.post(
        f"/receiver/claim/{strict_id}", data={"plates": 15}, follow_redirects=True
    )
    assert res_strict_partial.status_code == 200
    assert b"requires this meal to be collected in full" in res_strict_partial.data

    auth.logout()


def test_pooled_dispatch_and_collection_lifecycle(client, auth, app):
    """
    Full lifecycle for pooled claiming:
    - Donor dispatches each claim with individual PINs
    - Wrong PIN is rejected
    - Each receiver confirms collection
    - Listing becomes COLLECTED only when ALL claims are collected
    - Receipt shows both NGO beneficiaries
    """
    with app.app_context():
        donor_id = User.query.filter_by(email="donor@test.com").first().id
        r1_id = User.query.filter_by(email="receiver1@test.com").first().id
        r2_id = User.query.filter_by(email="receiver2@test.com").first().id

        listing = Listing(
            food_key="pulao",
            food_name="Paneer Pulao Grand Feast",
            quantity=80,
            remaining_quantity=0,
            allow_partial_claim=True,
            is_veg=True,
            address="HSR Layout Sector 1",
            city="Bengaluru",
            best_before=utc_now() + timedelta(hours=3),
            status=CLAIMED,
            donor_id=donor_id,
        )
        db.session.add(listing)
        db.session.flush()

        claim1 = ListingClaim(
            listing_id=listing.id,
            receiver_id=r1_id,
            plates_claimed=30,
            pickup_pin="4321",
            status=CLAIMED,
            created_at=utc_now(),
        )
        claim2 = ListingClaim(
            listing_id=listing.id,
            receiver_id=r2_id,
            plates_claimed=50,
            pickup_pin="8765",
            status=CLAIMED,
            created_at=utc_now(),
        )
        db.session.add_all([claim1, claim2])
        db.session.commit()
        listing_id = listing.id
        c1_id = claim1.id
        c2_id = claim2.id

    # --- Step 1: Donor dispatches Claim 1 ---
    auth.login("donor@test.com", "test1234")

    # Wrong PIN first
    res_wrong = client.post(f"/donor/dispatch-claim/{c1_id}", data={"pin": "0000"}, follow_redirects=True)
    assert b"Invalid Handover PIN" in res_wrong.data

    # Correct PIN for claim 1
    res_disp1 = client.post(f"/donor/dispatch-claim/{c1_id}", data={"pin": "4321"}, follow_redirects=True)
    assert b"30 plates" in res_disp1.data
    assert b"Dispatched" in res_disp1.data

    with app.app_context():
        assert db.session.get(ListingClaim, c1_id).status == DISPATCHED
        assert db.session.get(ListingClaim, c2_id).status == CLAIMED  # not yet

    # Correct PIN for claim 2
    res_disp2 = client.post(f"/donor/dispatch-claim/{c2_id}", data={"pin": "8765"}, follow_redirects=True)
    assert b"50 plates" in res_disp2.data

    with app.app_context():
        assert db.session.get(ListingClaim, c2_id).status == DISPATCHED
        assert db.session.get(Listing, listing_id).status == DISPATCHED

    auth.logout()

    # --- Step 2: Receiver 1 collects their portion ---
    auth.login("receiver1@test.com", "test1234")
    res_col1 = client.post(f"/receiver/collect-claim/{c1_id}", follow_redirects=True)
    assert res_col1.status_code == 200
    assert b"Collected" in res_col1.data

    with app.app_context():
        assert db.session.get(ListingClaim, c1_id).status == COLLECTED
        # Listing still DISPATCHED (claim2 not yet collected)
        assert db.session.get(Listing, listing_id).status == DISPATCHED
    auth.logout()

    # --- Step 3: Receiver 2 collects their portion ---
    auth.login("receiver2@test.com", "test1234")
    res_col2 = client.post(f"/receiver/collect-claim/{c2_id}", follow_redirects=True)
    assert res_col2.status_code == 200
    assert b"Collected" in res_col2.data

    with app.app_context():
        assert db.session.get(ListingClaim, c2_id).status == COLLECTED
        l = db.session.get(Listing, listing_id)
        # All claims collected + remaining=0 → listing is COLLECTED
        assert l.status == COLLECTED
        assert l.collected_at is not None
    auth.logout()

    # --- Step 4: Donor receipt shows both NGO beneficiaries ---
    auth.login("donor@test.com", "test1234")
    res_receipt = client.get(f"/donor/receipt/{listing_id}")
    assert res_receipt.status_code == 200
    # Both NGO names must appear in the receipt
    assert b"Approved NGO 1" in res_receipt.data
    assert b"30 plates" in res_receipt.data
    assert b"Approved NGO 2" in res_receipt.data
    assert b"50 plates" in res_receipt.data
    assert b"2 Verified NGO Partners" in res_receipt.data
    auth.logout()
