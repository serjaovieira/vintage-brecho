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
    """
    sql = text("""
        SELECT 
            o.id as order_id,
            p.title as product_title,
            p.price as product_price,
            o.customer_name,
            o.customer_email,
            o.customer_phone,
            o.customer_address,
            o.total_amount,
            o.payment_status,
            o.created_at
        FROM orders o
        JOIN products p ON o.product_id = p.id
        ORDER BY o.created_at DESC;
    """)

    result = await db.execute(sql)
    rows = result.mappings().all()

    orders = []
    for r in rows:
        item = dict(r)
        item["order_id"] = str(item["order_id"])
        orders.append(item)

    return orders
