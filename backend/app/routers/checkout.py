"""
Checkout Router for Vintage Brechó API.
Implements:
- POST /api/checkout/pix: Transparent PIX checkout with atomic 10-minute lock (Mocked for testing).
- GET /api/orders/{order_id}/status: Polling order status for celebratory redirect.
"""

import base64
from decimal import Decimal
import logging
from typing import Optional
import urllib.parse
import urllib.request
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.config import settings
    from app.database import get_db
    from app.schemas import CheckoutResponse, OrderCreate, OrderStatusOut
    from app.services.lock_service import (
        acquire_product_lock,
        release_product_lock,
        acquire_products_batch_lock,
        release_products_batch_lock,
    )
except ImportError:
    from backend.app.config import settings
    from backend.app.database import get_db
    from backend.app.schemas import CheckoutResponse, OrderCreate, OrderStatusOut
    from backend.app.services.lock_service import (
        acquire_product_lock,
        release_product_lock,
        acquire_products_batch_lock,
        release_products_batch_lock,
    )

router = APIRouter(tags=["checkout"])
logger = logging.getLogger("vintage_brecho.checkout")


def gerar_qr_code_base64(conteudo_pix: str) -> str:
    """Busca a imagem do QR Code renderizada para o texto do PIX e converte para Base64."""
    try:
        dados_codificados = urllib.parse.quote(conteudo_pix)
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={dados_codificados}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            return base64.b64encode(response.read()).decode("utf-8")
    except Exception as exc:
        logger.warning(f"Aviso: Não foi possível obter QR Code da API externa ({exc}).")
        return ""


