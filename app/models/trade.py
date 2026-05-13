from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Trade:
    trade_id: str
    order_id: str
    platform_id: str
    platform_user_id: str
    instrument_type: str
    instrument_id: str
    side: str
    quantity: Decimal
    price: Decimal
    exchange_fee: Decimal
    executed_at: datetime