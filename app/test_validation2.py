from decimal import Decimal
from datetime import datetime

from app.order import Order, OrderType, Side
from app.errors import OrderRejected


def test_invalid_quantity():
    try:
        Order(
            order_id="1",
            platform_id="platform",
            platform_user_id="user",
            instrument_type="STOCK",
            instrument_id="AAPL",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=Decimal("-5"),
            limit_price=Decimal("100"),
        )
    except OrderRejected as e:
        print(e.code)
        print(e.message)


def test_order_size_exceeded():
    try:
        Order(
            order_id="2",
            platform_id="platform",
            platform_user_id="user",
            instrument_type="STOCK",
            instrument_id="AAPL",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=Decimal("999999"),
            limit_price=Decimal("100"),
        )
    except OrderRejected as e:
        print(e.code)
        print(e.message)


def test_invalid_limit_price():
    try:
        Order(
            order_id="3",
            platform_id="platform",
            platform_user_id="user",
            instrument_type="STOCK",
            instrument_id="AAPL",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=Decimal("10"),
            limit_price=None,
        )
    except OrderRejected as e:
        print(e.code)
        print(e.message)


def test_market_with_limit_price():
    try:
        Order(
            order_id="4",
            platform_id="platform",
            platform_user_id="user",
            instrument_type="STOCK",
            instrument_id="AAPL",
            order_type=OrderType.MARKET,
            side=Side.BUY,
            quantity=Decimal("10"),
            limit_price=Decimal("100"),
        )
    except OrderRejected as e:
        print(e.code)
        print(e.message)


def test_invalid_instrument_type():
    try:
        Order(
            order_id="5",
            platform_id="platform",
            platform_user_id="user",
            instrument_type="CRYPTO",
            instrument_id="BTC",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=Decimal("1"),
            limit_price=Decimal("100"),
        )
    except OrderRejected as e:
        print(e.code)
        print(e.message)


def test_expired_option():
    try:
        Order(
            order_id="6",
            platform_id="platform",
            platform_user_id="user",
            instrument_type="OPTION",
            instrument_id="AAPL_CALL_100",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=Decimal("1"),
            limit_price=Decimal("5"),
            expires_at=datetime(2020, 1, 1),
        )
    except OrderRejected as e:
        print(e.code)
        print(e.message)


if __name__ == "__main__":
    print("\nINVALID QUANTITY")
    test_invalid_quantity()

    print("\nORDER SIZE EXCEEDED")
    test_order_size_exceeded()

    print("\nINVALID LIMIT PRICE")
    test_invalid_limit_price()

    print("\nMARKET WITH LIMIT PRICE")
    test_market_with_limit_price()

    print("\nINVALID INSTRUMENT TYPE")
    test_invalid_instrument_type()

    print("\nEXPIRED OPTION")
    test_expired_option()