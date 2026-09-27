"""
E2E Atomic Lock & 10-Minute Expiration Test Suite for Vintage Brechó.
Verifies atomic lock acquisition, 10-minute expiration window, automatic showcase re-entry,
and exclusion of locked pieces from public showcase (GET /api/products).
Requirements: R2, PROJECT.md Interface Contracts #1 & #3.
"""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest


@pytest.mark.asyncio
async def test_lock_setting_sets_10_minute_duration(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    R2 Requirement:
    Starting checkout sets status='locked' with 10-minute duration.
    The response must specify expires_in = 600 (seconds) or return a lock timestamp ~10m in future.
    """
    product = await create_product(title="Colete Tricô Artesanal", price=115.00)
    product_id = product["id"]

    checkout_res = await checkout_pix(product_id=product_id)
    assert checkout_res.status_code in (200, 201), f"Checkout failed: {checkout_res.text}"

    data = checkout_res.json()
    assert "expires_in" in data, f"Checkout response missing 'expires_in': {data}"
    assert data["expires_in"] == 600 or (590 <= data["expires_in"] <= 600), (
        f"Expected expires_in ~600 seconds (10 minutes), got: {data['expires_in']}"
    )


@pytest.mark.asyncio
async def test_locked_product_excluded_from_public_products(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    R2 Requirement:
    Public listing (GET /api/products) must return ONLY available items or expired locks.
    Actively locked items MUST be excluded from the showcase.
    """
    product = await create_product(title="Jaqueta Jeans CGC Anos 90", price=160.00)
    product_id = product["id"]

    # 1. Product must appear in public vitrine initially
    list_res_1 = await client.get("/api/products")
    assert list_res_1.status_code == 200
    catalog_1 = list_res_1.json()
    assert any(p["id"] == product_id for p in catalog_1), "Fresh product should appear in vitrine"

    # 2. Lock the product via checkout
    lock_res = await checkout_pix(product_id=product_id)
    assert lock_res.status_code in (200, 201)

    # 3. Product must immediately disappear from public vitrine
    list_res_2 = await client.get("/api/products")
    assert list_res_2.status_code == 200
    catalog_2 = list_res_2.json()
    assert not any(p["id"] == product_id for p in catalog_2), (
        f"Product {product_id} is locked and must NOT appear in GET /api/products"
    )

    # 4. Check category filter also excludes it
    cat = product.get("category")
    if cat:
        list_cat = await client.get(f"/api/products?category={cat}")
        assert list_cat.status_code == 200
        cat_items = list_cat.json()
        assert not any(p["id"] == product_id for p in cat_items), (
            f"Locked product {product_id} must not appear in category filter {cat}"
        )


@pytest.mark.asyncio
async def test_active_lock_rejects_second_reservation(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    R2 Requirement:
    Attempting to reserve/checkout an actively locked item returns HTTP 409 Conflict.
    """
    product = await create_product(title="Vestido Festa Veludo Molhado", price=199.00)
    product_id = product["id"]

    # First reservation succeeds
    res1 = await checkout_pix(product_id=product_id, customer_email="cliente1@teste.com")
    assert res1.status_code in (200, 201)

    # Second reservation during active lock fails with 409
    res2 = await checkout_pix(product_id=product_id, customer_email="cliente2@teste.com")
    assert res2.status_code == 409, (
        f"Expected HTTP 409 Conflict for actively locked piece, got {res2.status_code}: {res2.text}"
    )


@pytest.mark.asyncio
async def test_multiple_products_lock_independence(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    Locking product A must NOT affect product B's availability or locking capability.
    """
    prod_a = await create_product(title="Macacão Linho Rústico", price=140.00)
    prod_b = await create_product(title="Trench Coat Vintage Bege", price=220.00)

    # Lock prod_a
    lock_a = await checkout_pix(product_id=prod_a["id"])
    assert lock_a.status_code in (200, 201)

    # Vitrine must still show prod_b, but not prod_a
    vitrine = await client.get("/api/products")
    assert vitrine.status_code == 200
    ids = [p["id"] for p in vitrine.json()]
    assert prod_b["id"] in ids, "prod_b should still be available in vitrine"
    assert prod_a["id"] not in ids, "prod_a must be excluded from vitrine"

    # Now lock prod_b independently
    lock_b = await checkout_pix(product_id=prod_b["id"])
    assert lock_b.status_code in (200, 201), "prod_b should lock successfully"


@pytest.mark.asyncio
async def test_automatic_lock_expiration_re_enables_purchase(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    R2 Requirement:
    Automatic Lock Expiration:
    The SQL query is:
    UPDATE products SET status = 'locked', locked_until = NOW() + INTERVAL '10 minutes'
    WHERE id = :id AND (status = 'available' OR (status = 'locked' AND locked_until < NOW()));

    When a lock's locked_until is in the past:
    1. A new checkout must succeed without needing a background worker/cron.
    2. The item must be returned in GET /api/products.
    """
    # Create product with simulated expired lock if admin endpoint supports status/locked_until
    # or create product and test through expired lock handling
    product = await create_product(
        title="Lenço Seda Pura Italiano",
        price=75.00,
        status="locked",
        locked_until=(datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
    )
    product_id = product["id"]

    # Since locked_until is in the past, it should be visible in vitrine
    vitrine_res = await client.get("/api/products")
    assert vitrine_res.status_code == 200
    catalog = vitrine_res.json()
    assert any(p["id"] == product_id for p in catalog), (
        "Product with expired lock (< NOW()) must automatically appear in GET /api/products"
    )

    # And a new checkout must be allowed to acquire the lock
    re_lock_res = await client.post(
        "/api/checkout/pix",
        json={
            "product_id": product_id,
            "customer_name": "Novo Comprador",
            "customer_email": "novo@teste.com",
        },
    )
    assert re_lock_res.status_code in (200, 201), (
        f"Product with expired lock must be re-lockable by new buyer: {re_lock_res.text}"
    )
