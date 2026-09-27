"""
E2E Mercado Pago PIX Checkout Test Suite for Vintage Brechó.
Verifies transparent PIX checkout, R$ 15.00 fixed shipping calculation,
generation of EMVCo QR code and QR code base64 image, and order tracking via polling endpoint.
Requirements: R2, R3, PROJECT.md Interface Contracts #3 & #4.
"""

from collections.abc import Callable
from decimal import Decimal
from typing import Any
import uuid

import httpx
import pytest

from backend.app.services.mercadopago_service import (
    _calculate_crc16,
    create_pix_payment,
    generate_emvco_pix,
)


@pytest.mark.asyncio
async def test_checkout_pix_payload_and_shipping_calculation(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    R3 / Interface Contract #3:
    POST /api/checkout/pix
    - Adds fixed shipping price of R$ 15.00: total_amount = product_price + 15.00.
    - Returns qr_code, qr_code_base64, order_id, expires_in (600 seconds).
    """
    product = await create_product(title="Vestido Festa Plissado Anos 70", price=120.00)
    product_id = product["id"]

    payload = {
        "product_id": product_id,
        "customer_name": "Juliana Mendes",
        "customer_email": "juliana.mendes@teste.com",
        "customer_phone": "17981668413",
        "customer_address": "Rua das Flores, 123, Apto 4, São Paulo - SP, 01234-567",
    }

    res = await client.post("/api/checkout/pix", json=payload)
    assert res.status_code in (200, 201), f"Checkout failed: {res.text}"

    data = res.json()

    # 1. Verify pricing calculations
    assert "shipping_cost" in data, f"Response missing shipping_cost: {data}"
    assert float(data["shipping_cost"]) == 15.00, f"Expected shipping_cost = 15.00, got: {data['shipping_cost']}"

    assert "total_amount" in data, f"Response missing total_amount: {data}"
    expected_total = 120.00 + 15.00
    assert abs(float(data["total_amount"]) - expected_total) < 0.01, (
        f"Expected total_amount {expected_total}, got: {data['total_amount']}"
    )

    # 2. Verify QR Code attributes for mobile copy-paste and desktop scanning
    assert "qr_code" in data, "Response missing 'qr_code' (copia e cola key)"
    assert isinstance(data["qr_code"], str) and len(data["qr_code"]) > 0, "qr_code must be non-empty string"

    assert "qr_code_base64" in data, "Response missing 'qr_code_base64' (scannable QR image)"
    assert isinstance(data["qr_code_base64"], str) and len(data["qr_code_base64"]) > 0, (
        "qr_code_base64 must be non-empty string"
    )

    # 3. Verify order ID and timer
    assert "order_id" in data, "Response missing 'order_id'"
    assert "expires_in" in data, "Response missing 'expires_in'"
    assert data["expires_in"] == 600 or (590 <= data["expires_in"] <= 600)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "product_price,expected_total",
    [
        (89.90, 104.90),
        (49.95, 64.95),
        (199.00, 214.00),
        (15.50, 30.50),
    ],
)
async def test_checkout_shipping_cents_precision(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    product_price: float,
    expected_total: float,
):
    """
    Verifies that shipping of R$ 15.00 is added accurately with 2-decimal floating point precision,
    preventing currency rounding defects.
    """
    product = await create_product(
        title=f"Peça Teste Preço {product_price}",
        price=product_price,
    )

    res = await client.post(
        "/api/checkout/pix",
        json={
            "product_id": product["id"],
            "customer_name": "Testador Moeda",
            "customer_email": "moeda@teste.com",
        },
    )
    assert res.status_code in (200, 201), f"Checkout failed: {res.text}"
    data = res.json()

    assert abs(float(data["total_amount"]) - expected_total) < 0.01, (
        f"Precision error: for price {product_price}, expected total {expected_total}, got {data['total_amount']}"
    )


@pytest.mark.asyncio
async def test_checkout_creates_order_and_tracks_via_polling_endpoint(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    R3 / Interface Contract #4:
    After checkout creation, the order must be queryable via GET /api/orders/{order_id}/status:
    - payment_status: 'pending'
    - is_paid: False
    """
    product = await create_product(title="Casaco Veludo Cotelê", price=170.00)
    product_id = product["id"]

    checkout_res = await client.post(
        "/api/checkout/pix",
        json={
            "product_id": product_id,
            "customer_name": "Beatriz Lima",
            "customer_email": "beatriz@teste.com",
        },
    )
    assert checkout_res.status_code in (200, 201)
    order_id = checkout_res.json()["order_id"]

    # Poll status endpoint
    status_res = await client.get(f"/api/orders/{order_id}/status")
    assert status_res.status_code == 200, f"Failed to poll order status: {status_res.text}"

    status_data = status_res.json()
    assert status_data["order_id"] == order_id
    assert status_data["payment_status"] == "pending"
    assert status_data["is_paid"] is False


@pytest.mark.asyncio
async def test_checkout_nonexistent_product_returns_404(
    client: httpx.AsyncClient,
):
    """
    Edge case: Attempting to checkout a non-existent product ID must return HTTP 404 Not Found.
    """
    res = await client.post(
        "/api/checkout/pix",
        json={
            "product_id": 999999,
            "customer_name": "Fantasma",
            "customer_email": "fantasma@teste.com",
        },
    )
    assert res.status_code == 404, f"Expected 404 for non-existent product, got: {res.status_code}"


@pytest.mark.asyncio
async def test_checkout_missing_fields_validation(
    client: httpx.AsyncClient,
):
    """
    Boundary & Validation:
    Missing product_id, empty customer_email, or malformed payload returns HTTP 422 Unprocessable Entity.
    """
    # Missing product_id
    res1 = await client.post(
        "/api/checkout/pix",
        json={"customer_name": "Incompleto", "customer_email": "inc@teste.com"},
    )
    assert res1.status_code == 422

    # Missing email
    res2 = await client.post(
        "/api/checkout/pix",
        json={"product_id": 1, "customer_name": "Sem Email"},
    )
    assert res2.status_code == 422


@pytest.mark.asyncio
async def test_checkout_repeated_call_on_same_product_returns_409(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    R2 / R3: Sequential second attempt to checkout an already reserved item must return HTTP 409 Conflict.
    """
    product = await create_product(title="Vestido Linho Puro Cru", price=130.00)
    product_id = product["id"]

    res_first = await checkout_pix(product_id=product_id, customer_email="primeiro@teste.com")
    assert res_first.status_code in (200, 201)

    res_second = await checkout_pix(product_id=product_id, customer_email="segundo@teste.com")
    assert res_second.status_code == 409, f"Expected 409 Conflict on second checkout, got: {res_second.status_code}"


@pytest.mark.asyncio
async def test_emvco_pix_generator_structure_and_crc():
    """
    Verifies that the offline EMVCo BR Code generator complies with the
    BACEN / EMVCo standard specifications:
    - Payload format indicator: 000201
    - Merchant Account Info (PIX): tag 26
    - Currency BRL 986: tag 5303986
    - Amount: tag 54
    - Country BR: tag 5802BR
    - Checksum: tag 6304 followed by valid 4-character hex CRC16.
    """
    order_id = uuid.uuid4()
    amount = Decimal("149.90")
    payload = generate_emvco_pix(amount, order_id)

    assert payload.startswith("000201"), "Payload must start with 000201"
    assert "br.gov.bcb.pix" in payload, "Payload must contain br.gov.bcb.pix"
    assert "5303986" in payload, "Payload must contain currency 986 (BRL)"
    assert "5406149.90" in payload, "Payload must contain formatted amount tag"
    assert "5802BR" in payload, "Payload must contain country tag 5802BR"
    assert "6304" in payload, "Payload must contain CRC tag 6304"

    # Verify CRC16 accuracy
    data_part = payload[:-4]
    expected_crc = _calculate_crc16(data_part)
    actual_crc = payload[-4:]
    assert actual_crc == expected_crc, f"CRC mismatch: expected {expected_crc}, got {actual_crc}"


@pytest.mark.asyncio
async def test_create_pix_payment_network_fallback(monkeypatch):
    """
    Verifies that when network fails or API raises an exception,
    create_pix_payment falls back cleanly to local EMVCo generation without throwing unhandled exceptions.
    """
    from backend.app.services import mercadopago_service

    async def mock_post(*args, **kwargs):
        raise httpx.ConnectError("Simulated network down")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    order_id = uuid.uuid4()
    result = await mercadopago_service.create_pix_payment(
        product_id=42,
        total_amount=Decimal("135.00"),
        customer_email="teste@offline.com",
        customer_name="Offline User",
        order_id=order_id,
    )

    assert "qr_code" in result and len(result["qr_code"]) > 0
    assert "qr_code_base64" in result and len(result["qr_code_base64"]) > 0
    assert result["status"] == "pending"
    assert result["payment_id"].startswith("mp_")

