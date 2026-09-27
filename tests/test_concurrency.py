"""
E2E Concurrency & Race Condition Test Suite for Vintage Brechó.
Verifies that 1-of-1 unique pieces can never be double-locked or double-sold under concurrent requests.
Requirements: R2, R5, ORIGINAL_REQUEST.md, PROJECT.md Interface Contract #3.
"""

import asyncio
from collections.abc import Callable
from typing import Any

import httpx
import pytest


@pytest.mark.asyncio
async def test_two_simultaneous_requests_exact_one_wins_one_gets_409(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    Authoritative Requirement R2 / Acceptance Criteria:
    When 2 simultaneous requests attempt to lock the same single piece:
    - Exactly 1 request succeeds with HTTP 201 (or 200).
    - Exactly 1 request fails with HTTP 409 Conflict.
    - No double-booking or corrupt state.
    """
    # 1. Arrange: Create a fresh available 1-of-1 vintage product
    product = await create_product(
        title="Vestido Seda Pura 1975",
        price=189.90,
        size="M",
    )
    product_id = product["id"]

    # 2. Act: Prepare two simultaneous checkout/lock requests for the same piece
    payload_buyer1 = {
        "product_id": product_id,
        "customer_name": "Maria Silva",
        "customer_email": "maria.silva@example.com",
        "customer_phone": "17981668413",
        "customer_address": "Av. Vintage, 100 - São Paulo, SP",
    }
    payload_buyer2 = {
        "product_id": product_id,
        "customer_name": "Ana Oliveira",
        "customer_email": "ana.oliveira@example.com",
        "customer_phone": "17981668414",
        "customer_address": "Rua Retrô, 200 - Campinas, SP",
    }

    req1 = client.post("/api/checkout/pix", json=payload_buyer1)
    req2 = client.post("/api/checkout/pix", json=payload_buyer2)

    responses = await asyncio.gather(req1, req2, return_exceptions=False)
    status_codes = [r.status_code for r in responses]

    # 3. Assert: Exactly one 201/200 and exactly one 409 Conflict
    success_responses = [r for r in responses if r.status_code in (200, 201)]
    conflict_responses = [r for r in responses if r.status_code == 409]

    assert len(success_responses) == 1, (
        f"Expected exactly 1 successful checkout, but got {len(success_responses)}. "
        f"Status codes received: {status_codes}"
    )
    assert len(conflict_responses) == 1, (
        f"Expected exactly 1 HTTP 409 Conflict response, but got {len(conflict_responses)}. "
        f"Status codes received: {status_codes}"
    )

    # Winner verification: Valid order and PIX payment info returned
    winner_data = success_responses[0].json()
    assert "order_id" in winner_data or "id" in winner_data
    assert winner_data.get("product_id") == product_id or winner_data.get("productId") == product_id

    # Loser verification: 409 with explanatory message
    conflict_data = conflict_responses[0].json()
    error_detail = conflict_data.get("detail", conflict_data.get("message", "")).lower()
    assert any(keyword in error_detail for keyword in ["reservad", "conflict", "indispon", "já"]), (
        f"Expected conflict error detail to explain reservation, got: {error_detail}"
    )


@pytest.mark.asyncio
async def test_stress_n_concurrent_requests_single_winner(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    Stress concurrency: 5 simultaneous requests attempting to lock the same single piece.
    Asserts:
    - Exactly 1 request succeeds (HTTP 201/200).
    - Exactly 4 requests receive HTTP 409 Conflict.
    - Zero unhandled 500 internal server errors.
    """
    product = await create_product(
        title="Casaco Tweed Vintage Colecionador",
        price=299.00,
        size="G",
    )
    product_id = product["id"]
    n_concurrency = 5

    tasks = [
        client.post(
            "/api/checkout/pix",
            json={
                "product_id": product_id,
                "customer_name": f"Competidor {i}",
                "customer_email": f"buyer_{i}@teste.com",
            },
        )
        for i in range(n_concurrency)
    ]

    responses = await asyncio.gather(*tasks, return_exceptions=False)
    status_codes = [r.status_code for r in responses]

    # Verify no 500 or crash occurred under lock contention
    assert all(code in (200, 201, 409) for code in status_codes), (
        f"Unexpected status codes received during stress concurrency: {status_codes}"
    )

    success_count = sum(1 for code in status_codes if code in (200, 201))
    conflict_count = sum(1 for code in status_codes if code == 409)

    assert success_count == 1, (
        f"Concurrency breach: expected exactly 1 winner out of {n_concurrency}, got {success_count}. "
        f"All statuses: {status_codes}"
    )
    assert conflict_count == n_concurrency - 1, (
        f"Expected {n_concurrency - 1} 409 Conflicts, got {conflict_count}. All statuses: {status_codes}"
    )


@pytest.mark.asyncio
async def test_concurrent_lock_on_already_locked_item_rejects_both(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    If a product is already under an active lock, any subsequent concurrent requests
    must both be rejected with HTTP 409 Conflict.
    """
    product = await create_product(title="Bolsa Couro Legítimo Anos 80", price=145.00)
    product_id = product["id"]

    # Pre-lock the item
    first_lock = await checkout_pix(product_id=product_id, customer_email="primeiro@teste.com")
    assert first_lock.status_code in (200, 201), f"Pre-lock failed: {first_lock.text}"

    # Now launch 2 simultaneous requests
    req1 = client.post(
        "/api/checkout/pix",
        json={"product_id": product_id, "customer_email": "tardio1@teste.com", "customer_name": "Tardio 1"},
    )
    req2 = client.post(
        "/api/checkout/pix",
        json={"product_id": product_id, "customer_email": "tardio2@teste.com", "customer_name": "Tardio 2"},
    )

    responses = await asyncio.gather(req1, req2)
    statuses = [r.status_code for r in responses]

    assert statuses == [409, 409], (
        f"Both concurrent requests to an already locked item should be 409, got: {statuses}"
    )


@pytest.mark.asyncio
async def test_concurrent_requests_on_different_products_both_succeed(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    Verifies that concurrency locking is isolated per product:
    Concurrent checkouts on distinct products (Product A and Product B)
    must both succeed without false lock contention.
    """
    product_a = await create_product(title="Saia Plissada Xadrez", price=89.00)
    product_b = await create_product(title="Blusa Linho Bordada", price=95.00)

    req_a = client.post(
        "/api/checkout/pix",
        json={"product_id": product_a["id"], "customer_email": "comprador.a@teste.com", "customer_name": "Comprador A"},
    )
    req_b = client.post(
        "/api/checkout/pix",
        json={"product_id": product_b["id"], "customer_email": "comprador.b@teste.com", "customer_name": "Comprador B"},
    )

    resp_a, resp_b = await asyncio.gather(req_a, req_b)

    assert resp_a.status_code in (200, 201), f"Product A checkout failed: {resp_a.text}"
    assert resp_b.status_code in (200, 201), f"Product B checkout failed: {resp_b.text}"


@pytest.mark.asyncio
async def test_concurrency_exclusion_from_public_showcase(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    After a race condition where one buyer locks the product,
    verify that GET /api/products immediately stops listing the locked product.
    """
    product = await create_product(title="Chemise Vintage Estampada", price=110.00)
    product_id = product["id"]

    # Verify visible before lock
    res_before = await client.get("/api/products")
    assert res_before.status_code == 200
    ids_before = [p["id"] for p in res_before.json()]
    assert product_id in ids_before, "Product should be in showcase before lock"

    # Lock piece via checkout
    lock_res = await checkout_pix(product_id=product_id)
    assert lock_res.status_code in (200, 201)

    # Verify immediately excluded from vitrine
    res_after = await client.get("/api/products")
    assert res_after.status_code == 200
    ids_after = [p["id"] for p in res_after.json()]
    assert product_id not in ids_after, "Locked product must be excluded from public showcase"
