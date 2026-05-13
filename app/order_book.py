from app.order import Side
from app.order import OrderStatus, OrderType

class OrderBook:
    def __init__(self, ticker):
        self.ticker = ticker
        self.buy_orders = []
        self.sell_orders = []

    def add(self, order):
        if order.side == Side.BUY:
            self.buy_orders.append(order)
        else:
            self.sell_orders.append(order)

    def remove(self, order_id):
        self.buy_orders = [o for o in self.buy_orders if o.order_id != order_id]
        self.sell_orders = [o for o in self.sell_orders if o.order_id != order_id]

    def get(self):
        return {
            "buys": self.buy_orders,
            "sells": self.sell_orders,
        }

    def top_levels(self):
        best_bid = max(
            [o.limit_price for o in self.buy_orders if o.limit_price is not None],
            default=None,
        )
        best_ask = min(
            [o.limit_price for o in self.sell_orders if o.limit_price is not None],
            default=None,
        )
        return best_bid, best_ask

    def pressure(self):
        buy_volume = sum(o.remaining for o in self.buy_orders)
        sell_volume = sum(o.remaining for o in self.sell_orders)

        total = buy_volume + sell_volume
        if total == 0:
            return 0

        return (buy_volume - sell_volume) / total
    

    
    def iter_matchable(self, current_price):
        orders = []

        for order in self.buy_orders + self.sell_orders:
            if order.status not in (
                OrderStatus.PENDING,
                OrderStatus.PARTIALLY_FILLED,
            ):
                continue

            if order.order_type == OrderType.MARKET:
                orders.append(order)
                continue

            if order.side == Side.BUY and order.limit_price is not None and order.limit_price >= current_price:
                orders.append(order)

            elif order.side == Side.SELL and order.limit_price is not None and order.limit_price <= current_price:
                orders.append(order)


        orders.sort(key=lambda o: o.order_type != OrderType.MARKET)

        for o in orders:
            yield o