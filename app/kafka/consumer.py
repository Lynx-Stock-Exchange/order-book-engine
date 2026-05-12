import json
import os
from decimal import Decimal
from kafka import KafkaConsumer
from app.db import Database
from app.execution_service import ExecutionService

STOCK_PRICES_TOPIC = os.getenv("KAFKA_STOCK_PRICES_TOPIC", "stock.prices")
MARKET_TICKS_TOPIC = os.getenv("KAFKA_MARKET_TICKS_TOPIC", "market.ticks")

consumer = KafkaConsumer(
    STOCK_PRICES_TOPIC,
    MARKET_TICKS_TOPIC,
    bootstrap_servers=os.getenv("KAFKA_BROKERS", "localhost:9092"),
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="order-book-engine",
)

execution_service = ExecutionService()

price_cache: dict[str, float] = {}


def start_consumer():

    for message in consumer:

        try:
            data = message.value

            if message.topic == STOCK_PRICES_TOPIC:
                price_cache[data["ticker"]] = data["price"]

            elif message.topic == MARKET_TICKS_TOPIC:
                payload = data.get("payload", {})
                if not payload.get("is_open", False):
                    continue

                for instrument_id, current_price in list(price_cache.items()):
                    trades = execution_service.execute_tick(
                        instrument_id=instrument_id,
                        current_price=current_price,
                    )
                    print(f"TRADES [{instrument_id}]:", trades)

        except Exception as e:
            print(f"ERROR processing message (topic={message.topic} partition={message.partition} offset={message.offset}): {e}")


if __name__ == "__main__":
    Database.init_pool()
    start_consumer()
