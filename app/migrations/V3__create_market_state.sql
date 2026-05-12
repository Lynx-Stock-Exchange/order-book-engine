CREATE TABLE IF NOT EXISTS market_state (
    id      SERIAL PRIMARY KEY,
    is_open BOOLEAN   NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Seed a single row with the market closed (safe default).
-- If a row already exists this is a no-op.
INSERT INTO market_state (is_open)
SELECT FALSE
WHERE NOT EXISTS (SELECT 1 FROM market_state);
