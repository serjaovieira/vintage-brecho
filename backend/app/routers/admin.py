"""
Admin Router for Vintage Brechó API.
Provides endpoints for the shopkeeper mobile admin panel:
- GET /api/admin/orders: List dispatch and delivery orders.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.database import get_db
except ImportError:
    from backend.app.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/orders", response_model=List[Dict[str, Any]])
async def list_admin_orders(db: AsyncSession = Depends(get_db)):
    """
    Retorna os pedidos pagos para expedição e despacho com dados de envio e WhatsApp.
    Suporta pedidos unitários e multi-item, tratando com segurança peças deletadas.
    """
    sql = text("""
        SELECT 
            o.id as order_id,
            COALESCE(p.title, 'Peça histórica / arquivada') as product_title,
            COALESCE(p.price, o.total_amount - o.shipping_cost) as product_price,
            o.customer_name,
            o.customer_email,
            o.customer_phone,
            o.customer_address,
            o.total_amount,
            o.payment_status,
            o.created_at
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        ORDER BY o.created_at DESC;
    """)

    result = await db.execute(sql)
    rows = result.mappings().all()

    orders = []
    for r in rows:
        item = dict(r)
        order_uuid = str(item["order_id"])
        item["order_id"] = order_uuid

        # Consulta se há múltiplos itens nesta ordem
        items_res = await db.execute(
            text("""
                SELECT oi.product_id, oi.price_at_purchase, COALESCE(p.title, 'Item arquivado') as item_title
                FROM order_items oi
                LEFT JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = :oid
            """),
            {"oid": r["order_id"]}
        )
        sub_items = items_res.mappings().all()
        if len(sub_items) > 1:
            first_title = sub_items[0]["item_title"]
            item["product_title"] = f"{first_title} (+{len(sub_items)-1} peças no pacote)"
            item["items"] = [dict(si) for si in sub_items]
        elif len(sub_items) == 1:
            item["product_title"] = sub_items[0]["item_title"]
            item["items"] = [dict(si) for si in sub_items]
        else:
            item["items"] = []

        orders.append(item)

    return orders
