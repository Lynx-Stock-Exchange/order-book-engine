from decimal import Decimal

from app.order import Order, OrderType, Side
from app.errors import OrderRejected


def test_invalid_quantity():
    try:
        Order(
            order_id="1",
            platform_id="p1",
            platform_user_id="u1",
            instrument_type="STOCK",
            instrument_id="AAPL",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=Decimal("-5"),
            limit_price=Decimal("100"),
        )
    except OrderRejected as e:
        print(e.code, e.message)


def test_invalid_limit_order():
    try:
        Order(
            order_id="2",
            platform_id="p1",
            platform_user_id="u1",
            instrument_type="STOCK",
            instrument_id="AAPL",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=Decimal("10"),
        )
    except OrderRejected as e:
        print(e.code, e.message)


def test_invalid_market_order():
    try:
        Order(
            order_id="3",
            platform_id="p1",
            platform_user_id="u1",
            instrument_type="STOCK",
            instrument_id="AAPL",
            order_type=OrderType.MARKET,
            side=Side.BUY,
            quantity=Decimal("10"),
            limit_price=Decimal("100"),
        )
    except OrderRejected as e:
        print(e.code, e.message)


def test_invalid_instrument():
    try:
        Order(
            order_id="4",
            platform_id="p1",
            platform_user_id="u1",
            instrument_type="CRYPTO",
            instrument_id="BTC",
            order_type=OrderType.MARKET,
            side=Side.BUY,
            quantity=Decimal("10"),
        )
    except OrderRejected as e:
        print(e.code, e.message)


def test_option_order():
    try:
        order = Order(
            order_id="5",
            platform_id="p1",
            platform_user_id="u1",
            instrument_type="OPTION",
            instrument_id="AAPL_2025_C150",
            order_type=OrderType.LIMIT,
            side=Side.BUY,
            quantity=Decimal("10"),
            limit_price=Decimal("5"),
        )

        print("OPTION ORDER OK")
        print(order.instrument_type)

    except OrderRejected as e:
        print(e.code, e.message)


test_invalid_quantity()
test_invalid_limit_order()
test_invalid_market_order()
test_invalid_instrument()
test_option_order()