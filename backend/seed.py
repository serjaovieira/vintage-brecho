"""
Initial Catalog Seed Script for Vintage Brechó
Populates authentic 1-of-1 vintage feminine fashion pieces across 6 core categories:
- Vestidos
- Casacos
- Saias
- Alfaiataria
- Tricô
- Blusas Vintage

Can be run directly via CLI:
    python backend/seed.py
    python backend/seed.py --reset
"""

import argparse
import os
import sys
from decimal import Decimal
from typing import Any, Dict, List
import dotenv

dotenv.load_dotenv()

# Sample Authentic Vintage Feminine Clothing Catalog
VINTAGE_CATALOG: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # 1. VESTIDOS
    # -------------------------------------------------------------------------
    {
        "title": "Vestido Midi Floral Romântico Anos 70",
        "category": "Vestidos",
        "size": "M",
        "price": Decimal("149.90"),
        "description": "Peça autêntica dos anos 70 em viscose encorpada com toque de algodão. Estampa floral miúda em tons terrosos e fundo cru. Decote em V com delicados botões de madeira, mangas fluidas 3/4 e cintura marcada com elástico embutido. Medidas: Busto 92cm, Cintura 72-82cm, Quadril 108cm, Comprimento 118cm. Condição: Impecável 10/10, sem desgastes.",
        "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&auto=format&fit=crop",
        "status": "available",
    },
    {
        "title": "Vestido Evasê Poá Vintage Clássico",
        "category": "Vestidos",
        "size": "P",
        "price": Decimal("135.00"),
        "description": "Vestido vintage corte evasê clássico com estampa poá off-white sobre fundo terracota suave. Tecido crepe vintage de caimento impecável com gola boneca estruturada e zíper invisível nas costas. Medidas: Busto 86cm, Cintura 68cm, Quadril livre, Comprimento 102cm. Condição: Excelente estado de conservação, peça de acervo.",
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&auto=format&fit=crop",
        "status": "available",
    },

    # -------------------------------------------------------------------------
    # 2. CASACOS
    # -------------------------------------------------------------------------
    {
        "title": "Trench Coat Clássico Heritage Vintage",
        "category": "Casacos",
        "size": "G",
        "price": Decimal("229.00"),
        "description": "Sobretudo trench coat vintage estruturado em sarja peletizada de algodão puro. Abotoamento duplo clássico com botões estilo tartaruga, dragonas nos ombros e cinto original com fivela forrada. Forro interno acetinado xadrez suave. Medidas: Ombro a ombro 44cm, Busto 104cm, Manga 60cm, Comprimento 95cm. Condição: Peça rara e perfeita.",
        "image_url": "https://images.unsplash.com/photo-1544441893-675973e31985?w=800&auto=format&fit=crop",
        "status": "available",
    },
    {
        "title": "Casaco Lã Batida Verde Sage Anos 80",
        "category": "Casacos",
        "size": "M",
        "price": Decimal("189.00"),
        "description": "Casaco alongado vintage em lã batida verde sálvia com caimento desestruturado elegante. Bolsos frontais embutidos e fechamento por botão único em madeira entalhada. Peça quente e sofisticada. Medidas: Busto 100cm, Ombro 42cm, Manga 58cm, Comprimento 82cm. Condição: Impecável, lã higienizada e preservada.",
        "image_url": "https://images.unsplash.com/photo-1539533018447-63fcce667883?w=800&auto=format&fit=crop",
        "status": "available",
    },

    # -------------------------------------------------------------------------
    # 3. SAIAS
    # -------------------------------------------------------------------------
    {
        "title": "Saia Midi Plissada Acetinada Terracota",
        "category": "Saias",
        "size": "M",
        "price": Decimal("98.00"),
        "description": "Saia midi com plissado fino permanente em tom terracota vintage com brilho acetinado suave. Cós com elástico largo interno que se ajusta confortavelmente à silhueta feminina. Movimento fluido e elegante. Medidas: Cintura 70-80cm, Quadril livre, Comprimento 78cm. Condição: Estado de nova, sem fios puxados.",
        "image_url": "https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?w=800&auto=format&fit=crop",
        "status": "available",
    },
    {
        "title": "Saia Botões Frontais em Linho Puro",
        "category": "Saias",
        "size": "38",
        "price": Decimal("110.00"),
        "description": "Saia evasê vintage 100% linho rústico cru com fileira completa de botões frontais em madrepérola natural. Bolsos laterais faca funcionais e passantes para cinto fino. Medidas: Cintura 72cm, Quadril 98cm, Comprimento 72cm. Condição: Excelente, fibra natural nobre impecável.",
        "image_url": "https://images.unsplash.com/photo-1551803091-e20673f15770?w=800&auto=format&fit=crop",
        "status": "available",
    },

    # -------------------------------------------------------------------------
    # 4. ALFAIATARIA
    # -------------------------------------------------------------------------
    {
        "title": "Calça Alfaiataria Pregas CGC Anos 90",
        "category": "Alfaiataria",
        "size": "40",
        "price": Decimal("125.00"),
        "description": "Calça de alfaiataria feminina vintage autêntica com etiqueta CGC original. Modelagem cenoura com cintura alta marcada, duas pregas frontais clássicas, bolsos faca e barra italiana dobrada. Tecido misto de lã fria e viscose encorpada. Medidas: Cintura 76cm, Gancho 34cm, Quadril 104cm, Comprimento 102cm. Condição: Impecável de colecionador.",
        "image_url": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=800&auto=format&fit=crop",
        "status": "available",
    },
    {
        "title": "Blazer Oversized Alfaiataria Espinha de Peixe",
        "category": "Alfaiataria",
        "size": "G",
        "price": Decimal("195.00"),
        "description": "Blazer clássico corte alfaiataria masculina adaptado para mulher, padronagem espinha de peixe em tons de areia e castanho. Ombreiras vintage sutis e estruturadas, bolsos com lapela e forro acetinado completo. Medidas: Ombro a ombro 45cm, Busto 106cm, Manga 61cm, Comprimento 76cm. Condição: Estado impecável 10/10.",
        "image_url": "https://images.unsplash.com/photo-1584273143981-41c073dfe8f8?w=800&auto=format&fit=crop",
        "status": "available",
    },

    # -------------------------------------------------------------------------
    # 5. TRICÔ
    # -------------------------------------------------------------------------
    {
        "title": "Suéter Tricô Terracota Ponto Pipoca",
        "category": "Tricô",
        "size": "G",
        "price": Decimal("119.00"),
        "description": "Suéter artesanal em tricô ponto pipoca volumoso, cor terracota quente. Gola redonda canelada, punhos e barra ajustados. Fio aconchegante e macio, caimento soltinho e acolhedor para dias amenos. Medidas: Busto 104cm, Ombro caído, Manga 56cm, Comprimento 62cm. Condição: Excelente, sem bolinhas nem deformações.",
        "image_url": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800&auto=format&fit=crop",
        "status": "available",
    },
    {
        "title": "Cardigã Vintage Sage Bordado Floral",
        "category": "Tricô",
        "size": "M",
        "price": Decimal("139.00"),
        "description": "Cardigã vintage em malha de tricô verde sálvia com delicados bordados manuais de florzinhas silvestres nos ombros e decote. Botões perolados originais de época e acabamento scallop rendado nas bordas. Medidas: Busto 96cm, Ombro 40cm, Manga 57cm, Comprimento 58cm. Condição: Relíquia vintage em perfeito estado.",
        "image_url": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=800&auto=format&fit=crop",
        "status": "available",
    },

    # -------------------------------------------------------------------------
    # 6. BLUSAS VINTAGE
    # -------------------------------------------------------------------------
    {
        "title": "Camisa de Seda Pura Pesponto Artesanal",
        "category": "Blusas Vintage",
        "size": "P",
        "price": Decimal("115.00"),
        "description": "Camisa feminina clássica em 100% seda pura na cor marfim / creme suave. Caimento fluido extraordinário com colarinho estruturado, vista oculta de botões e pesponto delicado feito à mão. Medidas: Busto 90cm, Ombro 39cm, Manga 58cm, Comprimento 64cm. Condição: Seda impecável, sem manchas ou puídos.",
        "image_url": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&auto=format&fit=crop",
        "status": "available",
    },
    {
        "title": "Blusa Romântica Gola Laço Anos 80",
        "category": "Blusas Vintage",
        "size": "M",
        "price": Decimal("89.00"),
        "description": "Blusa vintage anos 80 com charmosa gola laço (pussy-bow) que pode ser usada com amarração frontal ou solta. Tecido crepe georgette levemente translúcido, punhos com mini botões forrados. Estampa geométrica retrô sutil. Medidas: Busto 98cm, Ombro 40cm, Manga 60cm, Comprimento 60cm. Condição: Perfeita, conservada em acervo.",
        "image_url": "https://images.unsplash.com/photo-1564257631407-4deb1f99d992?w=800&auto=format&fit=crop",
        "status": "available",
    },
]


