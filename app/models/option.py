from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OptionType(Enum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass
class Option:
    option_id: str

    underlying_ticker: str

    option_type: OptionType

    strike_price: Decimal

    expiry_time: datetime

    premium: Decimal

    is_active: bool = True