from app.market_state import MarketState
from app.errors import OrderRejected
from app.repositories.option_repository import OptionRepository


class OrderSubmissionService:

    def __init__(self, order_repository, option_repository=None):
        self.order_repo = order_repository
        self.option_repo = option_repository or OptionRepository()

    def submit_order(self, order):

        # Idempotency check: if a client_order_id was provided, return the
        # existing order rather than inserting a duplicate.
        if order.client_order_id:
            existing = self.order_repo.find_by_client_order_id(
                order.platform_id, order.client_order_id
            )
            if existing:
                return {
                    "status": "DUPLICATE",
                    "order_id": existing.order_id,
                    "client_order_id": existing.client_order_id,
                }

        if not MarketState.is_open:
            raise OrderRejected(
                code="MARKET_CLOSED",
                message="Market is currently closed."
            )

        if order.instrument_type == "OPTION":
            option = self.option_repo.find_by_id(order.instrument_id)
            if option is None or not option.is_active:
                raise OrderRejected(
                    code="OPTION_EXPIRED",
                    message="The option contract has expired or does not exist."
                )

        self.order_repo.insert(order)

        return {
            "status": "ACCEPTED",
            "order_id": order.order_id
        }
