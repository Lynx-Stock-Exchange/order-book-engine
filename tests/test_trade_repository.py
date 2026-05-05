import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.db import Database
from app.models.order import Order
from app.models.trade import Trade
from app.repositories.order_repository import OrderRepository
from app.repositories.trade_repository import TradeRepository


@pytest.fixture(autouse=True)
def setup_db():
    Database.init_pool()
    conn = Database.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM trades")
            cur.execute("DELETE FROM orders")
        conn.commit()
    finally:
        Database.release_connection(conn)


def make_order(order_id="order-001") -> Order:
    return Order(
        order_id=order_id,
        platform_id="platform-1",
        platform_user_id="user-1",
        instrument_type="STOCK",
        instrument_id="AAPL",
        order_type="LIMIT",
        side="BUY",
        quantity=Decimal("10"),
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        limit_price=Decimal("150.00"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        exchange_fee=Decimal("0"),
        expires_at=None
    )


def make_trade(trade_id="trade-001", order_id="order-001") -> Trade:
    return Trade(
        trade_id=trade_id,
        order_id=order_id,
        platform_id="platform-1",
        platform_user_id="user-1",
        instrument_type="STOCK",
        instrument_id="AAPL",
        side="BUY",
        quantity=Decimal("5"),
        price=Decimal("150.00"),
        exchange_fee=Decimal("0.75"),
        executed_at=datetime.now(timezone.utc)
    )


def test_insert_and_find_by_order_id():
    order_repo = OrderRepository()
    trade_repo = TradeRepository()

    order = make_order()
    order_repo.insert(order)

    trade = make_trade()
    trade_repo.insert(trade)

    found = trade_repo.find_by_order_id("order-001")

    assert len(found) == 1
    assert found[0].trade_id == trade.trade_id
    assert found[0].order_id == trade.order_id
    assert found[0].platform_id == trade.platform_id
    assert found[0].platform_user_id == trade.platform_user_id
    assert found[0].instrument_type == trade.instrument_type
    assert found[0].instrument_id == trade.instrument_id
    assert found[0].side == trade.side
    assert found[0].quantity == trade.quantity
    assert found[0].price == trade.price
    assert found[0].exchange_fee == trade.exchange_fee


def test_find_by_order_id_returns_empty_when_no_trades():
    trade_repo = TradeRepository()
    found = trade_repo.find_by_order_id("nonexistent-order")
    assert found == []


def test_insert_multiple_trades_for_same_order():
    order_repo = OrderRepository()
    trade_repo = TradeRepository()

    order = make_order()
    order_repo.insert(order)

    trade1 = make_trade(trade_id="trade-001")
    trade2 = make_trade(trade_id="trade-002")
    trade_repo.insert(trade1)
    trade_repo.insert(trade2)

    found = trade_repo.find_by_order_id("order-001")
    assert len(found) == 2
    trade_ids = [t.trade_id for t in found]
    assert "trade-001" in trade_ids
    assert "trade-002" in trade_ids


def test_trade_cannot_be_inserted_without_valid_order():
    trade_repo = TradeRepository()
    trade = make_trade(order_id="nonexistent-order")

    with pytest.raises(Exception):
        trade_repo.insert(trade)