@router.post("/checkout/pix", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout_pix(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Inicia o checkout transparente com PIX simulado (Modo de Teste):
    1. Executa a trava atômica de 10 minutos nas peças unitárias enviadas (1 ou mais).
    2. Adiciona a taxa fixa de frete de R$ 15,00 uma única vez para o pacote.
    3. Gera o código Pix Copia-e-Cola e a imagem em Base64 para o valor total consolidado.
    4. Registra o pedido na tabela orders e os itens na tabela order_items no Supabase.
    """
    product_ids = payload.get_product_ids()
    if not product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma peça selecionada para o pedido."
        )

    # 1. Trava atômica de 10 minutos (unitária ou em lote)
    locked_products = await acquire_products_batch_lock(db, product_ids)

    # 2. Cálculo dos valores (soma de todas as peças + frete único de R$ 15)
    product_price = sum(Decimal(str(p["price"])) for p in locked_products)
    shipping_cost = Decimal(str(settings.FIXED_SHIPPING_PRICE))
    total_amount = product_price + shipping_cost

    # 3. Geração dos identificadores e dados do PIX mockado
    order_id = uuid.uuid4()
    mercadopago_payment_id = f"mock_mp_{order_id.hex[:10]}"

    qr_code = (
        f"00020126580014br.gov.bcb.pix0136vintage-brecho-teste-pix"
        f"520400005303986540{float(total_amount):.2f}5802BR5914VINTAGE BRECHO6009SAO PAULO62070503***6304TEST"
    )
    qr_code_base64 = gerar_qr_code_base64(qr_code)

    # 4. Gravação do pedido pai na tabela orders e filhos em order_items
    try:
        bind = db.bind
        is_sqlite = bind is not None and bind.dialect.name == "sqlite"
        primary_product_id = product_ids[0] if product_ids else None

        sql_order = text("""
            INSERT INTO orders (
                id, product_id, customer_name, customer_email, customer_phone,
                customer_address, shipping_cost, total_amount, mercadopago_payment_id, payment_status
            ) VALUES (
                :id, :product_id, :customer_name, :customer_email, :customer_phone,
                :customer_address, :shipping_cost, :total_amount, :mercadopago_payment_id, 'pending'
            );
        """)

        await db.execute(
            sql_order,
            {
                "id": str(order_id) if is_sqlite else order_id,
                "product_id": primary_product_id,
                "customer_name": payload.customer_name,
                "customer_email": payload.customer_email,
                "customer_phone": payload.customer_phone,
                "customer_address": payload.customer_address,
                "shipping_cost": float(shipping_cost),
                "total_amount": float(total_amount),
                "mercadopago_payment_id": str(mercadopago_payment_id),
            }
        )

        # Inserção dos registros filhos em order_items
        for p in locked_products:
            sql_item = text("""
                INSERT INTO order_items (order_id, product_id, price_at_purchase)
                VALUES (:order_id, :product_id, :price_at_purchase);
            """)
            await db.execute(
                sql_item,
                {
                    "order_id": str(order_id) if is_sqlite else order_id,
                    "product_id": p["id"],
                    "price_at_purchase": float(p["price"]),
                }
            )

        await db.commit()
    except Exception as exc:
        logger.error(f"Erro ao salvar pedido, liberando trava das peças: {exc}")
        await release_products_batch_lock(db, product_ids)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar pedido de compra."
        )

    return CheckoutResponse(
        order_id=str(order_id),
        product_id=primary_product_id,
        product_ids=product_ids,
        items_count=len(product_ids),
        products_count=len(product_ids),
        total_amount=total_amount,
        shipping_cost=shipping_cost,
        product_price=product_price,
        qr_code=qr_code,
        qr_code_base64=qr_code_base64,
        expires_in=600,
    )


@router.get("/orders/{order_id}/status", response_model=OrderStatusOut)
async def get_order_status(order_id: str, db: AsyncSession = Depends(get_db)):
    """
    Polling de status do pedido para transição em tempo real na interface do cliente.
    Suporta pedidos unitários e múltiplos itens.
    """
    bind = db.bind
    is_sqlite = bind is not None and bind.dialect.name == "sqlite"

    try:
        parsed_id = order_id if is_sqlite else uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ID de pedido inválido.")

    # 1. Consulta o pedido principal
    sql_order = text("""
        SELECT id, payment_status, product_id
        FROM orders
        WHERE id = :order_id;
    """)
    order_res = await db.execute(sql_order, {"order_id": parsed_id})
    order_row = order_res.mappings().first()

    if not order_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    # 2. Consulta itens associados em order_items
    sql_items = text("""
        SELECT oi.product_id, oi.product_id as id, oi.price_at_purchase, p.title as product_title, p.status as product_status
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = :order_id;
    """)
    items_res = await db.execute(sql_items, {"order_id": parsed_id})
    items = [dict(r) for r in items_res.mappings().all()]

    is_paid = order_row["payment_status"] == "approved"

    # Se há itens cadastrados em order_items
    if items:
        first_title = items[0].get("product_title")
        first_status = items[0].get("product_status")
        title_summary = first_title if len(items) == 1 else f"{first_title} (+{len(items)-1} peças)"
        return OrderStatusOut(
            order_id=str(order_row["id"]),
            payment_status=order_row["payment_status"],
            is_paid=is_paid,
            product_title=title_summary,
            product_status=first_status,
            items_count=len(items),
            items=items,
        )

    # Fallback para pedidos antigos diretos na coluna product_id
    if order_row.get("product_id"):
        prod_res = await db.execute(
            text("SELECT title, status FROM products WHERE id = :id"),
            {"id": order_row["product_id"]}
        )
        prod = prod_res.mappings().first()
        return OrderStatusOut(
            order_id=str(order_row["id"]),
            payment_status=order_row["payment_status"],
            is_paid=is_paid,
            product_title=prod["title"] if prod else None,
            product_status=prod["status"] if prod else None,
            items_count=1,
            items=[],
        )

    return OrderStatusOut(
        order_id=str(order_row["id"]),
        payment_status=order_row["payment_status"],
        is_paid=is_paid,
        product_title="Pacote Vintage",
        product_status=None,
        items_count=0,
        items=[],
    )