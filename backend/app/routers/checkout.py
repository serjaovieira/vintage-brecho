"""
Checkout Router for Vintage Brechó API.
Implements:
- POST /api/checkout/pix: Transparent PIX checkout with atomic 10-minute lock.
- GET /api/orders/{order_id}/status: Polling order status for celebratory redirect.
"""

from decimal import Decimal
import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.config import settings
    from app.database import get_db
    from app.schemas import CheckoutResponse, OrderCreate, OrderStatusOut
    from app.services.lock_service import acquire_product_lock, release_product_lock
    from app.services.mercadopago_service import create_pix_payment
except ImportError:
    from backend.app.config import settings
    from backend.app.database import get_db
    from backend.app.schemas import CheckoutResponse, OrderCreate, OrderStatusOut
    from backend.app.services.lock_service import acquire_product_lock, release_product_lock
    from backend.app.services.mercadopago_service import create_pix_payment

router = APIRouter(tags=["checkout"])
logger = logging.getLogger("vintage_brecho.checkout")


@router.post("/checkout/pix", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout_pix(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Inicia o checkout transparente com PIX:
    1. Executa a trava atômica de 10 minutos na peça unitária (ou levanta HTTP 409 Conflict).
    2. Adiciona a taxa fixa de frete de R$ 15,00.
    3. Chama o serviço Mercado Pago para criar pagamento PIX com X-Idempotency-Key e metadata.
    4. Registra o pedido na tabela orders com o ID de pagamento gerado.
    5. Retorna o código PIX Copia-e-Cola, QR Code base64 e tempo de expiração de 10 minutos.
    """
    # 1. Acquire atomic 10-minute reservation lock
    product = await acquire_product_lock(db, payload.product_id)

    # 2. Shipping calculation
    product_price = Decimal(str(product["price"]))
    shipping_cost = Decimal(str(settings.FIXED_SHIPPING_PRICE))
    total_amount = product_price + shipping_cost

    # 3. Create order ID and generate PIX via Mercado Pago service
    order_id = uuid.uuid4()
    payment_info = await create_pix_payment(
        product_id=payload.product_id,
        total_amount=total_amount,
        customer_email=payload.customer_email,
        customer_name=payload.customer_name or "Cliente Vintage",
        order_id=order_id,
    )
    qr_code = payment_info["qr_code"]
    qr_code_base64 = payment_info["qr_code_base64"]
    mercadopago_payment_id = payment_info.get("payment_id") or f"mp_{order_id.hex[:12]}"

    try:
        bind = db.bind
        is_sqlite = bind is not None and bind.dialect.name == "sqlite"

        sql = text("""
            INSERT INTO orders (
                id, product_id, customer_name, customer_email, customer_phone,
                customer_address, shipping_cost, total_amount, mercadopago_payment_id, payment_status
            ) VALUES (
                :id, :product_id, :customer_name, :customer_email, :customer_phone,
                :customer_address, :shipping_cost, :total_amount, :mercadopago_payment_id, 'pending'
            );
        """)

        await db.execute(
            sql,
            {
                "id": str(order_id) if is_sqlite else order_id,
                "product_id": payload.product_id,
                "customer_name": payload.customer_name,
                "customer_email": payload.customer_email,
                "customer_phone": payload.customer_phone,
                "customer_address": payload.customer_address,
                "shipping_cost": float(shipping_cost),
                "total_amount": float(total_amount),
                "mercadopago_payment_id": str(mercadopago_payment_id),
            }
        )
        await db.commit()
    except Exception as exc:
        logger.error(f"Erro ao salvar pedido, liberando trava: {exc}")
        await release_product_lock(db, payload.product_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar pedido de compra."
        )

    return CheckoutResponse(
        order_id=str(order_id),
        product_id=payload.product_id,
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
    """
    bind = db.bind
    is_sqlite = bind is not None and bind.dialect.name == "sqlite"

    try:
        parsed_id = order_id if is_sqlite else uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ID de pedido inválido.")

    sql = text("""
        SELECT o.id, o.payment_status, p.title as product_title, p.status as product_status
        FROM orders o
        JOIN products p ON o.product_id = p.id
        WHERE o.id = :order_id;
    """)

    result = await db.execute(sql, {"order_id": parsed_id})
    row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    is_paid = row["payment_status"] == "approved"
    return OrderStatusOut(
        order_id=str(row["id"]),
        payment_status=row["payment_status"],
        is_paid=is_paid,
        product_title=row["product_title"],
        product_status=row["product_status"],
    )
