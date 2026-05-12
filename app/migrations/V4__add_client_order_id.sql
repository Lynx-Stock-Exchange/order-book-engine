ALTER TABLE orders
    ADD COLUMN IF NOT EXISTS client_order_id VARCHAR(64);

-- Unique constraint ensures (platform_id, client_order_id) is never duplicated.
-- NULL values are excluded from uniqueness checks, so existing rows without a
-- client_order_id are unaffected.
CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_platform_client
    ON orders (platform_id, client_order_id)
    WHERE client_order_id IS NOT NULL;