def seed_via_psycopg(db_url: str, reset: bool = False) -> int:
    """Synchronous seed using psycopg[binary] against PostgreSQL."""
    import psycopg

    print(f"[*] Conectando via psycopg ao PostgreSQL...")
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Ensure products table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    description TEXT,
                    size VARCHAR(20) NOT NULL,
                    price NUMERIC(10, 2) NOT NULL,
                    image_url TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'available',
                    locked_until TIMESTAMP WITH TIME ZONE NULL,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
                );
            """)

            if reset:
                print("[-] Limpando tabela products existentes (--reset ativado)...")
                cur.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE;")

            inserted = 0
            for item in VINTAGE_CATALOG:
                # Check for existing product with same title
                cur.execute("SELECT id FROM products WHERE title = %s LIMIT 1", (item["title"],))
                if cur.fetchone():
                    print(f"    [~] Peça '{item['title']}' já existe. Pulando...")
                    continue

                cur.execute(
                    """
                    INSERT INTO products (title, category, description, size, price, image_url, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        item["title"],
                        item["category"],
                        item["description"],
                        item["size"],
                        item["price"],
                        item["image_url"],
                        item["status"],
                    ),
                )
                inserted += 1

            conn.commit()
            print(f"[+] Concluído com sucesso! {inserted} novas peças inseridas no PostgreSQL.")
            return inserted


