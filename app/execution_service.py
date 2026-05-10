from decimal import Decimal
from datetime import datetime
from uuid import uuid4
from app.config import Config

from app.order_book import OrderBook
from app.matcher import match
from app.models.trade import Trade
from app.kafka.producer import publish

from app.repositories.order_repository import OrderRepository
from app.repositories.trade_repository import TradeRepository

from app.order import Order as RuntimeOrder
from app.order import (
    OrderType,
    OrderStatus,
    Side,
)


class ExecutionService:

    def __init__(self):
        self.order_repo = OrderRepository()
        self.trade_repo = TradeRepository()

    def execute_tick(self, instrument_id, current_price):

        # --- 1. LOAD OPEN ORDERS FROM DB ---
        db_orders = self.order_repo.find_open_by_ticker(instrument_id)

        # --- 2. EXPIRE STALE LIMIT ORDERS ---
        # Any LIMIT order whose expires_at has passed must not enter the book.
        # We expire them here so the broker platform gets an ORDER_UPDATE
        # immediately on the same tick rather than waiting for a separate sweep.
        now = datetime.utcnow()
        active_db_orders = []

        for o in db_orders:
            if (
                o.order_type == "LIMIT"
                and o.expires_at is not None
                and o.expires_at <= now
            ):
                self.order_repo.update_status(o.order_id, "EXPIRED")
                publish("order.updates", {
                    "type": "ORDER_UPDATE",
                    "payload": {
                        "order_id": o.order_id,
                        "platform_id": o.platform_id,
                        "status": "EXPIRED",
                        "filled_quantity": str(o.filled_quantity),
                        "average_fill_price": (
                            str(o.average_fill_price)
                            if o.average_fill_price is not None
                            else None
                        ),
                        "exchange_fee": str(o.exchange_fee),
                    }
                })
            else:
                active_db_orders.append(o)

        # --- 3. BUILD IN-MEMORY ORDER BOOK ---
        book = OrderBook(instrument_id)

        runtime_orders = []

        for o in active_db_orders:
            runtime_order = RuntimeOrder(
                order_id=o.order_id,
                platform_id=o.platform_id,
                platform_user_id=o.platform_user_id,
                instrument_type=o.instrument_type,
                instrument_id=o.instrument_id,
                order_type=OrderType(o.order_type),
                side=Side(o.side),
                quantity=o.quantity,
                limit_price=o.limit_price,
                expires_at=o.expires_at,
            )

            runtime_order.status = OrderStatus(o.status)
            runtime_order.filled_quantity = o.filled_quantity

            if o.average_fill_price is not None:
                runtime_order.average_fill_price = o.average_fill_price

            runtime_orders.append(runtime_order)
            book.add(runtime_order)

        # --- 4. MATCH ---
        trades = match(book, current_price)

        # --- 5. PERSIST RESULTS ---
        for trade_data in trades:

            fee = (
                Decimal(str(trade_data["price"]))
                * Decimal(str(trade_data["quantity"]))
                * Config.EXCHANGE_FEE_RATE
            ).quantize(Decimal("0.01"))

            trade = Trade(
                trade_id=str(uuid4()),
                order_id=trade_data["order_id"],
                platform_id=trade_data["platform_id"],
                platform_user_id=trade_data["platform_user_id"],
                instrument_type=trade_data["instrument_type"],
                instrument_id=trade_data["instrument_id"],
                side=trade_data["side"],
                quantity=Decimal(str(trade_data["quantity"])),
                price=Decimal(str(trade_data["price"])),
                exchange_fee=fee,
                executed_at=datetime.utcnow(),
            )

            # SAVE TRADE
            self.trade_repo.insert(trade)

            publish("order.updates", {
                "type": "TRADE_EXECUTED",
                "payload": {
                    "trade_id": trade.trade_id,
                    "order_id": trade.order_id,
                    "platform_id": trade.platform_id,
                    "instrument_id": trade.instrument_id,
                    "side": trade.side,
                    "quantity": str(trade.quantity),
                    "price": str(trade.price),
                    "exchange_fee": str(trade.exchange_fee),
                }
            })

            # FIND UPDATED ORDER
            updated_order = next(
                o for o in runtime_orders
                if o.order_id == trade.order_id
            )

            total_fee = (Decimal(str(updated_order.filled_quantity)) \
                * Decimal(str(updated_order.average_fill_price)) \
                * Config.EXCHANGE_FEE_RATE).quantize(Decimal("0.01"))

            # UPDATE ORDER
            self.order_repo.update_status(
                order_id=updated_order.order_id,
                status=updated_order.status.value,
                filled_quantity=Decimal(str(updated_order.filled_quantity)),
                average_fill_price=Decimal(str(updated_order.average_fill_price)),
                exchange_fee=total_fee,
            )

            publish("order.updates", {
                "type": "ORDER_UPDATE",
                "payload": {
                    "order_id": updated_order.order_id,
                    "platform_id": updated_order.platform_id,
                    "status": updated_order.status.value,
                    "filled_quantity": str(updated_order.filled_quantity),
                    "average_fill_price": str(updated_order.average_fill_price),
                    "exchange_fee": str(total_fee),
                }
            })

        # --- 6. PUBLISH BUY & SELL VOLUMES ---
        # Price Simulation consumes this to calculate order_pressure_component
        # per-tick per-instrument (spec §6.2: pressure_ratio = (buy-sell)/total)
        buy_volume = sum(
            Decimal(str(t["quantity"]))
            for t in trades
            if t["side"] == "BUY"
        )
        sell_volume = sum(
            Decimal(str(t["quantity"]))
            for t in trades
            if t["side"] == "SELL"
        )
        publish(Config.KAFKA_VOLUMES_TOPIC, {
            "instrument_id": instrument_id,
            "buy_volume": str(buy_volume),
            "sell_volume": str(sell_volume),
            "total_volume": str(buy_volume + sell_volume),
        })

        return trades