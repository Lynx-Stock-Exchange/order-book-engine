CREATE TABLE IF NOT EXISTS orders
(
    order_id           VARCHAR(255)   NOT NULL PRIMARY KEY,
    platform_id        VARCHAR(255)   NOT NULL,
    platform_user_id   VARCHAR(255)   NOT NULL,
    instrument_type    VARCHAR(10)    NOT NULL CHECK (instrument_type IN ('STOCK', 'OPTION')),
    instrument_id      VARCHAR(50)    NOT NULL,
    order_type         VARCHAR(10)    NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT')),
    side               VARCHAR(4)     NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity           NUMERIC(19, 4) NOT NULL,
    limit_price        NUMERIC(19, 4),
    status             VARCHAR(20)    NOT NULL,
    filled_quantity    NUMERIC(19, 4) NOT NULL DEFAULT 0,
    average_fill_price NUMERIC(19, 4),
    exchange_fee       NUMERIC(19, 4) NOT NULL DEFAULT 0,
    created_at         TIMESTAMP      NOT NULL,
    updated_at         TIMESTAMP      NOT NULL,
    expires_at         TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_instrument_id ON orders (instrument_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_platform_id ON orders (platform_id);

CREATE TABLE IF NOT EXISTS trades
(
    trade_id         VARCHAR(255)   NOT NULL PRIMARY KEY,
    order_id         VARCHAR(255)   NOT NULL,
    platform_id      VARCHAR(255)   NOT NULL,
    platform_user_id VARCHAR(255)   NOT NULL,
    instrument_type  VARCHAR(10)    NOT NULL CHECK (instrument_type IN ('STOCK', 'OPTION')),
    instrument_id    VARCHAR(50)    NOT NULL,
    side             VARCHAR(4)     NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity         NUMERIC(19, 4) NOT NULL,
    price            NUMERIC(19, 4) NOT NULL,
    exchange_fee     NUMERIC(19, 4) NOT NULL DEFAULT 0,
    executed_at      TIMESTAMP      NOT NULL,

    CONSTRAINT fk_trade_order FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

CREATE INDEX IF NOT EXISTS idx_trades_order_id ON trades (order_id);
CREATE INDEX IF NOT EXISTS idx_trades_instrument_id ON trades (instrument_id);

CREATE TABLE IF NOT EXISTS options
(
    option_id VARCHAR(255) PRIMARY KEY,

    underlying_ticker VARCHAR(50) NOT NULL,

    option_type VARCHAR(10) NOT NULL
        CHECK (option_type IN ('CALL', 'PUT')),

    strike_price NUMERIC(19,4) NOT NULL,

    expiry_time TIMESTAMP NOT NULL,

    premium NUMERIC(19,4) NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE
);