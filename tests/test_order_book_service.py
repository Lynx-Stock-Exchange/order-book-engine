import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, call

from app.order import Order, OrderType, Side, OrderStatus
from app.order_book import OrderBook
from app.order_book_service import OrderBookService


def make_order(order_id="order-001", order_type=OrderType.LIMIT,
               side=Side.BUY, status=OrderStatus.PENDING,
               expires_at=None):
    order = Order(
        order_id=order_id,
        platform_id="platform-1",
        platform_user_id="user-1",
        instrument_type="STOCK",
        instrument_id="AAPL",
        order_type=order_type,
        side=side,
        quantity=10,
        limit_price=150.0,
        expires_at=expires_at
    )
    order.status = status
    return order


def make_service(order_book=None):
    if order_book is None:
        order_book = OrderBook("AAPL")
    order_repo = MagicMock()
    trade_repo = MagicMock()
    service = OrderBookService(order_book, order_repo, trade_repo)
    return service, order_repo, trade_repo


# ─── Cancel Tests ─────────────────────────────────────────────────────────────

def test_cancel_order_cancels_in_memory_and_persists():
    book = OrderBook("AAPL")
    order = make_order()
    book.add(order)

    service, order_repo, _ = make_service(book)
    service.cancel_order("order-001")

    assert order.status == OrderStatus.CANCELLED
    assert all(o.order_id != "order-001"
               for o in book.buy_orders + book.sell_orders)
    order_repo.update_status.assert_called_once_with("order-001", "CANCELLED")


def test_cancel_order_is_idempotent():
    book = OrderBook("AAPL")
    order = make_order(status=OrderStatus.CANCELLED)

    service, order_repo, _ = make_service(book)
    service.cancel_order("order-001")
    service.cancel_order("order-001")

    order_repo.update_status.assert_called_with("order-001", "CANCELLED")


def test_cancel_order_does_nothing_for_filled_order():
    book = OrderBook("AAPL")
    service, order_repo, _ = make_service(book)

    db_order = MagicMock()
    db_order.status = "FILLED"
    order_repo.find_by_order_id.return_value = db_order

    service.cancel_order("order-999")

    order_repo.update_status.assert_not_called()


def test_cancel_order_does_nothing_when_order_not_found():
    book = OrderBook("AAPL")
    service, order_repo, _ = make_service(book)
    order_repo.find_by_order_id.return_value = None

    service.cancel_order("nonexistent")

    order_repo.update_status.assert_not_called()


# ─── TTL Expiry Tests ──────────────────────────────────────────────────────────

def test_expire_stale_orders_expires_past_due_limit_orders():
    book = OrderBook("AAPL")
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    order = make_order(expires_at=past, order_type=OrderType.LIMIT)
    book.add(order)

    service, order_repo, _ = make_service(book)
    expired = service.expire_stale_orders(datetime.now(timezone.utc))

    assert "order-001" in expired
    assert order.status == OrderStatus.EXPIRED
    order_repo.update_status.assert_called_once_with("order-001", "EXPIRED")


def test_expire_stale_orders_does_not_expire_future_orders():
    book = OrderBook("AAPL")
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    order = make_order(expires_at=future, order_type=OrderType.LIMIT)
    book.add(order)

    service, order_repo, _ = make_service(book)
    expired = service.expire_stale_orders(datetime.now(timezone.utc))

    assert expired == []
    order_repo.update_status.assert_not_called()


def test_expire_stale_orders_does_not_expire_market_orders():
    book = OrderBook("AAPL")
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    order = make_order(expires_at=past, order_type=OrderType.MARKET)
    book.add(order)

    service, order_repo, _ = make_service(book)
    expired = service.expire_stale_orders(datetime.now(timezone.utc))

    assert expired == []
    order_repo.update_status.assert_not_called()


def test_expire_stale_orders_skips_already_filled_orders():
    book = OrderBook("AAPL")
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    order = make_order(expires_at=past,
                       order_type=OrderType.LIMIT,
                       status=OrderStatus.FILLED)
    book.add(order)

    service, order_repo, _ = make_service(book)
    expired = service.expire_stale_orders(datetime.now(timezone.utc))

    assert expired == []
    order_repo.update_status.assert_not_called()


# ─── Market Close Tests ────────────────────────────────────────────────────────

def test_handle_market_close_expires_limit_orders():
    book = OrderBook("AAPL")
    order = make_order(order_id="order-001", order_type=OrderType.LIMIT)
    book.add(order)

    service, order_repo, _ = make_service(book)
    result = service.handle_market_close()

    assert "order-001" in result["expired"]
    assert result["rejected"] == []
    assert order.status == OrderStatus.EXPIRED
    order_repo.update_status.assert_called_with("order-001", "EXPIRED")


def test_handle_market_close_rejects_market_orders():
    book = OrderBook("AAPL")
    order = make_order(order_id="order-002", order_type=OrderType.MARKET)
    book.add(order)

    service, order_repo, _ = make_service(book)
    result = service.handle_market_close()

    assert "order-002" in result["rejected"]
    assert result["expired"] == []
    assert order.status == OrderStatus.REJECTED
    order_repo.update_status.assert_called_with("order-002", "REJECTED")


def test_handle_market_close_skips_already_filled_orders():
    book = OrderBook("AAPL")
    order = make_order(order_id="order-003",
                       order_type=OrderType.LIMIT,
                       status=OrderStatus.FILLED)
    book.add(order)

    service, order_repo, _ = make_service(book)
    result = service.handle_market_close()

    assert result["expired"] == []
    assert result["rejected"] == []
    order_repo.update_status.assert_not_called()


def test_handle_market_close_clears_book():
    book = OrderBook("AAPL")
    limit_order = make_order(order_id="order-001",
                             order_type=OrderType.LIMIT)
    market_order = make_order(order_id="order-002",
                              order_type=OrderType.MARKET)
    book.add(limit_order)
    book.add(market_order)

    service, _, _ = make_service(book)
    service.handle_market_close()

    assert book.buy_orders == []
    assert book.sell_orders == []