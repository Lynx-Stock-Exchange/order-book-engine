import pytest
from decimal import Decimal
from datetime import datetime, timezone

from app.db import Database
from app.models.order import Order
from app.repositories.order_repository import OrderRepository


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


def make_order(order_id="order-001", status="PENDING",
               instrument_id="AAPL", order_type="LIMIT") -> Order:
    return Order(
        order_id=order_id,
        platform_id="platform-1",
        platform_user_id="user-1",
        instrument_type="STOCK",
        instrument_id=instrument_id,
        order_type=order_type,
        side="BUY",
        quantity=Decimal("10"),
        status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        limit_price=Decimal("150.00"),
        filled_quantity=Decimal("0"),
        average_fill_price=None,
        exchange_fee=Decimal("0"),
        expires_at=None
    )


def test_insert_and_find_by_order_id():
    repo = OrderRepository()
    order = make_order()

    repo.insert(order)
    found = repo.find_by_order_id("order-001")

    assert found is not None
    assert found.order_id == order.order_id
    assert found.platform_id == order.platform_id
    assert found.platform_user_id == order.platform_user_id
    assert found.instrument_type == order.instrument_type
    assert found.instrument_id == order.instrument_id
    assert found.order_type == order.order_type
    assert found.side == order.side
    assert found.quantity == order.quantity
    assert found.status == order.status
    assert found.limit_price == order.limit_price
    assert found.filled_quantity == order.filled_quantity
    assert found.exchange_fee == order.exchange_fee


def test_find_by_order_id_returns_none_when_not_found():
    repo = OrderRepository()
    found = repo.find_by_order_id("nonexistent-order")
    assert found is None


def test_find_open_by_ticker_returns_pending_orders():
    repo = OrderRepository()
    order1 = make_order(order_id="order-001", status="PENDING", instrument_id="AAPL")
    order2 = make_order(order_id="order-002", status="PARTIALLY_FILLED", instrument_id="AAPL")
    order3 = make_order(order_id="order-003", status="FILLED", instrument_id="AAPL")

    repo.insert(order1)
    repo.insert(order2)
    repo.insert(order3)

    open_orders = repo.find_open_by_ticker("AAPL")

    assert len(open_orders) == 2
    order_ids = [o.order_id for o in open_orders]
    assert "order-001" in order_ids
    assert "order-002" in order_ids
    assert "order-003" not in order_ids


def test_find_open_by_ticker_returns_empty_when_none_open():
    repo = OrderRepository()
    order = make_order(order_id="order-001", status="FILLED", instrument_id="AAPL")
    repo.insert(order)

    open_orders = repo.find_open_by_ticker("AAPL")
    assert len(open_orders) == 0


def test_update_status():
    repo = OrderRepository()
    order = make_order(order_id="order-001", status="PENDING")
    repo.insert(order)

    repo.update_status(
        order_id="order-001",
        status="FILLED",
        filled_quantity=Decimal("10"),
        average_fill_price=Decimal("150.00"),
        exchange_fee=Decimal("1.50")
    )

    updated = repo.find_by_order_id("order-001")
    assert updated.status == "FILLED"
    assert updated.filled_quantity == Decimal("10")
    assert updated.average_fill_price == Decimal("150.00")
    assert updated.exchange_fee == Decimal("1.50")


def test_update_status_only_updates_status_when_no_optionals():
    repo = OrderRepository()
    order = make_order(order_id="order-001", status="PENDING")
    repo.insert(order)

    repo.update_status(order_id="order-001", status="CANCELLED")

    updated = repo.find_by_order_id("order-001")
    assert updated.status == "CANCELLED"
    assert updated.filled_quantity == Decimal("0")