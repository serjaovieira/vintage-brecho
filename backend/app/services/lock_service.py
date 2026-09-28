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


async def acquire_products_batch_lock(db: AsyncSession, product_ids: list[int]) -> list[Dict[str, Any]]:
    """
    Executa a trava atômica de 10 minutos em uma lista de peças unitárias 1-of-1:
    1. Verifica se todos os IDs enviados existem e se estão com status 'available' (ou lock expirado).
    2. Se QUALQUER peça já estiver reservada ('locked') ou vendida ('sold'), retorna HTTP 409
       informando o título da peça indisponível.
    3. Se todas estiverem livres, executa a trava atômica de 10 minutos em todas em uma única transação.
    """
    if not product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma peça selecionada para o checkout."
        )

    # Caso unitário, delega diretamente para a função otimizada
    if len(product_ids) == 1:
        single = await acquire_product_lock(db, product_ids[0])
        return [single]

    bind = db.bind
    is_sqlite = bind is not None and bind.dialect.name == "sqlite"

    # 1. Consulta o estado atual de todas as peças
    placeholders = ", ".join(f":id_{i}" for i in range(len(product_ids)))
    params = {f"id_{i}": pid for i, pid in enumerate(product_ids)}

    query_sql = f"""
        SELECT id, title, price, status, locked_until
        FROM products
        WHERE id IN ({placeholders});
    """
    res = await db.execute(text(query_sql), params)
    found_items = {row["id"]: dict(row) for row in res.mappings().all()}

    # Verifica se algum produto não foi encontrado
    for pid in product_ids:
        if pid not in found_items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Peça com ID {pid} não encontrada no catálogo."
            )

    # 2. Verifica disponibilidade de cada peça
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)

    for pid in product_ids:
        item = found_items[pid]
        st = item.get("status")
        l_until = item.get("locked_until")

        if st == "sold":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A peça '{item['title']}' já foi vendida e não está disponível."
            )

        if st == "locked" and l_until:
            if isinstance(l_until, str):
                try:
                    l_until = datetime.fromisoformat(l_until)
                except ValueError:
                    l_until = datetime.strptime(l_until[:19], "%Y-%m-%d %H:%M:%S")
            lock_time = l_until if getattr(l_until, "tzinfo", None) else l_until.replace(tzinfo=timezone.utc)
            if lock_time >= now_utc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A peça '{item['title']}' já está reservada por outro cliente."
                )

    # 3. Executa a trava atômica em lote em todas as peças simultaneamente
    if is_sqlite:
        update_sql = f"""
            UPDATE products
            SET status = 'locked',
                locked_until = datetime('now', '+10 minutes')
            WHERE id IN ({placeholders})
              AND (
                  status = 'available'
                  OR (status = 'locked' AND locked_until < datetime('now'))
              )
            RETURNING id, title, category, description, size, price, image_url, status, locked_until;
        """
    else:
        update_sql = f"""
            UPDATE products
            SET status = 'locked',
                locked_until = NOW() + INTERVAL '10 minutes'
            WHERE id IN ({placeholders})
              AND (
                  status = 'available'
                  OR (status = 'locked' AND locked_until < NOW())
              )
            RETURNING id, title, category, description, size, price, image_url, status, locked_until;
        """

    update_res = await db.execute(text(update_sql), params)
    locked_items = update_res.mappings().all()

    # Se alguma peça falhou na trava atômica (race condition entre o check e o update)
    if len(locked_items) != len(product_ids):
        # Desfaz e libera
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uma ou mais peças do seu pedido acabaram de ser reservadas por outro cliente."
        )

    await db.commit()
    return [dict(item) for item in locked_items]


async def release_products_batch_lock(db: AsyncSession, product_ids: list[int]) -> None:
    """Libera a trava atômica para um lote de peças."""
    if not product_ids:
        return
    placeholders = ", ".join(f":id_{i}" for i in range(len(product_ids)))
    params = {f"id_{i}": pid for i, pid in enumerate(product_ids)}
    sql = f"""
        UPDATE products
        SET status = 'available', locked_until = NULL
        WHERE id IN ({placeholders}) AND status = 'locked'
    """
    await db.execute(text(sql), params)
    await db.commit()
