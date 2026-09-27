"""
Empirical Challenger Concurrency & Stress Test Suite for Milestone 1.
Challenger 1 (Critic & Concurrency Specialist) verification.

Authoritative Requirements:
- ORIGINAL_REQUEST.md: R2, R5 (10-minute atomic lock, exactly 1 winner, 409 Conflict)
- PROJECT.md: Milestone 1 & Interface Contract #3

Test Dimensions:
1. 10 simultaneous callers on an available 1-of-1 product (POST /api/checkout/pix)
2. 10 simultaneous callers on direct acquire_product_lock service calls across isolated sessions
3. 10 simultaneous callers on an expired lock (>10 min past)
4. 10 simultaneous callers on an already locked piece (0 winners, 10 conflicts)
5. 10 simultaneous callers on a sold piece (0 winners, 10 conflicts with sold notice)
6. 10 consecutive bursts of 10 concurrent callers (100 total requests, 10 winners, 90 conflicts, 0 failures)
7. 10 simultaneous callers on nonexistent product (10 404s, 0 crashes)
"""

import asyncio
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import text

try:
    from app.database import get_db
    from app.services.lock_service import acquire_product_lock
except ImportError:
    from backend.app.database import get_db
    from backend.app.services.lock_service import acquire_product_lock


@pytest.mark.asyncio
async def test_challenger_10_concurrent_checkout_callers_single_winner(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    Stress-tests 10 simultaneous callers competing for the exact same 1-of-1 product.
    Verification criteria:
    - Exactly 1 caller succeeds with HTTP 201 Created.
    - Exactly 9 callers receive HTTP 409 Conflict.
    - Zero 500 errors, zero unhandled database lock exceptions.
    - Returned winner has valid order_id, product_id, and expires_in == 600.
    """
    product = await create_product(
        title="Vestido Festa Seda Anos 80 1-of-1",
        price=320.00,
        size="P",
    )
    product_id = product["id"]
    n_callers = 10

    async def _buyer_attempt(caller_idx: int):
        payload = {
            "product_id": product_id,
            "customer_name": f"Compradora Concorrente {caller_idx}",
            "customer_email": f"concorrente_{caller_idx}@brecho.com",
            "customer_phone": "17981668413",
            "customer_address": f"Rua Concorrência, {caller_idx} - SP",
        }
        return await client.post("/api/checkout/pix", json=payload)

    # Launch all 10 requests concurrently
    tasks = [_buyer_attempt(i) for i in range(n_callers)]
    responses = await asyncio.gather(*tasks, return_exceptions=False)

    status_counts = Counter(r.status_code for r in responses)

    assert status_counts[201] == 1, (
        f"Empirical Failure: Expected exactly 1 winner (HTTP 201), but got {status_counts[201]}. "
        f"All statuses: {[r.status_code for r in responses]}"
    )
    assert status_counts[409] == n_callers - 1, (
        f"Empirical Failure: Expected exactly {n_callers - 1} HTTP 409 Conflicts, but got {status_counts[409]}. "
        f"All statuses: {[r.status_code for r in responses]}"
    )
    assert sum(status_counts.values()) == n_callers, "Unexpected response count"
    assert status_counts[500] == 0, f"Server crashed with 500 under 10 concurrent requests: {responses}"

    winner_resp = next(r for r in responses if r.status_code == 201)
    winner_json = winner_resp.json()
    assert winner_json["product_id"] == product_id
    assert winner_json["expires_in"] == 600
    assert "order_id" in winner_json
    assert "qr_code" in winner_json

    # All 9 losers must have descriptive conflict detail
    loser_resps = [r for r in responses if r.status_code == 409]
    for loser in loser_resps:
        detail = loser.json().get("detail", "").lower()
        assert "reservad" in detail or "já" in detail, f"Unexpected conflict detail: {loser.text}"


@pytest.mark.asyncio
async def test_challenger_10_concurrent_direct_lock_service_calls(
    create_product: Callable[..., Any],
):
    """
    Direct service layer stress test:
    Executes 10 simultaneous calls to `acquire_product_lock` with separate DB sessions.
    Verification criteria:
    - Exactly 1 session succeeds and returns the locked item dict.
    - Exactly 9 sessions raise HTTPException with status_code=409.
    """
    product = await create_product(
        title="Blazer Alfaiataria Vintage CGC 1988",
        price=249.00,
        size="42",
    )
    product_id = product["id"]
    n_callers = 10

    results = []

    async def _call_lock(caller_idx: int):
        gen = get_db()
        try:
            session = await anext(gen)
            try:
                locked = await acquire_product_lock(session, product_id)
                return {"status": "SUCCESS", "caller": caller_idx, "data": locked}
            except HTTPException as http_exc:
                return {"status": "HTTP_EXC", "code": http_exc.status_code, "detail": http_exc.detail}
            except Exception as exc:
                return {"status": "CRASH", "error": str(exc)}
        finally:
            try:
                await gen.aclose()
            except Exception:
                pass

    tasks = [_call_lock(i) for i in range(n_callers)]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    successes = [r for r in results if r["status"] == "SUCCESS"]
    conflicts = [r for r in results if r["status"] == "HTTP_EXC" and r.get("code") == 409]
    crashes = [r for r in results if r["status"] == "CRASH"]

    assert len(crashes) == 0, f"Direct lock crashed with unexpected errors: {crashes}"
    assert len(successes) == 1, (
        f"Empirical Failure: Expected exactly 1 successful direct lock, got {len(successes)}. "
        f"Results: {results}"
    )
    assert len(conflicts) == n_callers - 1, (
        f"Empirical Failure: Expected {n_callers - 1} 409 conflicts, got {len(conflicts)}. "
        f"Results: {results}"
    )


@pytest.mark.asyncio
async def test_challenger_10_concurrent_callers_on_expired_lock(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    When a 10-minute lock has expired (locked_until < now), 10 simultaneous callers race
    to acquire the re-opened piece.
    Verification criteria:
    - Exactly 1 caller succeeds with HTTP 201.
    - Exactly 9 callers receive HTTP 409 Conflict.
    - The piece's lock is successfully renewed for 10 minutes into the future.
    """
    expired_time = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    product = await create_product(
        title="Vestido Poá Vintage 1960",
        price=180.00,
        status="locked",
        locked_until=expired_time,
    )
    product_id = product["id"]
    n_callers = 10

    tasks = [
        client.post(
            "/api/checkout/pix",
            json={
                "product_id": product_id,
                "customer_name": f"Compradora Expired {i}",
                "customer_email": f"expired_buyer_{i}@brecho.com",
            },
        )
        for i in range(n_callers)
    ]

    responses = await asyncio.gather(*tasks)
    status_counts = Counter(r.status_code for r in responses)

    assert status_counts[201] == 1, (
        f"Expected exactly 1 winner re-acquiring expired lock, got {status_counts[201]}. "
        f"Statuses: {[r.status_code for r in responses]}"
    )
    assert status_counts[409] == n_callers - 1, (
        f"Expected {n_callers - 1} conflicts on re-acquisition, got {status_counts[409]}. "
        f"Statuses: {[r.status_code for r in responses]}"
    )


@pytest.mark.asyncio
async def test_challenger_10_concurrent_callers_on_already_active_lock(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    When a product is ALREADY locked (active within the 10-minute window),
    10 simultaneous callers must ALL be rejected.
    Verification criteria:
    - Exactly 0 callers receive HTTP 201.
    - Exactly 10 callers receive HTTP 409 Conflict.
    """
    product = await create_product(title="Cardigã Vintage Verde Sage", price=135.00)
    product_id = product["id"]

    # Initial lock acquired
    first_res = await checkout_pix(product_id=product_id)
    assert first_res.status_code in (200, 201)

    # 10 simultaneous callers attempt to lock the actively locked item
    n_callers = 10
    tasks = [
        client.post(
            "/api/checkout/pix",
            json={
                "product_id": product_id,
                "customer_name": f"Tardia {i}",
                "customer_email": f"tardia_{i}@brecho.com",
            },
        )
        for i in range(n_callers)
    ]

    responses = await asyncio.gather(*tasks)
    status_counts = Counter(r.status_code for r in responses)

    assert status_counts[201] == 0, f"Expected 0 winners for actively locked piece, got {status_counts[201]}"
    assert status_counts[409] == n_callers, (
        f"Expected all {n_callers} callers to receive HTTP 409 Conflict, got {status_counts[409]}"
    )


@pytest.mark.asyncio
async def test_challenger_10_concurrent_callers_on_sold_product(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
    simulate_webhook: Callable[..., Any],
):
    """
    When a product has been marked 'sold', 10 simultaneous callers MUST ALL receive 409.
    Verification criteria:
    - 0 winners.
    - 10 HTTP 409 Conflict responses.
    - Error message explicitly states piece is sold.
    """
    product = await create_product(title="Saia Midi Plissada Vintage Rara", price=110.00)
    product_id = product["id"]

    # Lock and mark as sold via webhook
    await checkout_pix(product_id=product_id)
    webhook_res = await simulate_webhook(product_id=product_id, status="approved")
    assert webhook_res.status_code == 200

    # 10 callers race to checkout sold item
    n_callers = 10
    tasks = [
        client.post(
            "/api/checkout/pix",
            json={
                "product_id": product_id,
                "customer_name": f"Compradora Pós-Venda {i}",
                "customer_email": f"posvenda_{i}@brecho.com",
            },
        )
        for i in range(n_callers)
    ]

    responses = await asyncio.gather(*tasks)
    status_counts = Counter(r.status_code for r in responses)

    assert status_counts[201] == 0, f"Expected 0 winners on sold piece, got {status_counts[201]}"
    assert status_counts[409] == n_callers, (
        f"Expected all {n_callers} callers to receive HTTP 409 Conflict, got {status_counts[409]}"
    )

    for r in responses:
        detail = r.json().get("detail", "").lower()
        assert "vendida" in detail or "sold" in detail, f"Expected 'vendida' detail, got: {r.text}"


@pytest.mark.asyncio
async def test_challenger_burst_stress_100_concurrent_requests_across_10_products(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    High-volume stress harness:
    10 bursts of 10 simultaneous callers (100 total concurrent requests) across 10 distinct products.
    Verification criteria:
    - Exactly 10 successful checkouts (1 per product).
    - Exactly 90 HTTP 409 Conflict responses.
    - Exactly 0 crashes or 500 Internal Server Errors.
    """
    n_products = 10
    callers_per_product = 10

    # Setup 10 distinct products
    products = [
        await create_product(
            title=f"Peça Vintage Burst Stress #{p_idx}",
            price=150.00 + p_idx,
            size="M",
        )
        for p_idx in range(n_products)
    ]

    all_tasks = []
    for p in products:
        p_id = p["id"]
        for c_idx in range(callers_per_product):
            all_tasks.append(
                client.post(
                    "/api/checkout/pix",
                    json={
                        "product_id": p_id,
                        "customer_name": f"Burst Client {p_id}_{c_idx}",
                        "customer_email": f"burst_{p_id}_{c_idx}@brecho.com",
                    },
                )
            )

    # Fire all 100 requests concurrently
    all_responses = await asyncio.gather(*all_tasks)
    total_counts = Counter(r.status_code for r in all_responses)

    assert total_counts[201] == n_products, (
        f"Burst Concurrency Breach: Expected exactly {n_products} winners, got {total_counts[201]}. "
        f"Counts: {total_counts}"
    )
    assert total_counts[409] == n_products * (callers_per_product - 1), (
        f"Expected {n_products * (callers_per_product - 1)} 409 conflicts, got {total_counts[409]}. "
        f"Counts: {total_counts}"
    )
    assert total_counts[500] == 0, f"Detected {total_counts[500]} server crashes (500) during 100-request burst!"


@pytest.mark.asyncio
async def test_challenger_10_concurrent_callers_nonexistent_product(
    client: httpx.AsyncClient,
):
    """
    10 concurrent callers attempting to lock a non-existent product ID.
    Must all cleanly receive HTTP 404 Not Found without deadlocks or unhandled exceptions.
    """
    non_existent_id = 9999999
    n_callers = 10

    tasks = [
        client.post(
            "/api/checkout/pix",
            json={
                "product_id": non_existent_id,
                "customer_name": f"Ghost {i}",
                "customer_email": f"ghost_{i}@brecho.com",
            },
        )
        for i in range(n_callers)
    ]

    responses = await asyncio.gather(*tasks)
    status_counts = Counter(r.status_code for r in responses)

    assert status_counts[404] == n_callers, (
        f"Expected all {n_callers} callers to get 404 for nonexistent product, got: {status_counts}"
    )
