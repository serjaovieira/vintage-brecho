"""
Atomic Lock Service for Vintage Brechó.
Implements the 10-minute temporary reservation lock on 1-of-1 pieces.
Guarantees strict concurrency protection, raising HTTP 409 Conflict when a piece is unavailable.
"""

from typing import Any, Dict
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def acquire_product_lock(db: AsyncSession, product_id: int) -> Dict[str, Any]:
    """
    Executa a trava atômica de 10 minutos em uma peça unitária 1-of-1.
    Garante que apenas uma transação obtenha a reserva da peça.
    Se a peça estiver indisponível (já vendida ou reservada), levanta HTTP 409 Conflict.
    """
    # Detect dialect for database-specific timestamp syntax
    bind = db.bind
    is_sqlite = bind is not None and bind.dialect.name == "sqlite"

    if is_sqlite:
        sql = """
            UPDATE products
            SET status = 'locked',
                locked_until = datetime('now', '+10 minutes')
            WHERE id = :id
              AND (
                  status = 'available'
                  OR (status = 'locked' AND locked_until < datetime('now'))
              )
            RETURNING id, title, category, description, size, price, image_url, status, locked_until;
        """
    else:
        sql = """
            UPDATE products
            SET status = 'locked',
                locked_until = NOW() + INTERVAL '10 minutes'
            WHERE id = :id
              AND (
                  status = 'available'
                  OR (status = 'locked' AND locked_until < NOW())
              )
            RETURNING id, title, category, description, size, price, image_url, status, locked_until;
        """

    result = await db.execute(text(sql), {"id": product_id})
    locked_item = result.mappings().first()

    if not locked_item:
        # Check current item state to provide precise HTTP error feedback
        check_stmt = text("SELECT id, status, locked_until FROM products WHERE id = :id")
        check_res = await db.execute(check_stmt, {"id": product_id})
        item = check_res.mappings().first()

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Produto não encontrado."
            )

        if item["status"] == "sold":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esta peça exclusiva já foi vendida."
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta peça exclusiva já está reservada por outro cliente."
        )

    await db.commit()
    return dict(locked_item)


async def release_product_lock(db: AsyncSession, product_id: int) -> None:
    """
    Libera a trava atômica em caso de falha de gateway ou cancelamento explícito.
    Reverte o status para 'available' e zera 'locked_until'.
    """
    sql = text("""
        UPDATE products
        SET status = 'available', locked_until = NULL
        WHERE id = :id AND status = 'locked'
    """)
    await db.execute(sql, {"id": product_id})
    await db.commit()
