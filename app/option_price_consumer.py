import json
from datetime import datetime
from app.db import Database

from kafka import KafkaConsumer

from app.kafka.producer import publish

from app.repositories.option_repository import (
    OptionRepository
)

from app.option_pricing_service import (
    OptionPricingService
)

consumer = KafkaConsumer(
    "stock_prices",

    bootstrap_servers="localhost:9092",

    value_deserializer=lambda m:
        json.loads(m.decode("utf-8")),

    auto_offset_reset="latest",

    group_id="option-pricing-engine",
)

option_repo = OptionRepository()

pricing_service = OptionPricingService()


def start_consumer():

    for message in consumer:

        data = message.value

        ticker = data["ticker"]

        stock_price = data["price"]

        options = option_repo.find_active_by_underlying(
            ticker
        )

        for option in options:

            if option.expiry_time <= datetime.utcnow():
                continue

            premium = pricing_service.calculate_premium(
                option,
                stock_price
            )

            option_repo.update_premium(
                option.option_id,
                premium
            )

            publish("option_prices", {

                "option_id": option.option_id,

                "premium": str(premium),

                "underlying_ticker": ticker
            })

            print(
                "OPTION REPRICED:",
                option.option_id,
                premium
            )


if __name__ == "__main__":
    Database.init_pool()
    start_consumer()