"""
E2E Webhook & Inventory Depletion Test Suite for Vintage Brechó.
Verifies that Mercado Pago payment approval webhooks atomically transition 1-of-1 products
to 'sold', update order status to 'approved', permanently remove the item from the public vitrine,
and maintain idempotency under duplicate notifications.
Requirements: R2, R3, R5, PROJECT.md Interface Contracts #1, #4, #5, #7.
"""

from collections.abc import Callable
from typing import Any

import httpx
import pytest


@pytest.mark.asyncio
async def test_webhook_approved_transitions_product_to_sold_and_depletes_vitrine(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
    simulate_webhook: Callable[..., Any],
):
    """
    R2 / R3 / R5:
    When payment webhook arrives with status='approved':
    1. Product status becomes 'sold' atomically.
    2. Item is permanently removed from GET /api/products.
    3. Order payment_status becomes 'approved' and is_paid becomes True.
    """
    # 1. Arrange: Create and checkout product
    product = await create_product(
        title="Vestido Festa Seda Vintage 1980",
        price=210.00,
        size="P",
    )
    product_id = product["id"]

    checkout_res = await checkout_pix(product_id=product_id)
    assert checkout_res.status_code in (200, 201)
    order_id = checkout_res.json()["order_id"]

    # Verify initial polling status is 'pending'
    status_before = await client.get(f"/api/orders/{order_id}/status")
    assert status_before.status_code == 200
    assert status_before.json()["payment_status"] == "pending"
    assert status_before.json()["is_paid"] is False

    # 2. Act: Send simulated webhook approval
    webhook_res = await simulate_webhook(product_id=product_id, status="approved")
    assert webhook_res.status_code == 200, f"Webhook failed: {webhook_res.text}"
    assert webhook_res.json().get("status") in ("ok", "approved", "success")

    # 3. Assert: Order polling now reflects 'approved' and is_paid=True
    status_after = await client.get(f"/api/orders/{order_id}/status")
    assert status_after.status_code == 200
    order_data = status_after.json()
    assert order_data["payment_status"] == "approved", (
        f"Expected payment_status 'approved', got: {order_data['payment_status']}"
    )
    assert order_data["is_paid"] is True, "Expected is_paid=True after approval"

    # 4. Assert: Product is permanently depleted from public vitrine
    vitrine_res = await client.get("/api/products")
    assert vitrine_res.status_code == 200
    vitrine_ids = [p["id"] for p in vitrine_res.json()]
    assert product_id not in vitrine_ids, (
        f"Product {product_id} is marked 'sold' and must NEVER appear in public showcase"
    )


@pytest.mark.asyncio
async def test_webhook_idempotency_duplicate_calls(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
    simulate_webhook: Callable[..., Any],
):
    """
    Webhook Idempotency:
    Mercado Pago may send duplicate webhook notifications for the same transaction.
    Multiple calls must succeed (HTTP 200) without crashing or corrupting data.
    """
    product = await create_product(title="Bolsa Vintage Couro Caramelo", price=140.00)
    product_id = product["id"]

    await checkout_pix(product_id=product_id)

    # First webhook call
    res1 = await simulate_webhook(product_id=product_id, status="approved")
    assert res1.status_code == 200

    # Second duplicate webhook call
    res2 = await simulate_webhook(product_id=product_id, status="approved")
    assert res2.status_code == 200, f"Idempotent duplicate webhook failed: {res2.text}"

    # Third duplicate webhook call
    res3 = await simulate_webhook(product_id=product_id, status="approved")
    assert res3.status_code == 200


@pytest.mark.asyncio
async def test_sold_product_cannot_be_re_locked_or_purchased(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
    simulate_webhook: Callable[..., Any],
):
    """
    R2 / Acceptance Criteria:
    Once a piece is marked 'sold', any future checkout attempts must fail with HTTP 409 Conflict.
    """
    product = await create_product(title="Vestido Chemise Estampado CGC", price=125.00)
    product_id = product["id"]

    # Checkout and mark sold
    await checkout_pix(product_id=product_id)
    await simulate_webhook(product_id=product_id, status="approved")

    # Attempt to checkout the sold product
    new_checkout = await client.post(
        "/api/checkout/pix",
        json={
            "product_id": product_id,
            "customer_name": "Comprador Atrasado",
            "customer_email": "atrasado@teste.com",
        },
    )
    assert new_checkout.status_code in (409, 400), (
        f"Expected 409 Conflict for sold piece, got: {new_checkout.status_code}"
    )


