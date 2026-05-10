from app.market_state import MarketState
from app.errors import OrderRejected
from app.repositories.option_repository import OptionRepository


class OrderSubmissionService:

    def __init__(self, order_repository, option_repository=None):
        self.order_repo = order_repository
        self.option_repo = option_repository or OptionRepository()

    def submit_order(self, order):

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
