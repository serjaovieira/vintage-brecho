import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_multi_item_pix_checkout_creates_order_items(client: AsyncClient):
    """Valida checkout PIX com múltiplos itens (sacola) calculando frete único de R$ 15 e criando order_items."""
    # 1. Cadastra 2 produtos únicos
    p1_res = await client.post(
        "/api/products",
        json={
            "title": "Vestido Poá Vintage 1970",
            "category": "Vestidos",
            "description": "Vestido de bolinhas vintage",
            "size": "M",
            "price": 120.0,
            "image_url": "https://example.com/vestido.jpg",
        },
    )
    assert p1_res.status_code == 201
    p1 = p1_res.json()

    p2_res = await client.post(
        "/api/products",
        json={
            "title": "Bolsa Couro Legítimo Anos 80",
            "category": "Acessórios",
            "description": "Bolsa vintage conservada",
            "size": "Único",
            "price": 80.0,
            "image_url": "https://example.com/bolsa.jpg",
        },
    )
    assert p2_res.status_code == 201
    p2 = p2_res.json()

    # 2. Executa checkout multi-item
    checkout_res = await client.post(
        "/api/checkout/pix",
        json={
            "product_ids": [p1["id"], p2["id"]],
            "customer_name": "Maria Silva",
            "customer_email": "maria@example.com",
            "customer_phone": "17999998888",
            "customer_address": "Rua das Flores, 123 - Centro",
        },
    )
    assert checkout_res.status_code in (200, 201)
    checkout_data = checkout_res.json()

    # Validações financeiras e de payload
    assert checkout_data["items_count"] == 2
    # Preço total: 120 + 80 + 15 (frete fixo) = 215.00
    assert float(checkout_data["total_amount"]) == 215.0
    assert float(checkout_data["shipping_cost"]) == 15.0
    assert checkout_data["qr_code"] is not None
    assert checkout_data["qr_code_base64"] is not None

    order_id = checkout_data["order_id"]

    # 3. Consulta status do pedido e valida presença dos itens
    status_res = await client.get(f"/api/orders/{order_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["payment_status"] == "pending"
    assert len(status_data["items"]) == 2
    item_ids = [it["id"] for it in status_data["items"]]
    assert p1["id"] in item_ids
    assert p2["id"] in item_ids


@pytest.mark.asyncio
async def test_multi_item_conflict_when_one_product_is_locked(client: AsyncClient):
    """Garante que se uma peça do carrinho estiver travada ou vendida, retorna HTTP 409 e não trava as demais."""
    # 1. Cria 2 produtos
    p1_res = await client.post(
        "/api/products",
        json={
            "title": "Casaco Lã Batida Vintage",
            "category": "Casacos & Jaquetas",
            "description": "Casaco clássico",
            "size": "G",
            "price": 250.0,
            "image_url": "https://example.com/casaco.jpg",
        },
    )
    p1 = p1_res.json()

    p2_res = await client.post(
        "/api/products",
        json={
            "title": "Saia Midi Plissada Anos 60",
            "category": "Calças & Saias",
            "description": "Saia vintage impecável",
            "size": "P",
            "price": 95.0,
            "image_url": "https://example.com/saia.jpg",
        },
    )
    p2 = p2_res.json()

    # 2. Bloqueia a peça p1 ativamente via checkout direto
    lock_res = await client.post(
        "/api/checkout/pix",
        json={
            "product_id": p1["id"],
            "customer_name": "Cliente Um",
            "customer_email": "um@example.com",
            "customer_phone": "17999991111",
            "customer_address": "Rua Um, 1",
        },
    )
    assert lock_res.status_code in (200, 201)

    # 3. Tenta checkout multi-item com [p1, p2]
    checkout_res = await client.post(
        "/api/checkout/pix",
        json={
            "product_ids": [p1["id"], p2["id"]],
            "customer_name": "Ana Clara",
            "customer_email": "ana@example.com",
            "customer_phone": "17999997777",
            "customer_address": "Av Brasil, 456",
        },
    )
    assert checkout_res.status_code == 409
    detail = checkout_res.json()["detail"]
    assert "Casaco Lã Batida Vintage" in detail

    # 4. Confirma que a peça p2 NÃO ficou bloqueada e pode ser comprada
    p2_buy = await client.post(
        "/api/checkout/pix",
        json={
            "product_id": p2["id"],
            "customer_name": "Outro Cliente",
            "customer_email": "outro@example.com",
            "customer_phone": "17999992222",
            "customer_address": "Rua Dois, 2",
        },
    )
    assert p2_buy.status_code in (200, 201)


@pytest.mark.asyncio
async def test_delete_product_permanent(client: AsyncClient):
    """Valida o endpoint DELETE /api/products/{id} e exclusão permanente."""
    # 1. Cadastra peça para exclusão
    p_res = await client.post(
        "/api/products",
        json={
            "title": "Camisa Seda Vintage Rara",
            "category": "Blusas",
            "description": "Camisa estampada 100% seda",
            "size": "M",
            "price": 110.0,
            "image_url": "https://example.com/camisa.jpg",
        },
    )
    assert p_res.status_code == 201
    p_id = p_res.json()["id"]

    # 2. Exclui a peça
    del_res = await client.delete(f"/api/products/{p_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "success"
    assert del_data["id"] == p_id

    # 3. Confirma que a peça não é mais encontrada (404)
    get_res = await client.get(f"/api/products/{p_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_product_with_historical_order_sets_null_foreign_key(client: AsyncClient):
    """Garante que deletar uma peça associada a pedidos históricos não quebra foreign key e preserva o pedido."""
    # 1. Cadastra produto
    p_res = await client.post(
        "/api/products",
        json={
            "title": "Lenço Vintage Floral",
            "category": "Acessórios",
            "description": "Lenço anos 50",
            "size": "Único",
            "price": 45.0,
            "image_url": "https://example.com/lenco.jpg",
        },
    )
    p_id = p_res.json()["id"]

    # 2. Cria pedido com o produto
    checkout_res = await client.post(
        "/api/checkout/pix",
        json={
            "product_ids": [p_id],
            "customer_name": "Juliana Mendes",
            "customer_email": "juliana@example.com",
            "customer_phone": "17999996666",
            "customer_address": "Rua 15 de Novembro, 100",
        },
    )
    assert checkout_res.status_code in (200, 201)
    order_id = checkout_res.json()["order_id"]

    # 3. Deleta o produto permanentemente
    del_res = await client.delete(f"/api/products/{p_id}")
    assert del_res.status_code == 200

    # 4. Confirma que o produto foi deletado com sucesso
    get_res = await client.get(f"/api/products/{p_id}")
    assert get_res.status_code == 404

    # 5. Confirma que o histórico do pedido permanece acessível no endpoint
    order_status_res = await client.get(f"/api/orders/{order_id}/status")
    assert order_status_res.status_code == 200
    order_status = order_status_res.json()
    assert order_status["payment_status"] == "pending"
