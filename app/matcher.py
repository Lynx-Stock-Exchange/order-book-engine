from app.order import OrderType, OrderStatus, Side
from app.errors import OrderRejected



def match(order_book, current_price, max_liquidity_per_tick=50):
    trades = []

    remaining_liquidity = max_liquidity_per_tick

    for order in order_book.iter_matchable(current_price):

        if remaining_liquidity <= 0:
            break 

        remaining = order.remaining
        if remaining <= 0:
            continue

        fill_qty = min(remaining, remaining_liquidity)

        if order.order_type == OrderType.MARKET:
            price = current_price
        else:
            price = order.limit_price

        order.apply_fill(fill_qty, price)

        remaining_liquidity -= fill_qty 

        trades.append({
            "order_id": order.order_id,
            "platform_id": order.platform_id,
            "platform_user_id": order.platform_user_id,
            "instrument_id": order.instrument_id,
            "instrument_type": order.instrument_type,
            "side": order.side.value,
            "quantity": fill_qty,
            "price": price,
        })

    return trades