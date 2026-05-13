from decimal import Decimal
from app.config import Config

_current_fee_rate: Decimal = Config.EXCHANGE_FEE_RATE


def get_fee_rate() -> Decimal:
    return _current_fee_rate


def set_fee_rate(rate: Decimal) -> None:
    global _current_fee_rate
    _current_fee_rate = rate