def seed_via_sqlite(db_path: str, reset: bool = False) -> int:
    """Fallback synchronous seed using sqlite3 for local offline testing."""
    import sqlite3

    print(f"[*] Conectando ao SQLite local: {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            size TEXT NOT NULL,
            price REAL NOT NULL,
            image_url TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            locked_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    if reset:
        print("[-] Limpando tabela products no SQLite (--reset ativado)...")
        cur.execute("DELETE FROM products;")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='products';")

    inserted = 0
    for item in VINTAGE_CATALOG:
        cur.execute("SELECT id FROM products WHERE title = ? LIMIT 1", (item["title"],))
        if cur.fetchone():
            print(f"    [~] Peça '{item['title']}' já existe. Pulando...")
            continue

        cur.execute(
            """
            INSERT INTO products (title, category, description, size, price, image_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["title"],
                item["category"],
                item["description"],
                item["size"],
                float(item["price"]),
                item["image_url"],
                item["status"],
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"[+] Concluído com sucesso! {inserted} novas peças inseridas no SQLite.")
    return inserted


def run_seed(reset: bool = False) -> int:
    """Determines target database from DATABASE_URL and executes seed."""
    db_url = os.getenv("DATABASE_URL")
    if db_url and ("postgresql" in db_url or "postgres" in db_url):
        clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        try:
            return seed_via_psycopg(clean_url, reset=reset)
        except Exception as e:
            print(f"[!] Erro ao conectar ao PostgreSQL ({e}). Tentando fallback SQLite...")

    db_path = os.getenv("BRECHO_DB_PATH", "brecho.db")
    return seed_via_sqlite(db_path, reset=reset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed do catálogo Vintage Brechó")
    parser.add_argument("--reset", action="store_true", help="Remove produtos existentes antes de popular")
    args = parser.parse_args()

    count = run_seed(reset=args.reset)
    print(f"[OK] Catalogo vintage inicial pronto! Total processado: {count} pecas.")
