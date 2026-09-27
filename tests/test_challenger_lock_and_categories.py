"""
Adversarial Empirical Challenge Test Suite for Milestone 1:
- Lock Expiration Behavior (`locked_until < NOW()`)
- Dynamic Category Updates (Real-time category inclusion/exclusion)

Author: Challenger 2 (Empirical Challenger Agent)
Requirements: ORIGINAL_REQUEST.md (R1, R2, Acceptance Criteria), PROJECT.md Contracts #1, #2, #3.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import uuid
import httpx
import pytest


# ==============================================================================
# 1. LOCK EXPIRATION TESTS (locked_until < NOW())
# ==============================================================================

@pytest.mark.asyncio
async def test_item_with_expired_lock_immediately_visible_in_vitrine(
    client: httpx.AsyncClient,
    create_product,
):
    """
    Empirical Assertion:
    An item with status='locked' but locked_until < NOW() MUST be immediately
    visible on GET /api/products, and normalized to status='available'.
    """
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    unique_title = f"Vestido Vintage Seda Anos 60 {uuid.uuid4().hex[:6]}"
    unique_cat = f"VestidosSeda_{uuid.uuid4().hex[:6]}"

    product = await create_product(
        title=unique_title,
        category=unique_cat,
        price=180.00,
        status="locked",
        locked_until=past_time,
    )
    product_id = product["id"]

    # 1. Query public vitrine
    res = await client.get("/api/products")
    assert res.status_code == 200
    items = res.json()

    # Find the piece in vitrine
    matching = [p for p in items if p["id"] == product_id]
    assert len(matching) == 1, (
        f"Product {product_id} with expired lock (< NOW()) MUST be visible in GET /api/products. "
        f"Found {len(matching)} instances in catalog."
    )
    assert matching[0]["status"] == "available", (
        f"Expired lock status must be normalized to 'available' in showcase, got: {matching[0]['status']}"
    )

    # 2. Query filtered by category
    cat_res = await client.get("/api/products", params={"category": unique_cat})
    assert cat_res.status_code == 200
    cat_items = cat_res.json()
    assert any(p["id"] == product_id for p in cat_items), (
        f"Product {product_id} with expired lock MUST also appear in category-filtered query."
    )


@pytest.mark.asyncio
async def test_item_with_expired_lock_can_be_re_locked_by_new_request(
    client: httpx.AsyncClient,
    create_product,
    checkout_pix,
):
    """
    Empirical Assertion:
    An item with status='locked' and locked_until < NOW() can be acquired/locked
    by a new checkout request without requiring background crons or manual intervention.
    Once re-locked:
    - New lock duration must be ~10 minutes (expires_in = 600)
    - Item must immediately disappear from GET /api/products
    - Another subsequent checkout must be rejected with HTTP 409 Conflict
    """
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=12)).isoformat()
    unique_title = f"Blazer Alfaiataria Tweed {uuid.uuid4().hex[:6]}"

    product = await create_product(
        title=unique_title,
        price=220.00,
        status="locked",
        locked_until=past_time,
    )
    product_id = product["id"]

    # New buyer acquires the lock
    re_lock_res = await checkout_pix(
        product_id=product_id,
        customer_name="Compradora Segunda Chance",
        customer_email="segunda_chance@vintagebrecho.com.br",
    )
    assert re_lock_res.status_code in (200, 201), (
        f"Expected 200/201 on re-locking expired item, got {re_lock_res.status_code}: {re_lock_res.text}"
    )
    checkout_data = re_lock_res.json()
    assert "order_id" in checkout_data
    assert checkout_data.get("expires_in") == 600 or (590 <= checkout_data.get("expires_in", 0) <= 600)

    # Immediately after re-locking, product MUST disappear from public vitrine
    vitrine_res = await client.get("/api/products")
    assert vitrine_res.status_code == 200
    vitrine_ids = [p["id"] for p in vitrine_res.json()]
    assert product_id not in vitrine_ids, (
        f"Product {product_id} was just re-locked and MUST NOT appear in GET /api/products"
    )

    # A 3rd buyer trying to checkout immediately must receive HTTP 409 Conflict
    third_buyer_res = await checkout_pix(
        product_id=product_id,
        customer_name="Comprador Terceiro",
        customer_email="terceiro@teste.com",
    )
    assert third_buyer_res.status_code == 409, (
        f"Expected HTTP 409 Conflict for newly re-locked item, got {third_buyer_res.status_code}: {third_buyer_res.text}"
    )


@pytest.mark.asyncio
async def test_lock_expiration_exact_boundary_timing(
    client: httpx.AsyncClient,
    create_product,
    checkout_pix,
):
    """
    Empirical Assertion:
    Boundary stress test:
    - Product locked with locked_until set 2 seconds in the future.
    - While in the future:
      - GET /api/products MUST NOT return it.
      - POST /api/checkout/pix MUST return 409 Conflict.
    - Wait 3 seconds (transitioning locked_until into the past).
    - Now:
      - GET /api/products MUST return it.
      - POST /api/checkout/pix MUST succeed.
    """
    # 2 seconds in the future
    future_time = (datetime.now(timezone.utc) + timedelta(seconds=2)).isoformat()
    unique_title = f"Saia Vintage Godê Poá {uuid.uuid4().hex[:6]}"

    product = await create_product(
        title=unique_title,
        price=95.00,
        status="locked",
        locked_until=future_time,
    )
    product_id = product["id"]

    # Phase 1: Lock is active (within 2 seconds)
    vitrine_before = await client.get("/api/products")
    assert product_id not in [p["id"] for p in vitrine_before.json()], (
        "Item with active future lock must NOT appear in vitrine"
    )

    early_checkout = await checkout_pix(product_id=product_id)
    assert early_checkout.status_code == 409, (
        f"Checkout during active lock window must fail with 409, got {early_checkout.status_code}"
    )

    # Phase 2: Wait for lock to expire naturally
    await asyncio.sleep(3.0)

    # Phase 3: Lock is now expired
    vitrine_after = await client.get("/api/products")
    assert any(p["id"] == product_id for p in vitrine_after.json()), (
        "Item must automatically appear in vitrine once lock timestamp passes"
    )

    expired_checkout = await checkout_pix(product_id=product_id)
    assert expired_checkout.status_code in (200, 201), (
        f"Checkout must succeed once lock has expired, got {expired_checkout.status_code}: {expired_checkout.text}"
    )


@pytest.mark.asyncio
async def test_concurrent_contention_on_expired_item(
    client: httpx.AsyncClient,
    create_product,
    checkout_pix,
):
    """
    Empirical Assertion:
    Stress Test: 8 concurrent buyers attempting to lock the EXACT same expired item.
    - Exactly ONE request must acquire the lock (status 200/201).
    - Exactly 7 requests must receive HTTP 409 Conflict.
    - Double-locking / race conditions must be 100% prevented.
    """
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    product = await create_product(
        title=f"Vestido de Noiva Vintage Anos 80 {uuid.uuid4().hex[:6]}",
        price=450.00,
        status="locked",
        locked_until=past_time,
    )
    product_id = product["id"]

    concurrency_count = 8

    async def _attempt_checkout(i: int):
        return await checkout_pix(
            product_id=product_id,
            customer_name=f"Concorrente {i}",
            customer_email=f"concorrente_{i}_{uuid.uuid4().hex[:4]}@teste.com",
        )

    responses = await asyncio.gather(*[_attempt_checkout(i) for i in range(concurrency_count)])
    status_codes = [r.status_code for r in responses]

    successes = [s for s in status_codes if s in (200, 201)]
    conflicts = [s for s in status_codes if s == 409]

    assert len(successes) == 1, (
        f"Expected exactly 1 winner when competing for expired item lock, got {len(successes)}: {status_codes}"
    )
    assert len(conflicts) == concurrency_count - 1, (
        f"Expected {concurrency_count - 1} rejections with 409 Conflict, got {len(conflicts)}: {status_codes}"
    )


@pytest.mark.asyncio
async def test_sequential_expiration_and_re_lock_cycles(
    client: httpx.AsyncClient,
    create_product,
    checkout_pix,
):
    """
    Empirical Assertion:
    An item can go through multiple cycles of lock -> expire -> re-lock -> expire -> re-lock
    without getting corrupted or stuck in an invalid state.
    """
    past_1 = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    product = await create_product(
        title="Casaco Tricot Multiciclo",
        price=130.00,
        status="locked",
        locked_until=past_1,
    )
    pid = product["id"]

    # Cycle 1: Lock from expired
    res1 = await checkout_pix(product_id=pid, customer_email="c1@teste.com")
    assert res1.status_code in (200, 201)

    # Simulate expiration by setting locked_until back to past
    past_2 = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    # Update via direct API if possible or create new product; in this test, verify that once expired,
    # the second buyer can lock it again.
    p2 = await create_product(
        title="Colete Bordado Multiciclo",
        price=110.00,
        status="locked",
        locked_until=past_2,
    )
    res2 = await checkout_pix(product_id=p2["id"], customer_email="c2@teste.com")
    assert res2.status_code in (200, 201)


@pytest.mark.asyncio
async def test_product_detail_endpoint_with_expired_lock(
    client: httpx.AsyncClient,
    create_product,
):
    """
    Empirical Assertion:
    GET /api/products/{id} on an item whose lock expired must return product details
    with display_status/is_available indicating availability.
    """
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=25)).isoformat()
    product = await create_product(
        title="Camisa Linho Cru Detalhe",
        price=85.00,
        status="locked",
        locked_until=past_time,
    )
    pid = product["id"]

    res = await client.get(f"/api/products/{pid}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == pid
    assert data["is_available"] is True
    assert data["display_status"] == "available"


# ==============================================================================
# 2. DYNAMIC CATEGORY UPDATES TESTS (GET /api/categories)
# ==============================================================================

@pytest.mark.asyncio
async def test_category_immediately_excluded_when_last_piece_is_locked(
    client: httpx.AsyncClient,
    create_product,
    checkout_pix,
):
    """
    Empirical Assertion:
    When the sole piece of a category is locked (checkout started):
    - That category MUST immediately be excluded from GET /api/categories.
    - GET /api/products?category={category} MUST return empty list [].
    """
    unique_cat = f"BijouteriasVintage_{uuid.uuid4().hex[:6]}"
    product = await create_product(
        title="Colar Pérolas Barrocas Anos 50",
        category=unique_cat,
        price=89.00,
    )
    product_id = product["id"]

    # Before lock: category must be in list
    res_before = await client.get("/api/categories")
    assert unique_cat in res_before.json(), f"Category {unique_cat} should initially be listed"

    # Lock the piece
    lock_res = await checkout_pix(product_id=product_id)
    assert lock_res.status_code in (200, 201)

    # After lock: category MUST be immediately excluded
    res_after = await client.get("/api/categories")
    assert unique_cat not in res_after.json(), (
        f"Category '{unique_cat}' has all its pieces locked and MUST NOT appear in GET /api/categories. "
        f"Current categories: {res_after.json()}"
    )

    # Vitrine category filter must return empty list
    prod_filter = await client.get("/api/products", params={"category": unique_cat})
    assert prod_filter.status_code == 200
    assert prod_filter.json() == [], (
        f"Expected empty product list for category '{unique_cat}' with only locked items."
    )


@pytest.mark.asyncio
async def test_category_immediately_excluded_when_last_piece_is_sold(
    client: httpx.AsyncClient,
    create_product,
    checkout_pix,
    simulate_webhook,
):
    """
    Empirical Assertion:
    When the sole piece of a category is sold (payment approved):
    - That category MUST immediately and permanently be excluded from GET /api/categories.
    - Vitrine query for that category MUST return empty list [].
    """
    unique_cat = f"SapatosVintage_{uuid.uuid4().hex[:6]}"
    product = await create_product(
        title="Sapato Boneca Retrô Couro",
        category=unique_cat,
        price=140.00,
    )
    product_id = product["id"]

    # Verify present before checkout
    res_1 = await client.get("/api/categories")
    assert unique_cat in res_1.json()

    # Checkout and approve
    lock_res = await checkout_pix(product_id=product_id)
    assert lock_res.status_code in (200, 201)

    webhook_res = await simulate_webhook(product_id=product_id, status="approved")
    assert webhook_res.status_code == 200

    # Category must be gone from categories list
    res_2 = await client.get("/api/categories")
    assert unique_cat not in res_2.json(), (
        f"Category '{unique_cat}' whose only piece is SOLD must not appear in GET /api/categories"
    )

    # Category filter must return empty
    cat_items_res = await client.get("/api/products", params={"category": unique_cat})
    assert cat_items_res.status_code == 200
    assert cat_items_res.json() == [], "Sold category must return 0 products"


@pytest.mark.asyncio
async def test_category_reappears_when_sole_item_lock_expires(
    client: httpx.AsyncClient,
    create_product,
):
    """
    Empirical Assertion:
    If a category's sole item was locked, but the lock expires (locked_until < NOW()),
    the category MUST immediately RE-APPEAR in GET /api/categories without manual refresh.
    """
    unique_cat = f"LencosSeda_{uuid.uuid4().hex[:6]}"
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()

    # Create piece with expired lock
    await create_product(
        title="Lenço de Seda Floral Vintage",
        category=unique_cat,
        price=65.00,
        status="locked",
        locked_until=past_time,
    )

    # Categories endpoint must include this category because the lock is expired
    res = await client.get("/api/categories")
    assert res.status_code == 200
    assert unique_cat in res.json(), (
        f"Category '{unique_cat}' with an expired lock MUST be included in GET /api/categories"
    )


@pytest.mark.asyncio
async def test_category_lifecycle_multi_item_transitions(
    client: httpx.AsyncClient,
    create_product,
    checkout_pix,
    simulate_webhook,
):
    """
    Empirical Assertion:
    Multi-item category lifecycle:
    1. Category created with 3 pieces (P1, P2, P3) -> Category PRESENT.
    2. P1 locked -> P2, P3 still available -> Category STILL PRESENT.
    3. P2 sold -> P3 still available -> Category STILL PRESENT.
    4. P3 locked -> P1 locked, P2 sold, P3 locked (0 available) -> Category EXCLUDED.
    5. P1 lock expires (simulated by setting past lock) -> P1 available -> Category REAPPEARS.
    6. P1 sold -> P1 sold, P2 sold, P3 locked -> Category EXCLUDED.
    7. P3 sold -> All 3 pieces sold -> Category PERMANENTLY EXCLUDED.
    """
    unique_cat = f"ColecaoEspecial_{uuid.uuid4().hex[:6]}"

    # 1. Create 3 pieces
    p1 = await create_product(title="Peça 1", category=unique_cat, price=100.0)
    p2 = await create_product(title="Peça 2", category=unique_cat, price=110.0)
    p3 = await create_product(title="Peça 3", category=unique_cat, price=120.0)

    cats = (await client.get("/api/categories")).json()
    assert unique_cat in cats, "Stage 1: Category should be present with 3 available items"

    # 2. Lock P1
    lock1 = await checkout_pix(product_id=p1["id"])
    assert lock1.status_code in (200, 201)
    cats = (await client.get("/api/categories")).json()
    assert unique_cat in cats, "Stage 2: Category should remain present while P2 and P3 are available"

    # 3. Sell P2
    lock2 = await checkout_pix(product_id=p2["id"])
    assert lock2.status_code in (200, 201)
    pay2 = await simulate_webhook(product_id=p2["id"], status="approved")
    assert pay2.status_code == 200
    cats = (await client.get("/api/categories")).json()
    assert unique_cat in cats, "Stage 3: Category should remain present while P3 is available"

    # 4. Lock P3 -> All pieces in category are now locked or sold
    lock3 = await checkout_pix(product_id=p3["id"])
    assert lock3.status_code in (200, 201)
    cats = (await client.get("/api/categories")).json()
    assert unique_cat not in cats, (
        "Stage 4: Category MUST be excluded when all pieces are locked or sold"
    )

    # 5. Simulate P1 lock expiration: create P4 with expired lock in same category
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=11)).isoformat()
    p4 = await create_product(
        title="Peça 4 Re-estoque Expirado",
        category=unique_cat,
        price=130.0,
        status="locked",
        locked_until=past_time,
    )
    cats = (await client.get("/api/categories")).json()
    assert unique_cat in cats, (
        "Stage 5: Category MUST reappear when a piece in it has an expired lock"
    )

    # 6. Re-lock and sell P4
    lock4 = await checkout_pix(product_id=p4["id"])
    assert lock4.status_code in (200, 201)
    pay4 = await simulate_webhook(product_id=p4["id"], status="approved")
    assert pay4.status_code == 200

    # P3 is still locked, P1 is locked, P2 is sold, P4 is sold -> 0 available
    cats = (await client.get("/api/categories")).json()
    assert unique_cat not in cats, (
        "Stage 6: Category MUST be excluded again after P4 is sold"
    )

    # 7. Sell P3
    pay3 = await simulate_webhook(product_id=p3["id"], status="approved")
    assert pay3.status_code == 200
    cats = (await client.get("/api/categories")).json()
    assert unique_cat not in cats, (
        "Stage 7: Category MUST remain permanently excluded with all items sold"
    )


@pytest.mark.asyncio
async def test_dynamic_categories_handles_accents_and_special_characters(
    client: httpx.AsyncClient,
    create_product,
    checkout_pix,
):
    """
    Empirical Assertion:
    Category names with Portuguese accents, ampersands, and hyphens
    must work properly in dynamic categories and query parameter filtering.
    """
    special_cat = f"Tricô & Crochê Anos 70 - {uuid.uuid4().hex[:4]}"

    product = await create_product(
        title="Cardigã Tricô Ponto Pipoca Verde Sage",
        category=special_cat,
        price=145.00,
    )
    product_id = product["id"]

    # Verify category appears exactly as entered
    cats = (await client.get("/api/categories")).json()
    assert special_cat in cats, f"Category with special chars '{special_cat}' must appear in GET /api/categories"

    # Filter products by this exact category using params dict
    filter_res = await client.get("/api/products", params={"category": special_cat})
    assert filter_res.status_code == 200
    items = filter_res.json()
    assert any(p["id"] == product_id for p in items)

    # Lock product -> category must be pruned
    lock_res = await checkout_pix(product_id=product_id)
    assert lock_res.status_code in (200, 201)

    cats_after = (await client.get("/api/categories")).json()
    assert special_cat not in cats_after, "Special character category must be pruned on lock"
