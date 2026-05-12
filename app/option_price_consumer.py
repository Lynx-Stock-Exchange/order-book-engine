import json
import os
from decimal import Decimal
from app.db import Database

from kafka import KafkaConsumer

from app.kafka.producer import publish
from app.repositories.option_repository import OptionRepository
from app.option_pricing_service import OptionPricingService
from app.option_expiry_service import OptionExpiryService


consumer = KafkaConsumer(
    os.getenv("KAFKA_STOCK_PRICES_TOPIC", "stock.prices"),
    bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="option-pricing-engine",
)

option_repo = OptionRepository()
pricing_service = OptionPricingService()
expiry_service = OptionExpiryService()


def start_consumer():

    for message in consumer:

        data = message.value
        ticker = data["ticker"]
        stock_price = Decimal(str(data["price"]))

        # 1. Auto-exercise and expire any options whose time has come,
        #    using the current stock price for in-the-money determination
        expiry_service.expire_options(stock_prices={ticker: stock_price})

        # 2. Reprice remaining active options on this underlying
        #    (find_active_by_underlying only returns is_active=TRUE rows,
        #    so just-expired options are already excluded)
        options = option_repo.find_active_by_underlying(ticker)

        for option in options:

            premium = pricing_service.calculate_premium(option, stock_price)

            option_repo.update_premium(option.option_id, premium)

            publish("option_prices", {
                "option_id": option.option_id,
                "premium": str(premium),
                "underlying_ticker": ticker,
            })

            print("OPTION REPRICED:", option.option_id, premium)


if __name__ == "__main__":
    Database.init_pool()
    start_consumer()
