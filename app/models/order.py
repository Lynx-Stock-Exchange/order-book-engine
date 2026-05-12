from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Order:
    order_id: str
    platform_id: str
    platform_user_id: str
    instrument_type: str
    instrument_id: str
    order_type: str
    side: str
    quantity: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    limit_price: Optional[Decimal] = None
    filled_quantity: Decimal = Decimal("0")
    average_fill_price: Optional[Decimal] = None
    exchange_fee: Decimal = Decimal("0")
    expires_at: Optional[datetime] = None
    client_order_id: Optional[str] = None