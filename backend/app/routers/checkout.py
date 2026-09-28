"""
Checkout Router for Vintage Brechó API.
Implements:
- POST /api/checkout/pix: Transparent PIX checkout with atomic 10-minute lock (Mocked for testing).
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
except ImportError:
    from backend.app.config import settings
    from backend.app.database import get_db
    from backend.app.schemas import CheckoutResponse, OrderCreate, OrderStatusOut
    from backend.app.services.lock_service import acquire_product_lock, release_product_lock

router = APIRouter(tags=["checkout"])
logger = logging.getLogger("vintage_brecho.checkout")

# QR Code real de teste estilizado em Base64
MOCK_QR_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAPAAAADwCAYAAAA+VemSAAAACXBIWXMAAA7EAAAOxAGVKw4b"
    "AAAFoElEQVR4nO3dQY7bRhBF0a7A/W952wUCBJq0W31U/Z5zkhx084gkuqf+u30e57z8990F"
    "Pld/+wJ8vgReJ4HXSeB1EnidBF4ngddJ4HUSEPjrF/j+V/r5Enhd9v55nPO1C5x9f4D39U/g"
    "dRJ4nQReJ4HXSeB1EnidBF4ngdfJ3j+PczqB470T+D7/BF4ngddJ4HUSEHidBF4ngddJ4HUS"
    "eJ0EXieB10ngdQoI/P7/qfF/1ZfA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOtk75/HOZ3A8d4J"
    "fJ9/Aq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrFBD4/f9T4/+qL4HXiY/nBH5MAq+TwOsk"
    "8DoJvE4Cr5PA6yTwOgm8TvZ+eZx1/19wAu9d4Pvn/R8EXieB10ngdRJ4nQReJ4HXSeB1Enid"
    "BF4ngddp/t6PwPfxT+B1EnidBF4ngddJ4HUS+DkE/nI/7v3zOOdrb4HXSeB1EnidBF4ngddJ"
    "4HUS+DkJ/FwCr5PA6yTwOgm8TgKvk8DrJPA6CbxOAu+dwOsk8DoJvE4Cr5PA6yTwOgm8TgKv"
    "k8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4C"
    "r5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxO"
    "Aq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8"
    "TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJ"
    "vE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6"
    "CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTw"
    "Ogm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk"
    "8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8Dr"
    "JPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA"
    "6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+T"
    "wOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKv"
    "k8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4C"
    "r5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxO"
    "Aq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8"
    "TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJ"
    "vE4Cr5PA6yTwOgm8TgKvk8DrJPA6CbxOAq+TwOsk8DoJvE4Cr5PA6yTwOgm8TgKvk8Dr/ANw"
    "Cg9G2m15uAAAAABJRU5ErkJggg=="
)


@router.post("/checkout/pix", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
async def checkout_pix(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    """
    Inicia o checkout transparente com PIX simulado (Modo de Teste):
    1. Executa a trava atômica de 10 minutos na peça unitária.
    2. Adiciona a taxa fixa de frete de R$ 15,00.
    3. Mocka o retorno do PIX (Copia-e-Cola e QR Code).
    4. Registra o pedido na tabela orders no Supabase.
    """
    # 1. Acquire atomic 10-minute reservation lock
    product = await acquire_product_lock(db, payload.product_id)

    # 2. Shipping calculation
    product_price = Decimal(str(product["price"]))
    shipping_cost = Decimal(str(settings.FIXED_SHIPPING_PRICE))
    total_amount = product_price + shipping_cost

    # 3. MOCK DO MERCADO PAGO (Simulação segura para testes locais e em nuvem)
    order_id = uuid.uuid4()
    mercadopago_payment_id = f"mock_mp_{order_id.hex[:10]}"
    
    # Código Pix Copia-e-Cola simulado para testar o botão de cópia
    qr_code = (
        f"00020126580014br.gov.bcb.pix0136vintage-brecho-teste-pix520400005303986"
        f"540{float(total_amount):.2f}5802BR5914VINTAGE BRECHO6009SAO PAULO62070503***6304TEST"
    )
    qr_code_base64 = MOCK_QR_BASE64

    # 4. Gravação do pedido no banco de dados
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
        logger.error(f"Erro ao salvar pedido, liberando trava da peça: {exc}")
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