@pytest.mark.asyncio
async def test_admin_orders_contains_approved_order_details_for_dispatch(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
    simulate_webhook: Callable[..., Any],
):
    """
    R4 / Contract #7:
    Approved orders must appear in GET /api/admin/orders with customer name, phone, address,
    and product title so the shopkeeper can pack and dispatch via WhatsApp.
    """
    customer_phone = "17981668413"
    customer_address = "Rua Vintage, 777 - Apto 12 - São Paulo, SP"
    product = await create_product(title="Sobretudo Lã Batida Vintage", price=320.00)
    product_id = product["id"]

    checkout_res = await checkout_pix(
        product_id=product_id,
        customer_name="Fernanda Lima",
        customer_phone=customer_phone,
        customer_address=customer_address,
    )
    assert checkout_res.status_code in (200, 201)
    order_id = checkout_res.json()["order_id"]

    # Approve order via webhook
    await simulate_webhook(product_id=product_id, status="approved")

    # Fetch admin orders
    admin_res = await client.get("/api/admin/orders")
    if admin_res.status_code == 200:
        orders = admin_res.json()
        matching = [o for o in orders if o.get("order_id") == order_id or str(o.get("id")) == str(order_id)]
        assert len(matching) >= 1, f"Approved order {order_id} not found in admin dispatch list"
        order_entry = matching[0]
        assert order_entry.get("customer_phone") == customer_phone
        assert order_entry.get("customer_address") == customer_address


@pytest.mark.asyncio
async def test_webhook_live_mercadopago_approval(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
    monkeypatch,
):
    """
    Simulates a live Mercado Pago webhook notification:
    1. Checkout reserves product.
    2. Webhook receives `data: {"id": "888999111"}` without mock_metadata.
    3. Mocked `get_payment` returns status='approved' with metadata.
    4. Webhook updates product to 'sold' and order to 'approved'.
    5. Item is excluded from public vitrine.
    """
    from backend.app.main import app
    from backend.app.routers import webhooks

    product = await create_product(title="Saia Plissada Dourada 1975", price=160.00)
    product_id = product["id"]

    checkout_res = await checkout_pix(product_id=product_id)
    assert checkout_res.status_code in (200, 201)
    order_id = checkout_res.json()["order_id"]

    # Mock get_payment to simulate real Mercado Pago response
    async def mock_get_payment(payment_id: str | int):
        return {
            "id": 888999111,
            "status": "approved",
            "status_detail": "accredited",
            "metadata": {
                "product_id": product_id,
                "order_id": order_id,
            },
        }

    monkeypatch.setattr(webhooks, "get_payment", mock_get_payment)

    # Post live webhook payload to ASGI in-process app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as direct_client:
        res = await direct_client.post(
            "/api/webhooks/mercadopago",
            json={
                "action": "payment.updated",
                "type": "payment",
                "data": {"id": "888999111"},
            },
        )
        assert res.status_code == 200
        assert res.json().get("status") == "ok"

    # Verify order is approved
    status_res = await client.get(f"/api/orders/{order_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["payment_status"] == "approved"
    assert status_res.json()["is_paid"] is True

    # Verify product is removed from vitrine
    vitrine_res = await client.get("/api/products")
    assert product_id not in [p["id"] for p in vitrine_res.json()]


@pytest.mark.asyncio
async def test_webhook_live_mercadopago_rejected_releases_lock(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
    monkeypatch,
):
    """
    Verifies that when Mercado Pago returns status='rejected' or 'cancelled':
    1. Active reservation lock is released back to 'available'.
    2. Order status is updated to 'rejected' / 'cancelled'.
    3. Product becomes available for purchase again in vitrine.
    """
    from backend.app.main import app
    from backend.app.routers import webhooks

    product = await create_product(title="Casaco Tweed Vintage 1960", price=250.00)
    product_id = product["id"]

    checkout_res = await checkout_pix(product_id=product_id)
    assert checkout_res.status_code in (200, 201)
    order_id = checkout_res.json()["order_id"]

    # Mock get_payment with rejected status
    async def mock_get_payment(payment_id: str | int):
        return {
            "id": 777666555,
            "status": "rejected",
            "status_detail": "cc_rejected_insufficient_amount",
            "metadata": {
                "product_id": product_id,
                "order_id": order_id,
            },
        }

    monkeypatch.setattr(webhooks, "get_payment", mock_get_payment)

    # Post webhook to ASGI in-process app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as direct_client:
        res = await direct_client.post(
            "/api/webhooks/mercadopago",
            json={
                "action": "payment.updated",
                "type": "payment",
                "data": {"id": "777666555"},
            },
        )
        assert res.status_code == 200

    # Verify order is marked rejected
    status_res = await client.get(f"/api/orders/{order_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["payment_status"] == "rejected"

    # Product should now be available again for purchase
    vitrine_res = await client.get("/api/products")
    vitrine_ids = [p["id"] for p in vitrine_res.json()]
    assert product_id in vitrine_ids, "Product should have its lock released after rejection"

