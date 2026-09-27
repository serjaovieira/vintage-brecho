"""
E2E Dynamic Categories Test Suite for Vintage Brechó.
Verifies that GET /api/categories returns strictly categories with active, available stock,
reflects newly registered categories immediately, and prunes depleted/locked categories.
Requirements: R1, R2, Acceptance Criteria, PROJECT.md Interface Contract #2.
"""

import uuid
from collections.abc import Callable
from typing import Any

import httpx
import pytest


@pytest.mark.asyncio
async def test_get_categories_returns_list_of_strings(
    client: httpx.AsyncClient,
):
    """
    Contract 2:
    GET /api/categories must return 200 OK and an Array of strings.
    """
    res = await client.get("/api/categories")
    assert res.status_code == 200, f"Failed to get categories: {res.text}"
    categories = res.json()
    assert isinstance(categories, list), f"Expected list of categories, got: {type(categories)}"
    assert all(isinstance(c, str) for c in categories), "All items in categories must be strings"


@pytest.mark.asyncio
async def test_newly_registered_category_immediately_appears(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    R1 / Acceptance Criteria:
    When a new product is created with a new category, that category
    must immediately be reflected in GET /api/categories without server restart.
    """
    unique_cat = f"Brocados_{uuid.uuid4().hex[:6]}"

    # Verify not present initially
    res_before = await client.get("/api/categories")
    assert res_before.status_code == 200
    assert unique_cat not in res_before.json()

    # Register product with this category
    product = await create_product(
        title="Colete Bordado com Brocados",
        category=unique_cat,
        price=135.00,
    )
    assert product["category"] == unique_cat

    # Verify immediately available in categories
    res_after = await client.get("/api/categories")
    assert res_after.status_code == 200
    categories_after = res_after.json()
    assert unique_cat in categories_after, (
        f"Newly registered category '{unique_cat}' must appear in GET /api/categories. "
        f"Received: {categories_after}"
    )


@pytest.mark.asyncio
async def test_category_pruned_when_sole_item_is_sold(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
    simulate_webhook: Callable[..., Any],
):
    """
    R1 / R2:
    Only categories containing currently available pieces should be returned.
    When the last/sole item in a category transitions to 'sold', the category must disappear.
    """
    unique_cat = f"Kimonos_{uuid.uuid4().hex[:6]}"

    # 1. Create sole product in this category
    product = await create_product(
        title="Kimono Seda Estampado Anos 70",
        category=unique_cat,
        price=175.00,
    )
    product_id = product["id"]

    # Verify category is listed
    res_1 = await client.get("/api/categories")
    assert unique_cat in res_1.json(), "Category should be present while product is available"

    # 2. Checkout and approve payment (transition to 'sold')
    checkout_res = await checkout_pix(product_id=product_id)
    assert checkout_res.status_code in (200, 201)

    webhook_res = await simulate_webhook(product_id=product_id, status="approved")
    assert webhook_res.status_code == 200

    # 3. Category must no longer be returned
    res_2 = await client.get("/api/categories")
    assert res_2.status_code == 200
    categories_after = res_2.json()
    assert unique_cat not in categories_after, (
        f"Category '{unique_cat}' had its only item sold, so it must NOT appear in GET /api/categories. "
        f"Received: {categories_after}"
    )


@pytest.mark.asyncio
async def test_category_temporarily_excluded_when_all_items_locked(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
    checkout_pix: Callable[..., Any],
):
    """
    R1 / R2:
    If all items in a category are actively locked, that category has 0 available pieces
    and must not be presented to shoppers in GET /api/categories.
    """
    unique_cat = f"Chapeus_{uuid.uuid4().hex[:6]}"

    product = await create_product(
        title="Chapéu Feltro Vintage Fedora",
        category=unique_cat,
        price=85.00,
    )
    product_id = product["id"]

    # Verify present before lock
    res1 = await client.get("/api/categories")
    assert unique_cat in res1.json()

    # Lock product
    lock_res = await checkout_pix(product_id=product_id)
    assert lock_res.status_code in (200, 201)

    # Category must not be listed while its only product is locked
    res2 = await client.get("/api/categories")
    assert unique_cat not in res2.json(), (
        f"Category '{unique_cat}' whose only product is locked must not appear in GET /api/categories"
    )


@pytest.mark.asyncio
async def test_categories_deduplicated_for_multiple_products(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    If multiple available products share the same category, the category must appear
    exactly ONCE in the GET /api/categories response (no duplicates).
    """
    unique_cat = f"SaiasMidi_{uuid.uuid4().hex[:6]}"

    await create_product(title="Saia Midi Plissada Bege", category=unique_cat, price=80.0)
    await create_product(title="Saia Midi Godê Floral", category=unique_cat, price=90.0)
    await create_product(title="Saia Midi Jeans Retrô", category=unique_cat, price=95.0)

    res = await client.get("/api/categories")
    assert res.status_code == 200
    categories = res.json()

    occurrences = [c for c in categories if c == unique_cat]
    assert len(occurrences) == 1, (
        f"Expected category '{unique_cat}' to appear exactly once, but appeared {len(occurrences)} times."
    )


@pytest.mark.asyncio
async def test_filter_products_by_category(
    client: httpx.AsyncClient,
    create_product: Callable[..., Any],
):
    """
    GET /api/products?category={category} returns only items belonging to that category.
    """
    cat_target = f"Blazers_{uuid.uuid4().hex[:6]}"
    cat_other = f"Cintos_{uuid.uuid4().hex[:6]}"

    p_target = await create_product(title="Blazer Alfaiataria Risca de Giz", category=cat_target, price=150.0)
    p_other = await create_product(title="Cinto Couro Fivela Dourada", category=cat_other, price=45.0)

    res = await client.get(f"/api/products?category={cat_target}")
    assert res.status_code == 200
    items = res.json()

    item_ids = [item["id"] for item in items]
    assert p_target["id"] in item_ids, "Target item must be present in category filtered query"
    assert p_other["id"] not in item_ids, "Other category item must not appear in target category filter"
