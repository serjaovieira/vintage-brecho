"""
Pytest configuration and shared fixtures for Vintage Brechó E2E tests.
Provides async HTTP client configured for either the live backend server or ASGI transport.
"""

import os
import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Any

import httpx
import pytest

BASE_URL = os.getenv("TEST_BASE_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))

_SERVER_CHECKED = False
_IS_LIVE_SERVER = False
_CAN_IMPORT_ASGI = False


async def _probe_environment():
    global _SERVER_CHECKED, _IS_LIVE_SERVER, _CAN_IMPORT_ASGI
    if _SERVER_CHECKED:
        return
    # Probe live HTTP server
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=0.5) as check_client:
            res = await check_client.get("/docs")
            if res.status_code in (200, 404):
                _IS_LIVE_SERVER = True
    except (httpx.HTTPError, OSError):
        _IS_LIVE_SERVER = False

    if not _IS_LIVE_SERVER:
        try:
            from backend.app.main import app  # noqa: F401
            _CAN_IMPORT_ASGI = True
        except ImportError:
            _CAN_IMPORT_ASGI = False

    _SERVER_CHECKED = True


@pytest.fixture(scope="session")
def server_base_url() -> str:
    return BASE_URL


@pytest.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Yields an AsyncClient connected to the running backend service,
    or falls back to ASGITransport if backend.app.main is available in-process.
    """
    await _probe_environment()

    if _IS_LIVE_SERVER:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as ac:
            yield ac
    elif _CAN_IMPORT_ASGI:
        from backend.app.main import app
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=15.0) as ac:
            yield ac
    else:
        pytest.fail(
            f"Backend service is not reachable at {BASE_URL} and 'backend.app.main:app' "
            f"cannot be imported. Please ensure the backend server is running on port 8000 "
            f"or the backend implementation is present."
        )


@pytest.fixture
def make_unique_id() -> Callable[[str], str]:
    """Helper to generate unique identifiers for test isolation."""
    def _gen(prefix: str = "item") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
    return _gen


@pytest.fixture
def create_product(client: httpx.AsyncClient) -> Callable[..., Any]:
    """
    Helper fixture to create an available product via POST /api/products
    and return the created product data dict including 'id'.
    """
    async def _create(**overrides) -> dict[str, Any]:
        uid = uuid.uuid4().hex[:6]
        payload = {
            "title": f"Peça Vintage Exclusiva {uid}",
            "category": f"Categoria_{uid}",
            "description": f"Peça única feminina vintage com medidas perfeitas {uid}",
            "size": "M",
            "price": 120.00,
            "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800",
        }
        payload.update(overrides)
        res = await client.post("/api/products", json=payload)
        if res.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to create test product: status={res.status_code}, response={res.text}"
            )
        return res.json()

    return _create


@pytest.fixture
def checkout_pix(client: httpx.AsyncClient) -> Callable[..., Any]:
    """
    Helper fixture to initiate PIX checkout on a product.
    """
    async def _checkout(product_id: int, **overrides) -> httpx.Response:
        uid = uuid.uuid4().hex[:6]
        payload = {
            "product_id": product_id,
            "customer_name": f"Cliente Vintage {uid}",
            "customer_email": f"cliente_{uid}@teste.com",
            "customer_phone": "17981668413",
            "customer_address": "Rua Vintage, 1970 - São Paulo, SP",
        }
        payload.update(overrides)
        return await client.post("/api/checkout/pix", json=payload)

    return _checkout


@pytest.fixture
def simulate_webhook(client: httpx.AsyncClient) -> Callable[..., Any]:
    """
    Helper fixture to simulate a Mercado Pago payment webhook notification.
    """
    async def _simulate(product_id: int, status: str = "approved") -> httpx.Response:
        payload = {
            "action": "payment.updated",
            "type": "payment",
            "data": {"id": f"mock_pay_{product_id}_{uuid.uuid4().hex[:6]}"},
            "mock_metadata": {
                "product_id": product_id,
                "status": status,
            },
        }
        return await client.post("/api/webhooks/mercadopago", json=payload)

    return _simulate
