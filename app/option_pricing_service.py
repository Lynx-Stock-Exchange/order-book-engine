from decimal import Decimal
from datetime import datetime

from app.models.option import OptionType


class OptionPricingService:

    def calculate_premium(
        self,
        option,
        stock_price
    ):

        if option.option_type == OptionType.CALL:

            intrinsic = max(
                Decimal(str(stock_price))
                - option.strike_price,
                Decimal("0")
            )

        else:

            intrinsic = max(
                option.strike_price
                - Decimal(str(stock_price)),
                Decimal("0")
            )

        days_left = max(
            (
                option.expiry_time
                - datetime.utcnow()
            ).days,
            0
        )

        time_value = Decimal(days_left) * Decimal("0.1")

        premium = intrinsic + time_value

        return premium.quantize(
            Decimal("0.01")
        )