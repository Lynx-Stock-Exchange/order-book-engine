from app.market_state import MarketState
from app.errors import OrderRejected


class OrderSubmissionService:

    def __init__(self, order_repository):
        self.order_repo = order_repository

    def submit_order(self, order):

        if not MarketState.is_open:
            raise OrderRejected(
                code="MARKET_CLOSED",
                message="Market is currently closed."
            )

        self.order_repo.insert(order)

        return {
            "status": "ACCEPTED",
            "order_id": order.order_id
        }