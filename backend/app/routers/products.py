"""
Products Router for Vintage Brechó API.
Implements:
- GET /api/products: Vitrine showcase filtering out sold pieces and active locks.
- GET /api/categories: Dynamic category bar displaying only categories with active stock.
- GET /api/products/{id}: Product details modal.
- POST /api/products: Product registration for admin and test suites.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.database import get_db
    from app.schemas import ProductCreate, ProductDetailOut, ProductOut
except ImportError:
    from backend.app.database import get_db
    from backend.app.schemas import ProductCreate, ProductDetailOut, ProductOut

router = APIRouter(tags=["products"])


@router.get("/products", response_model=List[ProductOut])
async def list_products(
    category: Optional[str] = Query(None, description="Filtrar por categoria específica"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna apenas peças disponíveis ou com lock expirado (> 10 minutos).
    Peças vendidas ('sold') ou com lock ativo não são retornadas na vitrine pública.
    """
    bind = db.bind
    is_sqlite = bind is not None and bind.dialect.name == "sqlite"

    if is_sqlite:
        where_clause = "(status = 'available' OR (status = 'locked' AND locked_until < datetime('now')))"
    else:
        where_clause = "(status = 'available' OR (status = 'locked' AND locked_until < NOW()))"

    params = {}
    if category:
        where_clause += " AND category = :category"
        params["category"] = category

    sql = f"""
        SELECT id, title, category, description, size, price, image_url, status, locked_until, created_at
        FROM products
        WHERE {where_clause}
        ORDER BY created_at DESC, id DESC
    """

    result = await db.execute(text(sql), params)
    rows = result.mappings().all()

    # Normalize response: if lock is expired, present status as 'available'
    products = []
    for row in rows:
        item = dict(row)
        if item.get("status") == "locked":
            item["status"] = "available"
        products.append(item)

    return products


@router.get("/categories", response_model=List[str])
async def list_available_categories(db: AsyncSession = Depends(get_db)):
    """
    Retorna apenas categorias que possuem peças disponíveis no momento.
    Atualiza dinamicamente conforme novas categorias são cadastradas ou peças são vendidas.
    """
    bind = db.bind
    is_sqlite = bind is not None and bind.dialect.name == "sqlite"

    if is_sqlite:
        where_clause = "(status = 'available' OR (status = 'locked' AND locked_until < datetime('now')))"
    else:
        where_clause = "(status = 'available' OR (status = 'locked' AND locked_until < NOW()))"

    sql = f"""
        SELECT DISTINCT category
        FROM products
        WHERE {where_clause}
          AND category IS NOT NULL
          AND TRIM(category) != ''
        ORDER BY category ASC
    """

    result = await db.execute(text(sql))
    rows = result.fetchall()
    return [row[0] for row in rows]


@router.get("/products/{product_id}", response_model=ProductDetailOut)
async def get_product_detail(product_id: int, db: AsyncSession = Depends(get_db)):
    """Retorna detalhes completos da peça para exibição no modal de compra."""
    sql = text("""
        SELECT id, title, category, description, size, price, image_url, status, locked_until, created_at
        FROM products
        WHERE id = :id
    """)

    result = await db.execute(sql, {"id": product_id})
    row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado."
        )

    return dict(row)


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(product_in: ProductCreate, db: AsyncSession = Depends(get_db)):
    """
    Cadastra uma nova peça vintage unitária 1-of-1.
    Utilizado pelo painel admin e pelas fixtures de teste automatizadas.
    """
    bind = db.bind
    is_sqlite = bind is not None and bind.dialect.name == "sqlite"

    sql = text("""
        INSERT INTO products (title, category, description, size, price, image_url, status, locked_until)
        VALUES (:title, :category, :description, :size, :price, :image_url, :status, :locked_until)
        RETURNING id, title, category, description, size, price, image_url, status, locked_until, created_at;
    """)

    result = await db.execute(
        sql,
        {
            "title": product_in.title,
            "category": product_in.category,
            "description": product_in.description,
            "size": product_in.size,
            "price": float(product_in.price),
            "image_url": product_in.image_url,
            "status": product_in.status or "available",
            "locked_until": product_in.locked_until,
        }
    )
    new_product = result.mappings().first()
    await db.commit()
    return dict(new_product)
