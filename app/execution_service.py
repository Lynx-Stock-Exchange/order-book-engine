from decimal import Decimal
from datetime import datetime
from uuid import uuid4
from app.fee_rate import get_fee_rate

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

        # --- 2. BUILD IN-MEMORY ORDER BOOK ---
        book = OrderBook(instrument_id)

        runtime_orders = []

        for o in db_orders:
            try:
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
            except Exception as e:
                print(f"[execution] skipping order {o.order_id}: {e}")
                continue

        # --- 3. MATCH ---
        trades = match(book, current_price)

        # --- 4. PERSIST RESULTS ---
        for trade_data in trades:

            fee = (
                Decimal(str(trade_data["price"]))
                * Decimal(str(trade_data["quantity"]))
                * get_fee_rate()
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

            # FIND UPDATED ORDER
            updated_order = next(
                o for o in runtime_orders
                if o.order_id == trade.order_id
            )

            total_fee = (Decimal(str(updated_order.filled_quantity)) \
                * Decimal(str(updated_order.average_fill_price)) \
                * get_fee_rate()).quantize(Decimal("0.01"))

            # UPDATE ORDER
            self.order_repo.update_status(
                order_id=updated_order.order_id,
                status=updated_order.status.value,
                filled_quantity=Decimal(str(updated_order.filled_quantity)),
                average_fill_price=Decimal(str(updated_order.average_fill_price)),
                exchange_fee=total_fee,
            )

            # Publish flat message — WS server expects top-level fields, numeric types
            publish("orders.updates", {
                "order_id": updated_order.order_id,
                "platform_id": updated_order.platform_id,
                "status": updated_order.status.value,
                "filled_quantity": int(updated_order.filled_quantity),
                "average_fill_price": float(updated_order.average_fill_price),
                "exchange_fee": float(total_fee),
                "market_time": datetime.utcnow().isoformat(),
            })

        return trades