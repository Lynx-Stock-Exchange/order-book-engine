from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.kafka.producer import publish
from app.db import Database
from app.config import Config
from app.models.trade import Trade
from app.repositories.trade_repository import TradeRepository
from app.repositories.order_repository import OrderRepository


class OptionExpiryService:

    def __init__(self):
        self.trade_repo = TradeRepository()
        self.order_repo = OrderRepository()

    def expire_options(self, stock_prices: dict = None):
        """
        Process all options whose expiry_time has passed.

        For each expired option:
          - BUY orders that are in-the-money  -> auto-exercised (FILLED trade created)
          - Everything else (SELL, out-of-money, no price) -> EXPIRED

        stock_prices: dict of { underlying_ticker: current_price } used for
        in-the-money determination. If a ticker is missing, all open orders
        for that option are expired without exercise.
        """
        conn = Database.get_connection()

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT option_id, underlying_ticker, option_type, strike_price
                    FROM options
                    WHERE expiry_time <= %s AND is_active = TRUE
                """, (datetime.utcnow(),))
                expired_rows = cur.fetchall()

            if not expired_rows:
                return

            for row in expired_rows:
                option_id, ticker, option_type, strike_price = row
                current_price = (
                    Decimal(str(stock_prices[ticker]))
                    if stock_prices and ticker in stock_prices
                    else None
                )
                self._process_expired_option(
                    option_id=option_id,
                    ticker=ticker,
                    option_type=option_type,
                    strike_price=Decimal(str(strike_price)),
                    current_price=current_price,
                )

            # Mark all now-expired options inactive
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE options
                    SET is_active = FALSE
                    WHERE expiry_time <= %s AND is_active = TRUE
                """, (datetime.utcnow(),))
                expired_count = cur.rowcount

            conn.commit()

            if expired_count > 0:
                publish("option_expired", {
                    "type": "OPTION_EXPIRED",
                    "expired_count": expired_count,
                })

        finally:
            Database.release_connection(conn)

    def _process_expired_option(
        self,
        option_id: str,
        ticker: str,
        option_type: str,
        strike_price: Decimal,
        current_price: Decimal | None,
    ):
        open_orders = self.order_repo.find_open_by_ticker(option_id)

        for order in open_orders:

            # No price info — can't determine ITM, expire everything
            if current_price is None:
                self.order_repo.update_status(order.order_id, "EXPIRED")
                continue

            # Determine in-the-money and per-contract exercise gain (spec §8.3)
            if option_type == "CALL":
                in_the_money = current_price > strike_price
                exercise_gain = current_price - strike_price
            else:  # PUT
                in_the_money = current_price < strike_price
                exercise_gain = strike_price - current_price

            # Only BUY orders benefit from auto-exercise
            if not in_the_money or order.side != "BUY":
                self.order_repo.update_status(order.order_id, "EXPIRED")
                continue

            # Auto-exercise: fill the remaining quantity at the exercise gain
            remaining = order.quantity - order.filled_quantity
            fee = (
                exercise_gain * remaining * Config.EXCHANGE_FEE_RATE
            ).quantize(Decimal("0.01"))

            trade = Trade(
                trade_id=str(uuid4()),
                order_id=order.order_id,
                platform_id=order.platform_id,
                platform_user_id=order.platform_user_id,
                instrument_type="OPTION",
                instrument_id=option_id,
                side="BUY",
                quantity=remaining,
                price=exercise_gain,
                exchange_fee=fee,
                executed_at=datetime.utcnow(),
            )
            self.trade_repo.insert(trade)

            self.order_repo.update_status(
                order_id=order.order_id,
                status="FILLED",
                filled_quantity=order.quantity,
                average_fill_price=exercise_gain,
                exchange_fee=fee,
            )

            publish("order.updates", {
                "type": "OPTION_EXERCISED",
                "payload": {
                    "order_id": order.order_id,
                    "option_id": option_id,
                    "underlying_ticker": ticker,
                    "exercise_price": str(exercise_gain),
                    "quantity": str(remaining),
                    "exchange_fee": str(fee),
                }
            })
