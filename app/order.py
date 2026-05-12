from enum import Enum
from decimal import Decimal
from app.errors import OrderRejected
from app.config import Config
from datetime import datetime
 

class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Order:
    def __init__(
        self,
        order_id,
        platform_id,
        platform_user_id,
        instrument_type,
        instrument_id,
        order_type,
        side,
        quantity,
        limit_price=None,
        expires_at=None,
    ):
         # --- VALIDATION ---

        if quantity <= 0:
            raise OrderRejected(
                code="INVALID_QUANTITY",
                message="Quantity must be positive."
            )
        
        if quantity > Config.MAX_ORDER_SIZE:
            raise OrderRejected(
                code="ORDER_SIZE_EXCEEDED",
                message="Order quantity exceeds platform limit."
            )

        if (
            order_type == OrderType.LIMIT
            and (limit_price is None or limit_price <= 0)
        ):
            raise OrderRejected(
                code="INVALID_LIMIT_PRICE",
                message="LIMIT orders require positive limit_price."
            )
        
        if order_type == OrderType.MARKET and limit_price is not None:
            raise OrderRejected(
                code="INVALID_ORDER_TYPE",
                message="MARKET orders cannot have limit_price."
            )
        
        VALID_INSTRUMENT_TYPES = {"STOCK", "OPTION"}
        
        if instrument_type not in VALID_INSTRUMENT_TYPES:
            raise OrderRejected(
                code="INVALID_INSTRUMENT_TYPE",
                message="Unsupported instrument type."
            )
        
        

        # --- FIELDS ---
        
        self.order_id = order_id
        self.platform_id = platform_id
        self.platform_user_id = platform_user_id
        self.instrument_type = instrument_type
        self.instrument_id = instrument_id

        self.order_type = order_type
        self.side = side

        self.quantity = quantity
        self.filled_quantity = Decimal("0")

        self.limit_price = limit_price
        self.average_fill_price = None

        self.exchange_fee = Decimal("0")

        self.status = OrderStatus.PENDING

        self.expires_at = expires_at

        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    @property
    def remaining(self):
        return self.quantity - self.filled_quantity

    def apply_fill(self, qty, price):
        if self.status in [
            OrderStatus.CANCELLED,
            OrderStatus.EXPIRED,
            OrderStatus.REJECTED,
        ]:
            return

        total_value = (self.average_fill_price or Decimal("0")) * self.filled_quantity
        total_value += price * qty

        self.filled_quantity += qty

        self.average_fill_price = total_value / self.filled_quantity

        if self.remaining == 0:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self):
        if self.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]:
            self.status = OrderStatus.CANCELLED

    def expire(self):
        if self.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]:
            self.status = OrderStatus.EXPIRED