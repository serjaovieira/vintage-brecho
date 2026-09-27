"""
Webhooks Router for Vintage Brechó API.
Handles Mercado Pago payment notifications and simulated mock webhooks for QA/testing.
Atomically marks product as 'sold' and order as 'approved'.
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.database import get_db
    from app.services.mercadopago_service import get_payment
except ImportError:
    from backend.app.database import get_db
    from backend.app.services.mercadopago_service import get_payment

router = APIRouter(tags=["webhooks"])
logger = logging.getLogger("vintage_brecho.webhooks")


@router.post("/webhooks/mercadopago", status_code=status.HTTP_200_OK)
async def mercadopago_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Recebe notificação de pagamento do Mercado Pago ou evento simulado via mock_metadata.
    Ao aprovar o pagamento:
    1. Consulta a autenticidade e status na API oficial do Mercado Pago quando recebido payment_id real.
    2. Transiciona atomicamente a peça unitária para status='sold'.
    3. Atualiza o status do pedido para 'approved'.
    4. Remove definitivamente a peça da vitrine pública.
    Mantém compatibilidade integral com `mock_metadata` para testes e devtools MCP.
    """
    try:
        body: Dict[str, Any] = await request.json()
    except Exception:
        body = {}

    # 1. Suporte prioritário para simulações de QA e Devtools MCP (sem cobrança real)
    mock_metadata = body.get("mock_metadata")
    if mock_metadata and "product_id" in mock_metadata:
        product_id = mock_metadata["product_id"]
        payment_status = mock_metadata.get("status", "approved")

        if payment_status == "approved":
            # Atualiza produto para vendido atomicamente
            await db.execute(
                text("UPDATE products SET status = 'sold', locked_until = NULL WHERE id = :id"),
                {"id": product_id}
            )
            # Atualiza pedidos correspondentes para aprovado
            await db.execute(
                text("UPDATE orders SET payment_status = 'approved' WHERE product_id = :id"),
                {"id": product_id}
            )
            await db.commit()
            logger.info(f"[Webhook Mock] Produto {product_id} atualizado para 'sold' e pedido para 'approved'.")

        return {"status": "ok", "product_id": product_id, "payment_status": payment_status}

    # 2. Notificação oficial Mercado Pago (Webhook JSON ou IPN query params)
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    payment_id = (
        data.get("id")
        or body.get("id")
        or request.query_params.get("data.id")
        or request.query_params.get("id")
    )

    if payment_id:
        logger.info(f"[Webhook MP] Notificação recebida para payment_id={payment_id}")

        # Consulta API do Mercado Pago para verificar status oficial
        mp_payment = await get_payment(payment_id)

        if mp_payment:
            mp_status = mp_payment.get("status")
            metadata = mp_payment.get("metadata") or {}
            mp_product_id = metadata.get("product_id")
            mp_order_id = metadata.get("order_id")

            logger.info(
                f"[Webhook MP] API retornou status={mp_status}, metadata={metadata} para payment_id={payment_id}"
            )

            if mp_status == "approved":
                if mp_product_id:
                    await db.execute(
                        text("UPDATE products SET status = 'sold', locked_until = NULL WHERE id = :id"),
                        {"id": int(mp_product_id)}
                    )

                if mp_order_id:
                    bind = db.bind
                    is_sqlite = bind is not None and bind.dialect.name == "sqlite"
                    await db.execute(
                        text(
                            "UPDATE orders SET payment_status = 'approved', mercadopago_payment_id = :mp_id "
                            "WHERE id = :order_id"
                        ),
                        {
                            "mp_id": str(payment_id),
                            "order_id": str(mp_order_id) if is_sqlite else mp_order_id,
                        }
                    )
                elif mp_product_id:
                    await db.execute(
                        text(
                            "UPDATE orders SET payment_status = 'approved', mercadopago_payment_id = :mp_id "
                            "WHERE product_id = :p_id"
                        ),
                        {"mp_id": str(payment_id), "p_id": int(mp_product_id)}
                    )

                await db.commit()
                logger.info(
                    f"[Webhook MP] Pagamento {payment_id} aprovado para produto {mp_product_id}. Pedido atualizado."
                )
                return {"status": "ok", "payment_id": str(payment_id), "payment_status": "approved"}

            elif mp_status in ("cancelled", "rejected"):
                if mp_product_id:
                    # Libera a peça de volta para a vitrine caso o pagamento tenha sido cancelado/recusado
                    await db.execute(
                        text(
                            "UPDATE products SET status = 'available', locked_until = NULL "
                            "WHERE id = :id AND status = 'locked'"
                        ),
                        {"id": int(mp_product_id)}
                    )
                if mp_order_id:
                    bind = db.bind
                    is_sqlite = bind is not None and bind.dialect.name == "sqlite"
                    await db.execute(
                        text("UPDATE orders SET payment_status = :status WHERE id = :order_id"),
                        {
                            "status": mp_status,
                            "order_id": str(mp_order_id) if is_sqlite else mp_order_id,
                        }
                    )
                await db.commit()
                logger.info(f"[Webhook MP] Pagamento {payment_id} com status={mp_status}. Trava liberada se pendente.")
                return {"status": "ok", "payment_id": str(payment_id), "payment_status": mp_status}

        # Fallback para ambientes de teste / offline onde o mercadopago_payment_id foi gravado no banco
        order_res = await db.execute(
            text("SELECT product_id, id FROM orders WHERE mercadopago_payment_id = :mp_id"),
            {"mp_id": str(payment_id)}
        )
        order_row = order_res.mappings().first()
        if order_row:
            p_id = order_row["product_id"]
            await db.execute(
                text("UPDATE products SET status = 'sold', locked_until = NULL WHERE id = :id"),
                {"id": p_id}
            )
            await db.execute(
                text("UPDATE orders SET payment_status = 'approved' WHERE mercadopago_payment_id = :mp_id"),
                {"mp_id": str(payment_id)}
            )
            await db.commit()
            logger.info(f"[Webhook Local Fallback] Pagamento {payment_id} aprovado para produto {p_id}.")
            return {"status": "ok", "product_id": p_id, "payment_status": "approved"}

    return {"status": "ok"}
