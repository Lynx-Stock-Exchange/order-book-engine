from datetime import datetime, timezone
from decimal import Decimal

from app.order import OrderStatus, OrderType
from app.repositories.order_repository import OrderRepository
from app.repositories.trade_repository import TradeRepository
from app.models.trade import Trade


class OrderBookService:

    def __init__(
        self,
        order_book,
        order_repository: OrderRepository,
        trade_repository: TradeRepository
    ):
        self.order_book = order_book
        self.order_repo = order_repository
        self.trade_repo = trade_repository

    # ─── Cancel ───────────────────────────────────────────────────────────────

    def cancel_order(self, order_id: str) -> None:

        db_order = self.order_repo.find_by_order_id(order_id)

        if db_order is None:
            return

        if db_order.status in (
            "CANCELLED",
            "FILLED",
            "EXPIRED",
            "REJECTED"
        ):
            return

        self.order_repo.update_status(
            order_id,
            "CANCELLED"
        )

    # ─── TTL Expiry ───────────────────────────────────────────────────────────

    def expire_stale_orders(self, current_time: datetime) -> list[str]:

        expired_ids = []

        all_orders = self.order_repo.find_all_open_orders()

        for order in all_orders:

            if order.order_type != "LIMIT":
                continue

            if order.expires_at is None:
                continue

            if order.expires_at <= current_time:

                self.order_repo.update_status(
                    order.order_id,
                    "EXPIRED"
                )

                expired_ids.append(order.order_id)

        return expired_ids

    # ─── Market Close ─────────────────────────────────────────────────────────

    def handle_market_close(self) -> dict:

        expired = []
        rejected = []

        all_orders = self.order_repo.find_all_open_orders()

        for order in all_orders:

            if order.order_type == "LIMIT":

                self.order_repo.update_status(
                    order.order_id,
                    "EXPIRED"
                )

                expired.append(order.order_id)

            elif order.order_type == "MARKET":

                self.order_repo.update_status(
                    order.order_id,
                    "REJECTED"
                )

                rejected.append(order.order_id)

        return {
            "expired": expired,
            "rejected": rejected
        }

    # ─── Persist Trades ───────────────────────────────────────────────────────

    def persist_trades(
        self,
        raw_trades: list[dict],
        instrument_type: str
    ) -> None:

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
                exchange_fee=Decimal(
                    str(raw.get("exchange_fee", "0"))
                ),
                executed_at=raw.get(
                    "executed_at",
                    datetime.now(timezone.utc)
                )
            )

            self.trade_repo.insert(trade)