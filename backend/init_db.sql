-- ==============================================================================
-- Vintage Brechó - Database Initialization & DDL Migration Script
-- Target: Supabase PostgreSQL (AWS sa-east-1)
-- ==============================================================================

-- 1. Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Products table (1-of-1 exclusive vintage feminine pieces)
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Orders table (PIX checkouts with 10-minute hold)
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50),
    customer_address TEXT,
    shipping_cost NUMERIC(10, 2) NOT NULL DEFAULT 15.00,
    total_amount NUMERIC(10, 2) NOT NULL,
    mercadopago_payment_id VARCHAR(100),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. High-performance composite and lookup indices
CREATE INDEX IF NOT EXISTS idx_products_status_lock ON products(status, locked_until);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);
CREATE INDEX IF NOT EXISTS idx_orders_mp_payment_id ON orders(mercadopago_payment_id);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);

-- 5. Supabase Storage: Initialize 'brecho-photos' bucket
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'brecho-photos',
    'brecho-photos',
    true,
    10485760,
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/heic']
)
ON CONFLICT (id) DO UPDATE 
SET public = true,
    file_size_limit = 10485760,
    allowed_mime_types = ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/heic'];

-- 6. Storage Row Level Security (RLS) Policies
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' 
          AND tablename = 'objects' 
          AND policyname = 'Public Access brecho-photos'
    ) THEN
        CREATE POLICY "Public Access brecho-photos" 
        ON storage.objects FOR SELECT 
        USING (bucket_id = 'brecho-photos');
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' 
          AND tablename = 'objects' 
          AND policyname = 'Public Upload brecho-photos'
    ) THEN
        CREATE POLICY "Public Upload brecho-photos" 
        ON storage.objects FOR INSERT 
        WITH CHECK (bucket_id = 'brecho-photos');
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'storage' 
          AND tablename = 'objects' 
          AND policyname = 'Public Update brecho-photos'
    ) THEN
        CREATE POLICY "Public Update brecho-photos" 
        ON storage.objects FOR UPDATE 
        USING (bucket_id = 'brecho-photos');
    END IF;
END $$;
