from datetime import datetime, timezone
from decimal import Decimal

from app.order import OrderStatus, OrderType
from app.repositories.order_repository import OrderRepository
from app.repositories.trade_repository import TradeRepository
from app.models.trade import Trade


class OrderBookService:

    def __init__(self, order_book, order_repository: OrderRepository,
                 trade_repository: TradeRepository):
        self.order_book = order_book
        self.order_repo = order_repository
        self.trade_repo = trade_repository

    # ─── Cancel ───────────────────────────────────────────────────────────────

    def cancel_order(self, order_id: str) -> None:
        """
        Cancel an order by order_id.
        Idempotent — safe to call multiple times.
        """
        # Find in memory
        all_orders = (self.order_book.buy_orders +
                      self.order_book.sell_orders)
        order = next((o for o in all_orders
                      if o.order_id == order_id), None)

        if order is None:
            # Already removed from book or never existed — check DB
            db_order = self.order_repo.find_by_order_id(order_id)
            if db_order is None:
                return  # Does not exist at all — idempotent, just return
            if db_order.status in ("CANCELLED", "FILLED",
                                   "EXPIRED", "REJECTED"):
                return  # Already in a terminal state — nothing to do
            # Persist cancellation
            self.order_repo.update_status(order_id, "CANCELLED")
            return

        # Cancel in memory
        order.cancel()

        # Remove from book if cancelled
        if order.status == OrderStatus.CANCELLED:
            self.order_book.remove(order_id)

        # Persist — idempotent, safe to call even if already cancelled
        self.order_repo.update_status(order_id, "CANCELLED")

    # ─── TTL Expiry ───────────────────────────────────────────────────────────

    def expire_stale_orders(self, current_time: datetime) -> list[str]:
        """
        Expire all LIMIT orders whose expires_at has passed.
        Returns list of expired order_ids.
        Per spec §6.4 — only LIMIT orders expire.
        """
        expired_ids = []

        all_orders = (self.order_book.buy_orders +
                      self.order_book.sell_orders)

        for order in list(all_orders):
            if order.order_type != OrderType.LIMIT:
                continue
            if order.expires_at is None:
                continue
            if order.status not in (OrderStatus.PENDING,
                                    OrderStatus.PARTIALLY_FILLED):
                continue
            if order.expires_at <= current_time:
                order.expire()
                self.order_book.remove(order.order_id)
                self.order_repo.update_status(order.order_id, "EXPIRED")
                expired_ids.append(order.order_id)

        return expired_ids

    # ─── Market Close ─────────────────────────────────────────────────────────

    def handle_market_close(self) -> dict:
        """
        Handle market close per spec §6.4:
        - LIMIT orders (PENDING or PARTIALLY_FILLED) → EXPIRED
        - MARKET orders (PENDING or PARTIALLY_FILLED) → REJECTED
        Returns counts of expired and rejected orders.
        """
        expired = []
        rejected = []

        all_orders = (self.order_book.buy_orders +
                      self.order_book.sell_orders)

        for order in list(all_orders):
            if order.status not in (OrderStatus.PENDING,
                                    OrderStatus.PARTIALLY_FILLED):
                continue

            if order.order_type == OrderType.LIMIT:
                order.expire()
                self.order_book.remove(order.order_id)
                self.order_repo.update_status(order.order_id, "EXPIRED")
                expired.append(order.order_id)

            elif order.order_type == OrderType.MARKET:
                order.status = OrderStatus.REJECTED
                self.order_book.remove(order.order_id)
                self.order_repo.update_status(order.order_id, "REJECTED")
                rejected.append(order.order_id)

        return {
            "expired": expired,
            "rejected": rejected
        }

    # ─── Persist Trades ───────────────────────────────────────────────────────

    def persist_trades(self, raw_trades: list[dict],
                       instrument_type: str) -> None:
        """
        Persist trade dicts produced by matcher.match() to the database.
        """
        for raw in raw_trades:
            trade = Trade(
                trade_id=raw["trade_id"],
                order_id=raw["order_id"],
                platform_id=raw["platform_id"],
                platform_user_id=raw["platform_user_id"],
                instrument_type=instrument_type,
                instrument_id=raw["instrument_id"],
                side=raw["side"],
                quantity=Decimal(str(raw["quantity"])),
                price=Decimal(str(raw["price"])),
                exchange_fee=Decimal(str(raw.get("exchange_fee", "0"))),
                executed_at=raw.get("executed_at", datetime.now(timezone.utc))
            )
            self.trade_repo.insert(trade)